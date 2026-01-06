"""
Agent helper utilities
"""
import uuid
import hashlib
import platform
import socket


def generate_device_id(hostname: str, serial_number: str = None, mac_address: str = None) -> str:
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


def generate_monitor_id(manufacturer_id: str, serial_number: str, product_code: str = None) -> str:
    """Generate a unique monitor ID based on EDID identifiers."""
    components = [manufacturer_id or 'UNK', serial_number or 'UNKNOWN']

    if product_code:
        components.append(str(product_code))

    combined = '|'.join(components)
    hash_bytes = hashlib.sha256(combined.encode()).digest()

    return str(uuid.UUID(bytes=hash_bytes[:16]))


def get_platform() -> str:
    """Get the current platform identifier."""
    system = platform.system().lower()
    if system == 'darwin':
        return 'macos'
    return system


def get_hostname() -> str:
    """Get the system hostname."""
    return socket.gethostname()


def format_bytes(bytes_value: int, decimal_places: int = 2) -> str:
    """Format bytes into human-readable format."""
    if bytes_value is None:
        return None

    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.{decimal_places}f} {unit}"
        bytes_value /= 1024.0

    return f"{bytes_value:.{decimal_places}f} EB"


def bytes_to_gb(bytes_value: int) -> float:
    """Convert bytes to gigabytes."""
    if bytes_value is None:
        return None
    return round(bytes_value / (1024 ** 3), 2)
