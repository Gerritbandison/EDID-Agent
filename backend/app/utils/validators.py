"""
Data validation utilities
"""
import re


def validate_device_data(data):
    """Validate device data from agent."""
    errors = []

    if not data.get('id'):
        errors.append('Device ID is required')

    if not data.get('hostname'):
        errors.append('Hostname is required')

    # Validate hostname format
    if data.get('hostname'):
        hostname = data['hostname']
        if len(hostname) > 255:
            errors.append('Hostname too long (max 255 characters)')
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*$', hostname):
            errors.append('Invalid hostname format')

    # Validate serial number
    if data.get('serial_number') and len(data['serial_number']) > 255:
        errors.append('Serial number too long')

    # Validate numeric fields
    numeric_fields = ['cpu_cores', 'cpu_threads', 'ram_total_gb', 'storage_total_gb']
    for field in numeric_fields:
        if field in data and data[field] is not None:
            try:
                value = float(data[field])
                if value < 0:
                    errors.append(f'{field} cannot be negative')
            except (TypeError, ValueError):
                errors.append(f'{field} must be a number')

    # Validate IP address
    if data.get('ip_address'):
        ip = data['ip_address']
        # Simple validation - allow IPv4 and IPv6
        if not re.match(r'^[\d\.]+$', ip) and not re.match(r'^[\da-fA-F:]+$', ip):
            errors.append('Invalid IP address format')

    # Validate MAC address
    if data.get('mac_address'):
        mac = data['mac_address']
        if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac):
            errors.append('Invalid MAC address format')

    return errors


def validate_monitor_data(data):
    """Validate monitor EDID data from agent."""
    errors = []

    if not data.get('id'):
        errors.append('Monitor ID is required')

    if not data.get('device_id'):
        errors.append('Device ID is required')

    # Validate resolution values
    if data.get('native_resolution_width'):
        try:
            width = int(data['native_resolution_width'])
            if width < 0 or width > 16384:
                errors.append('Invalid resolution width')
        except (TypeError, ValueError):
            errors.append('Resolution width must be a number')

    if data.get('native_resolution_height'):
        try:
            height = int(data['native_resolution_height'])
            if height < 0 or height > 16384:
                errors.append('Invalid resolution height')
        except (TypeError, ValueError):
            errors.append('Resolution height must be a number')

    # Validate manufacture year
    if data.get('manufacture_year'):
        try:
            year = int(data['manufacture_year'])
            if year < 1990 or year > 2100:
                errors.append('Invalid manufacture year')
        except (TypeError, ValueError):
            errors.append('Manufacture year must be a number')

    # Validate manufacture week
    if data.get('manufacture_week'):
        try:
            week = int(data['manufacture_week'])
            if week < 1 or week > 53:
                errors.append('Invalid manufacture week (must be 1-53)')
        except (TypeError, ValueError):
            errors.append('Manufacture week must be a number')

    # Validate diagonal size
    if data.get('diagonal_inches'):
        try:
            size = float(data['diagonal_inches'])
            if size < 0 or size > 200:
                errors.append('Invalid diagonal size')
        except (TypeError, ValueError):
            errors.append('Diagonal size must be a number')

    return errors


def sanitize_string(value, max_length=255):
    """Sanitize a string value."""
    if value is None:
        return None

    # Convert to string
    value = str(value).strip()

    # Truncate to max length
    if len(value) > max_length:
        value = value[:max_length]

    # Remove potentially dangerous characters
    value = re.sub(r'[<>]', '', value)

    return value if value else None
