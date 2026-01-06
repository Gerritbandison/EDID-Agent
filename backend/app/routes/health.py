"""
Health Check Routes - Agent health check and system status
"""
from datetime import datetime, timezone
from flask import Blueprint, jsonify

from app import db
from app.models import Device, Monitor, AgentStatus

bp = Blueprint('health', __name__, url_prefix='/api')


@bp.route('/health', methods=['GET'])
def health_check():
    """Agent health check endpoint."""
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'

    return jsonify({
        'status': 'ok' if db_status == 'healthy' else 'degraded',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'database': db_status,
        'version': '1.0.0'
    })


@bp.route('/health/detailed', methods=['GET'])
def detailed_health():
    """Detailed system health check."""
    try:
        # Database check
        db.session.execute(db.text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'

    # Get counts
    try:
        device_count = Device.query.count()
        monitor_count = Monitor.query.count()
        agent_count = AgentStatus.query.count()
    except Exception:
        device_count = monitor_count = agent_count = -1

    return jsonify({
        'status': 'ok' if db_status == 'healthy' else 'degraded',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'components': {
            'database': db_status
        },
        'metrics': {
            'total_devices': device_count,
            'total_monitors': monitor_count,
            'total_agents': agent_count
        },
        'version': '1.0.0'
    })


@bp.route('/agent/version', methods=['GET'])
def get_agent_version():
    """Get latest agent version info for auto-update."""
    return jsonify({
        'version': '1.0.0',
        'min_version': '1.0.0',
        'download_urls': {
            'windows': '/downloads/agent-windows-1.0.0.msi',
            'macos': '/downloads/agent-macos-1.0.0.pkg',
            'linux_deb': '/downloads/agent-linux-1.0.0.deb',
            'linux_rpm': '/downloads/agent-linux-1.0.0.rpm'
        },
        'changelog': 'Initial release',
        'release_date': '2024-01-01'
    })


@bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint."""
    return jsonify({
        'pong': True,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })
