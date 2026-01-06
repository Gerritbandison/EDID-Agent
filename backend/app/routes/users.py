"""
Users Routes - User-centric views for device assignment
"""
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, Response
import csv
import io

from app import db
from app.models import Device, Monitor

bp = Blueprint('users', __name__, url_prefix='/api/users')


@bp.route('', methods=['GET'])
def list_users():
    """Get list of all users with device counts."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')

    # Get unique users with device counts
    query = db.session.query(
        Device.assigned_user,
        Device.assigned_user_email,
        Device.domain,
        Device.department,
        db.func.count(Device.id).label('device_count'),
        db.func.max(Device.last_check_in).label('last_activity')
    ).filter(
        Device.assigned_user.isnot(None)
    ).group_by(
        Device.assigned_user,
        Device.assigned_user_email,
        Device.domain,
        Device.department
    )

    # Search filter
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Device.assigned_user.ilike(search_filter),
                Device.assigned_user_email.ilike(search_filter),
                Device.department.ilike(search_filter)
            )
        )

    # Order by username
    query = query.order_by(Device.assigned_user)

    # Pagination
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    total = query.count()

    users_data = query.offset(offset).limit(per_page).all()

    users = []
    for user in users_data:
        users.append({
            'username': user.assigned_user,
            'email': user.assigned_user_email,
            'domain': user.domain,
            'department': user.department,
            'device_count': user.device_count,
            'last_activity': user.last_activity.isoformat() if user.last_activity else None
        })

    return jsonify({
        'users': users,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'has_next': offset + per_page < total,
            'has_prev': page > 1
        }
    })


@bp.route('/<username>', methods=['GET'])
def get_user_devices(username):
    """Get all devices and monitors for a specific user."""
    devices = Device.query.filter(Device.assigned_user == username).all()

    if not devices:
        return jsonify({'error': 'No devices found for user'}), 404

    # Get user info from first device
    user_info = {
        'username': username,
        'email': devices[0].assigned_user_email,
        'domain': devices[0].domain,
        'department': devices[0].department
    }

    # Build device list with monitors
    device_list = []
    total_monitors = 0

    for device in devices:
        status = Device.get_status(device)
        monitors = list(device.monitors.filter(Monitor.is_connected == True))
        total_monitors += len(monitors)

        device_list.append({
            'id': device.id,
            'hostname': device.hostname,
            'serial_number': device.serial_number,
            'model': device.model,
            'manufacturer': device.manufacturer,
            'os': f"{device.os_name} {device.os_version}",
            'last_check_in': device.last_check_in.isoformat() if device.last_check_in else None,
            'status': status,
            'status_color': get_status_color(status),
            'monitors': [m.to_dict() for m in monitors],
            'monitor_count': len(monitors)
        })

    return jsonify({
        'user': user_info,
        'devices': device_list,
        'summary': {
            'total_devices': len(devices),
            'total_monitors': total_monitors
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


@bp.route('/<username>/export', methods=['GET'])
def export_user_assets(username):
    """Export user's assets to CSV."""
    devices = Device.query.filter(Device.assigned_user == username).all()

    if not devices:
        return jsonify({'error': 'No devices found for user'}), 404

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['Asset Report for: ' + username])
    writer.writerow(['Generated: ' + datetime.now().isoformat()])
    writer.writerow([])

    # Devices section
    writer.writerow(['DEVICES'])
    writer.writerow([
        'Hostname', 'Serial Number', 'Model', 'Manufacturer',
        'CPU', 'RAM (GB)', 'Storage (GB)', 'OS', 'Last Check-in'
    ])

    for device in devices:
        writer.writerow([
            device.hostname,
            device.serial_number,
            device.model,
            device.manufacturer,
            device.cpu_model,
            device.ram_total_gb,
            device.storage_total_gb,
            f"{device.os_name} {device.os_version}",
            device.last_check_in.isoformat() if device.last_check_in else ''
        ])

    writer.writerow([])

    # Monitors section
    writer.writerow(['MONITORS'])
    writer.writerow([
        'Connected To', 'Manufacturer', 'Model', 'Serial Number',
        'Resolution', 'Size (inches)', 'Manufacture Year'
    ])

    for device in devices:
        monitors = device.monitors.filter(Monitor.is_connected == True).all()
        for monitor in monitors:
            writer.writerow([
                device.hostname,
                monitor.manufacturer_name,
                monitor.model_name,
                monitor.serial_number,
                monitor.native_resolution,
                monitor.diagonal_inches,
                monitor.manufacture_year
            ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={username}_assets.csv'
        }
    )


@bp.route('/departments', methods=['GET'])
def get_departments():
    """Get list of departments with device counts."""
    departments = db.session.query(
        Device.department,
        db.func.count(Device.id).label('device_count'),
        db.func.count(db.distinct(Device.assigned_user)).label('user_count')
    ).filter(
        Device.department.isnot(None)
    ).group_by(Device.department).all()

    return jsonify([
        {
            'department': d.department,
            'device_count': d.device_count,
            'user_count': d.user_count
        }
        for d in departments
    ])


@bp.route('/by-department/<department>', methods=['GET'])
def get_users_by_department(department):
    """Get all users in a department."""
    users = db.session.query(
        Device.assigned_user,
        Device.assigned_user_email,
        db.func.count(Device.id).label('device_count')
    ).filter(
        Device.department == department,
        Device.assigned_user.isnot(None)
    ).group_by(
        Device.assigned_user,
        Device.assigned_user_email
    ).all()

    if not users:
        return jsonify({'error': 'No users found in department'}), 404

    return jsonify({
        'department': department,
        'users': [
            {
                'username': u.assigned_user,
                'email': u.assigned_user_email,
                'device_count': u.device_count
            }
            for u in users
        ],
        'total_users': len(users)
    })
