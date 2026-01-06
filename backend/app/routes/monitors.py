"""
Monitor Routes - API endpoints for monitor/display management
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
import json

from app import db
from app.models import Monitor, Device
from app.routes.auth import require_api_key

bp = Blueprint('monitors', __name__, url_prefix='/api/monitors')


@bp.route('', methods=['POST'])
@require_api_key
def receive_monitor_data():
    """Receive monitor EDID data from agent."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if not data.get('device_id'):
        return jsonify({'error': 'Device ID is required'}), 400

    # Verify device exists
    device = Device.query.get(data['device_id'])
    if not device:
        return jsonify({'error': 'Device not found'}), 404

    # Process monitors array
    monitors_data = data.get('monitors', [])
    if isinstance(data.get('monitor'), dict):
        # Single monitor submission
        monitors_data = [data['monitor']]

    processed = []
    for monitor_data in monitors_data:
        monitor_id = monitor_data.get('id')
        if not monitor_id:
            continue

        # Check if monitor exists
        monitor = Monitor.query.get(monitor_id)

        if monitor:
            monitor = update_monitor(monitor, monitor_data, data['device_id'])
        else:
            monitor = create_monitor(monitor_data, data['device_id'])
            db.session.add(monitor)

        processed.append(monitor_id)

    # Mark disconnected monitors
    Monitor.query.filter(
        Monitor.device_id == data['device_id'],
        ~Monitor.id.in_(processed)
    ).update({'is_connected': False})

    db.session.commit()

    return jsonify({
        'message': 'Monitor data received',
        'monitors_processed': len(processed)
    }), 200


def create_monitor(data, device_id):
    """Create a new monitor from EDID data."""
    supported_resolutions = data.get('supported_resolutions', [])
    if isinstance(supported_resolutions, list):
        supported_resolutions = json.dumps(supported_resolutions)

    monitor = Monitor(
        id=data['id'],
        device_id=device_id,
        manufacturer_id=data.get('manufacturer_id'),
        manufacturer_name=data.get('manufacturer_name'),
        product_code=data.get('product_code'),
        serial_number=data.get('serial_number'),
        model_name=data.get('model_name'),
        manufacture_week=data.get('manufacture_week'),
        manufacture_year=data.get('manufacture_year'),
        manufacture_date_formatted=data.get('manufacture_date_formatted'),
        native_resolution_width=data.get('native_resolution_width'),
        native_resolution_height=data.get('native_resolution_height'),
        native_resolution=data.get('native_resolution'),
        screen_width_cm=data.get('screen_width_cm'),
        screen_height_cm=data.get('screen_height_cm'),
        diagonal_inches=data.get('diagonal_inches'),
        aspect_ratio=data.get('aspect_ratio'),
        max_horizontal_freq_khz=data.get('max_horizontal_freq_khz'),
        max_vertical_freq_hz=data.get('max_vertical_freq_hz'),
        max_pixel_clock_mhz=data.get('max_pixel_clock_mhz'),
        color_bit_depth=data.get('color_bit_depth'),
        hdr_supported=data.get('hdr_supported', False),
        connection_type=data.get('connection_type'),
        connection_port=data.get('connection_port'),
        edid_raw=data.get('edid_raw'),
        edid_version=data.get('edid_version'),
        supported_resolutions=supported_resolutions,
        is_primary=data.get('is_primary', False),
        is_connected=True,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    return monitor


def update_monitor(monitor, data, device_id):
    """Update existing monitor with new data."""
    update_fields = [
        'manufacturer_id', 'manufacturer_name', 'product_code',
        'serial_number', 'model_name', 'manufacture_week', 'manufacture_year',
        'manufacture_date_formatted', 'native_resolution_width',
        'native_resolution_height', 'native_resolution', 'screen_width_cm',
        'screen_height_cm', 'diagonal_inches', 'aspect_ratio',
        'max_horizontal_freq_khz', 'max_vertical_freq_hz', 'max_pixel_clock_mhz',
        'color_bit_depth', 'hdr_supported', 'connection_type', 'connection_port',
        'edid_raw', 'edid_version', 'is_primary'
    ]

    for field in update_fields:
        if field in data and data[field] is not None:
            setattr(monitor, field, data[field])

    if 'supported_resolutions' in data:
        resolutions = data['supported_resolutions']
        if isinstance(resolutions, list):
            monitor.supported_resolutions = json.dumps(resolutions)
        else:
            monitor.supported_resolutions = resolutions

    monitor.device_id = device_id
    monitor.is_connected = True
    monitor.last_seen = datetime.now(timezone.utc)
    return monitor


@bp.route('/<monitor_id>', methods=['GET'])
def get_monitor(monitor_id):
    """Get specific monitor details."""
    monitor = Monitor.query.get(monitor_id)

    if not monitor:
        return jsonify({'error': 'Monitor not found'}), 404

    result = monitor.to_dict()
    # Include device info
    if monitor.device:
        result['device'] = {
            'id': monitor.device.id,
            'hostname': monitor.device.hostname,
            'assigned_user': monitor.device.assigned_user
        }

    return jsonify(result)


@bp.route('', methods=['GET'])
def list_monitors():
    """List all monitors with optional filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    manufacturer = request.args.get('manufacturer')
    min_age_years = request.args.get('min_age_years', type=int)
    max_age_years = request.args.get('max_age_years', type=int)
    connected_only = request.args.get('connected_only', 'true').lower() == 'true'

    query = Monitor.query

    # Search filter
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Monitor.model_name.ilike(search_filter),
                Monitor.serial_number.ilike(search_filter),
                Monitor.manufacturer_name.ilike(search_filter)
            )
        )

    # Manufacturer filter
    if manufacturer:
        query = query.filter(Monitor.manufacturer_name == manufacturer)

    # Age filter
    current_year = datetime.now().year
    if min_age_years is not None:
        query = query.filter(Monitor.manufacture_year <= current_year - min_age_years)
    if max_age_years is not None:
        query = query.filter(Monitor.manufacture_year >= current_year - max_age_years)

    # Connected filter
    if connected_only:
        query = query.filter(Monitor.is_connected == True)

    # Order by last seen
    query = query.order_by(Monitor.last_seen.desc())

    # Pagination
    per_page = min(per_page, 100)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'monitors': [m.to_dict() for m in pagination.items],
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
    """Get list of unique monitor manufacturers."""
    manufacturers = db.session.query(Monitor.manufacturer_name).distinct().all()
    return jsonify([m[0] for m in manufacturers if m[0]])


@bp.route('/stats', methods=['GET'])
def get_monitor_stats():
    """Get monitor statistics."""
    current_year = datetime.now().year

    # Total monitors
    total = Monitor.query.filter(Monitor.is_connected == True).count()

    # By manufacturer
    by_manufacturer = db.session.query(
        Monitor.manufacturer_name,
        db.func.count(Monitor.id)
    ).filter(
        Monitor.is_connected == True
    ).group_by(Monitor.manufacturer_name).all()

    # By age range
    age_ranges = {
        '0-2 years': Monitor.query.filter(
            Monitor.manufacture_year >= current_year - 2,
            Monitor.is_connected == True
        ).count(),
        '3-5 years': Monitor.query.filter(
            Monitor.manufacture_year >= current_year - 5,
            Monitor.manufacture_year < current_year - 2,
            Monitor.is_connected == True
        ).count(),
        '6+ years': Monitor.query.filter(
            Monitor.manufacture_year < current_year - 5,
            Monitor.is_connected == True
        ).count()
    }

    # By resolution
    by_resolution = db.session.query(
        Monitor.native_resolution,
        db.func.count(Monitor.id)
    ).filter(
        Monitor.is_connected == True
    ).group_by(Monitor.native_resolution).all()

    return jsonify({
        'total': total,
        'by_manufacturer': {m[0]: m[1] for m in by_manufacturer if m[0]},
        'by_age': age_ranges,
        'by_resolution': {r[0]: r[1] for r in by_resolution if r[0]}
    })
