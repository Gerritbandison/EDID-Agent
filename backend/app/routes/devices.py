"""
Device Routes - API endpoints for device management
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

from app import db
from app.models import Device, AgentStatus
from app.routes.auth import require_api_key

bp = Blueprint('devices', __name__, url_prefix='/api/devices')


@bp.route('', methods=['POST'])
@require_api_key
def receive_device_data():
    """Receive device data from agent."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if not data.get('id'):
        return jsonify({'error': 'Device ID is required'}), 400

    # Check if device exists
    device = Device.query.get(data['id'])

    if device:
        # Update existing device
        device = update_device(device, data)
    else:
        # Create new device
        device = create_device(data)
        db.session.add(device)

    # Update or create agent status
    update_agent_status(device, data.get('agent', {}))

    db.session.commit()

    return jsonify({
        'message': 'Device data received',
        'device_id': device.id,
        'status': 'updated' if device.created_at != device.updated_at else 'created'
    }), 200


def create_device(data):
    """Create a new device from data."""
    device = Device(
        id=data['id'],
        hostname=data.get('hostname', 'Unknown'),
        serial_number=data.get('serial_number'),
        model=data.get('model'),
        manufacturer=data.get('manufacturer'),
        cpu_model=data.get('cpu_model'),
        cpu_cores=data.get('cpu_cores'),
        cpu_threads=data.get('cpu_threads'),
        ram_total_gb=data.get('ram_total_gb'),
        storage_total_gb=data.get('storage_total_gb'),
        storage_type=data.get('storage_type'),
        os_name=data.get('os_name'),
        os_version=data.get('os_version'),
        os_build=data.get('os_build'),
        os_architecture=data.get('os_architecture'),
        ip_address=data.get('ip_address'),
        mac_address=data.get('mac_address'),
        assigned_user=data.get('assigned_user'),
        assigned_user_email=data.get('assigned_user_email'),
        domain=data.get('domain'),
        ad_distinguished_name=data.get('ad_distinguished_name'),
        ad_organizational_unit=data.get('ad_organizational_unit'),
        entra_device_id=data.get('entra_device_id'),
        entra_tenant_id=data.get('entra_tenant_id'),
        location=data.get('location'),
        department=data.get('department'),
        first_seen=datetime.now(timezone.utc),
        last_check_in=datetime.now(timezone.utc)
    )
    return device


def update_device(device, data):
    """Update existing device with new data."""
    update_fields = [
        'hostname', 'serial_number', 'model', 'manufacturer',
        'cpu_model', 'cpu_cores', 'cpu_threads', 'ram_total_gb',
        'storage_total_gb', 'storage_type', 'os_name', 'os_version',
        'os_build', 'os_architecture', 'ip_address', 'mac_address',
        'assigned_user', 'assigned_user_email', 'domain',
        'ad_distinguished_name', 'ad_organizational_unit',
        'entra_device_id', 'entra_tenant_id', 'location', 'department'
    ]

    for field in update_fields:
        if field in data and data[field] is not None:
            setattr(device, field, data[field])

    device.last_check_in = datetime.now(timezone.utc)
    return device


def update_agent_status(device, agent_data):
    """Update or create agent status."""
    agent_status = AgentStatus.query.filter_by(device_id=device.id).first()

    if not agent_status:
        agent_status = AgentStatus(device_id=device.id)
        db.session.add(agent_status)

    agent_status.agent_version = agent_data.get('version')
    agent_status.agent_platform = agent_data.get('platform')
    agent_status.check_in_interval_seconds = agent_data.get('check_in_interval', 1800)
    agent_status.update_heartbeat()
    agent_status.record_check_in(success=True)


@bp.route('/<device_id>', methods=['GET'])
def get_device(device_id):
    """Get specific device details."""
    device = Device.query.get(device_id)

    if not device:
        return jsonify({'error': 'Device not found'}), 404

    return jsonify(device.to_dict(include_monitors=True, include_agent_status=True))


@bp.route('/<device_id>', methods=['DELETE'])
@require_api_key
def delete_device(device_id):
    """Delete a device."""
    device = Device.query.get(device_id)

    if not device:
        return jsonify({'error': 'Device not found'}), 404

    db.session.delete(device)
    db.session.commit()

    return jsonify({'message': 'Device deleted'})


@bp.route('', methods=['GET'])
def list_devices():
    """List all devices with optional filtering."""
    # Query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    manufacturer = request.args.get('manufacturer')
    status = request.args.get('status')
    sort_by = request.args.get('sort_by', 'last_check_in')
    sort_order = request.args.get('sort_order', 'desc')

    # Build query
    query = Device.query

    # Search filter
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Device.hostname.ilike(search_filter),
                Device.serial_number.ilike(search_filter),
                Device.assigned_user.ilike(search_filter),
                Device.model.ilike(search_filter)
            )
        )

    # Manufacturer filter
    if manufacturer:
        query = query.filter(Device.manufacturer == manufacturer)

    # Status filter (requires subquery for agent status)
    if status:
        now = datetime.now(timezone.utc)
        if status == 'online':
            # Checked in within last hour
            from datetime import timedelta
            query = query.filter(Device.last_check_in >= now - timedelta(hours=1))
        elif status == 'idle':
            from datetime import timedelta
            query = query.filter(
                Device.last_check_in < now - timedelta(hours=1),
                Device.last_check_in >= now - timedelta(hours=24)
            )
        elif status == 'offline':
            from datetime import timedelta
            query = query.filter(Device.last_check_in < now - timedelta(hours=24))

    # Sorting
    sort_column = getattr(Device, sort_by, Device.last_check_in)
    if sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    per_page = min(per_page, 100)  # Max 100 per page
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'devices': [d.to_dict(include_monitors=True) for d in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@bp.route('/manufacturers', methods=['GET'])
def get_manufacturers():
    """Get list of unique manufacturers."""
    manufacturers = db.session.query(Device.manufacturer).distinct().all()
    return jsonify([m[0] for m in manufacturers if m[0]])


@bp.route('/models', methods=['GET'])
def get_models():
    """Get list of unique models, optionally filtered by manufacturer."""
    manufacturer = request.args.get('manufacturer')

    query = db.session.query(Device.model, Device.manufacturer)

    if manufacturer:
        query = query.filter(Device.manufacturer == manufacturer)

    models = query.distinct().all()

    return jsonify([{'model': m[0], 'manufacturer': m[1]} for m in models if m[0]])
