"""
Inventory Routes - Combined views and statistics
"""
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, Response
import csv
import io

from app import db
from app.models import Device, Monitor, AgentStatus

bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')


@bp.route('', methods=['GET'])
def get_inventory():
    """Get full inventory with devices and monitors."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status')
    sort_by = request.args.get('sort_by', 'last_check_in')
    sort_order = request.args.get('sort_order', 'desc')

    query = Device.query

    # Search filter
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Device.hostname.ilike(search_filter),
                Device.serial_number.ilike(search_filter),
                Device.assigned_user.ilike(search_filter),
                Device.model.ilike(search_filter),
                Device.manufacturer.ilike(search_filter)
            )
        )

    # Status filter
    now = datetime.now(timezone.utc)
    if status == 'online':
        query = query.filter(Device.last_check_in >= now - timedelta(hours=1))
    elif status == 'idle':
        query = query.filter(
            Device.last_check_in < now - timedelta(hours=1),
            Device.last_check_in >= now - timedelta(hours=24)
        )
    elif status == 'offline':
        query = query.filter(Device.last_check_in < now - timedelta(hours=24))

    # Sorting
    sort_column = getattr(Device, sort_by, Device.last_check_in)
    if sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    per_page = min(per_page, 100)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Build inventory items
    inventory = []
    for device in pagination.items:
        device_status = Device.get_status(device)
        item = {
            **device.to_dict(include_monitors=True, include_agent_status=True),
            'status': device_status,
            'status_color': get_status_color(device_status)
        }
        inventory.append(item)

    return jsonify({
        'inventory': inventory,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


def get_status_color(status):
    """Get color code for status."""
    colors = {
        'online': 'green',
        'idle': 'yellow',
        'offline': 'red',
        'unknown': 'gray'
    }
    return colors.get(status, 'gray')


@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics."""
    now = datetime.now(timezone.utc)

    # Device counts
    total_devices = Device.query.count()
    online_devices = Device.query.filter(
        Device.last_check_in >= now - timedelta(hours=1)
    ).count()
    idle_devices = Device.query.filter(
        Device.last_check_in < now - timedelta(hours=1),
        Device.last_check_in >= now - timedelta(hours=24)
    ).count()
    offline_devices = Device.query.filter(
        Device.last_check_in < now - timedelta(hours=24)
    ).count()

    # Monitor counts
    total_monitors = Monitor.query.filter(Monitor.is_connected == True).count()

    # Unique users
    unique_users = db.session.query(Device.assigned_user).distinct().filter(
        Device.assigned_user.isnot(None)
    ).count()

    # Recent check-ins (last 24 hours)
    recent_check_ins = Device.query.filter(
        Device.last_check_in >= now - timedelta(hours=24)
    ).count()

    # By manufacturer
    devices_by_manufacturer = db.session.query(
        Device.manufacturer,
        db.func.count(Device.id)
    ).group_by(Device.manufacturer).all()

    # By model
    devices_by_model = db.session.query(
        Device.model,
        Device.manufacturer,
        db.func.count(Device.id)
    ).group_by(Device.model, Device.manufacturer).limit(10).all()

    # By OS
    devices_by_os = db.session.query(
        Device.os_name,
        db.func.count(Device.id)
    ).group_by(Device.os_name).all()

    # Recent devices (last 5 check-ins)
    recent_devices = Device.query.order_by(
        Device.last_check_in.desc()
    ).limit(5).all()

    return jsonify({
        'summary': {
            'total_devices': total_devices,
            'online_devices': online_devices,
            'idle_devices': idle_devices,
            'offline_devices': offline_devices,
            'total_monitors': total_monitors,
            'unique_users': unique_users,
            'recent_check_ins_24h': recent_check_ins
        },
        'by_manufacturer': {m[0] or 'Unknown': m[1] for m in devices_by_manufacturer},
        'by_model': [
            {'model': m[0] or 'Unknown', 'manufacturer': m[1], 'count': m[2]}
            for m in devices_by_model
        ],
        'by_os': {o[0] or 'Unknown': o[1] for o in devices_by_os},
        'recent_devices': [
            {
                'id': d.id,
                'hostname': d.hostname,
                'assigned_user': d.assigned_user,
                'last_check_in': d.last_check_in.isoformat() if d.last_check_in else None,
                'status': Device.get_status(d)
            }
            for d in recent_devices
        ]
    })


@bp.route('/export', methods=['GET'])
def export_inventory():
    """Export inventory to CSV."""
    format_type = request.args.get('format', 'csv')
    include_monitors = request.args.get('include_monitors', 'true').lower() == 'true'

    devices = Device.query.all()

    if format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        headers = [
            'Hostname', 'Serial Number', 'Model', 'Manufacturer',
            'CPU', 'RAM (GB)', 'Storage (GB)', 'OS', 'OS Version',
            'Assigned User', 'Email', 'Domain', 'Department', 'Location',
            'IP Address', 'MAC Address', 'Last Check-in', 'Status'
        ]

        if include_monitors:
            headers.extend(['Monitor Count', 'Monitor Details'])

        writer.writerow(headers)

        # Data rows
        for device in devices:
            status = Device.get_status(device)
            row = [
                device.hostname,
                device.serial_number,
                device.model,
                device.manufacturer,
                device.cpu_model,
                device.ram_total_gb,
                device.storage_total_gb,
                device.os_name,
                device.os_version,
                device.assigned_user,
                device.assigned_user_email,
                device.domain,
                device.department,
                device.location,
                device.ip_address,
                device.mac_address,
                device.last_check_in.isoformat() if device.last_check_in else '',
                status
            ]

            if include_monitors:
                monitors = list(device.monitors.filter(Monitor.is_connected == True))
                row.append(len(monitors))
                monitor_details = '; '.join([
                    f"{m.manufacturer_name} {m.model_name} ({m.native_resolution})"
                    for m in monitors
                ])
                row.append(monitor_details)

            writer.writerow(row)

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=inventory_export.csv'
            }
        )

    return jsonify({'error': 'Unsupported format'}), 400


@bp.route('/export/monitors', methods=['GET'])
def export_monitors():
    """Export monitors to CSV."""
    monitors = Monitor.query.filter(Monitor.is_connected == True).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    headers = [
        'Manufacturer', 'Model', 'Serial Number', 'Resolution',
        'Screen Size (inches)', 'Manufacture Year', 'Age (years)',
        'Connection Type', 'Connected Device', 'Assigned User'
    ]
    writer.writerow(headers)

    # Data rows
    current_year = datetime.now().year
    for monitor in monitors:
        age = current_year - monitor.manufacture_year if monitor.manufacture_year else None
        row = [
            monitor.manufacturer_name,
            monitor.model_name,
            monitor.serial_number,
            monitor.native_resolution,
            monitor.diagonal_inches,
            monitor.manufacture_year,
            age,
            monitor.connection_type,
            monitor.device.hostname if monitor.device else '',
            monitor.device.assigned_user if monitor.device else ''
        ]
        writer.writerow(row)

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=monitors_export.csv'
        }
    )
