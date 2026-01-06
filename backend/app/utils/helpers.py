"""
Helper utility functions
"""
import uuid
import hashlib


def generate_device_id(hostname, serial_number=None, mac_address=None):
    """Generate a unique device ID based on system identifiers."""
    components = [hostname]

    if serial_number:
        components.append(serial_number)
    if mac_address:
        components.append(mac_address)

    # Create a hash of the components
    combined = '|'.join(filter(None, components))
    hash_bytes = hashlib.sha256(combined.encode()).digest()

    # Convert to UUID format
    return str(uuid.UUID(bytes=hash_bytes[:16]))


def generate_monitor_id(manufacturer_id, serial_number, product_code=None):
    """Generate a unique monitor ID based on EDID identifiers."""
    components = [manufacturer_id or 'UNK', serial_number or 'UNKNOWN']

    if product_code:
        components.append(str(product_code))

    combined = '|'.join(components)
    hash_bytes = hashlib.sha256(combined.encode()).digest()

    return str(uuid.UUID(bytes=hash_bytes[:16]))


def format_bytes(bytes_value, decimal_places=2):
    """Format bytes into human-readable format."""
    if bytes_value is None:
        return None

    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.{decimal_places}f} {unit}"
        bytes_value /= 1024.0

    return f"{bytes_value:.{decimal_places}f} EB"


def format_uptime(seconds):
    """Format uptime in seconds to human-readable format."""
    if seconds is None:
        return None

    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")

    return ' '.join(parts) if parts else '< 1m'


def calculate_aspect_ratio(width, height):
    """Calculate aspect ratio from resolution."""
    if not width or not height:
        return None

    from math import gcd
    divisor = gcd(width, height)
    ratio_w = width // divisor
    ratio_h = height // divisor

    # Common aspect ratios
    common_ratios = {
        (16, 9): '16:9',
        (16, 10): '16:10',
        (4, 3): '4:3',
        (21, 9): '21:9',
        (32, 9): '32:9',
        (5, 4): '5:4',
        (3, 2): '3:2'
    }

    return common_ratios.get((ratio_w, ratio_h), f'{ratio_w}:{ratio_h}')


def calculate_diagonal_inches(width_cm, height_cm):
    """Calculate diagonal size in inches from dimensions in cm."""
    if not width_cm or not height_cm:
        return None

    import math
    diagonal_cm = math.sqrt(width_cm ** 2 + height_cm ** 2)
    return round(diagonal_cm / 2.54, 1)
