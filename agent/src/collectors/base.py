"""
Base collector class with common functionality
"""
import socket
import platform
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from ..utils.helpers import generate_device_id, generate_monitor_id
from ..utils.edid_parser import EDIDParser

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for system information collectors."""

    def __init__(self):
        self.device_id = None
        self.hostname = socket.gethostname()

    def collect_all(self) -> Dict[str, Any]:
        """Collect all system and monitor information."""
        logger.info("Starting system information collection")

        # Collect device info
        device_info = self.collect_device_info()

        # Generate device ID
        self.device_id = generate_device_id(
            hostname=device_info.get('hostname', self.hostname),
            serial_number=device_info.get('serial_number'),
            mac_address=device_info.get('mac_address')
        )
        device_info['id'] = self.device_id

        # Add agent info
        device_info['agent'] = {
            'version': '1.0.0',
            'platform': self.get_platform_name(),
            'check_in_interval': 1800
        }

        # Collect monitor info
        monitors = self.collect_monitor_info()

        logger.info(f"Collected info for device {self.device_id} with {len(monitors)} monitors")

        return {
            'device': device_info,
            'monitors': monitors
        }

    def collect_device_info(self) -> Dict[str, Any]:
        """Collect comprehensive device information."""
        info = {
            'hostname': self.hostname,
            'os_name': platform.system(),
            'os_version': platform.version(),
            'os_build': platform.release(),
            'os_architecture': platform.machine()
        }

        # Get hardware info
        try:
            hardware = self.get_hardware_info()
            info.update(hardware)
        except Exception as e:
            logger.error(f"Error collecting hardware info: {e}")

        # Get CPU info
        try:
            cpu = self.get_cpu_info()
            info.update(cpu)
        except Exception as e:
            logger.error(f"Error collecting CPU info: {e}")

        # Get memory info
        try:
            memory = self.get_memory_info()
            info.update(memory)
        except Exception as e:
            logger.error(f"Error collecting memory info: {e}")

        # Get storage info
        try:
            storage = self.get_storage_info()
            info.update(storage)
        except Exception as e:
            logger.error(f"Error collecting storage info: {e}")

        # Get network info
        try:
            network = self.get_network_info()
            info.update(network)
        except Exception as e:
            logger.error(f"Error collecting network info: {e}")

        # Get user info
        try:
            user = self.get_user_info()
            info.update(user)
        except Exception as e:
            logger.error(f"Error collecting user info: {e}")

        return info

    def collect_monitor_info(self) -> List[Dict[str, Any]]:
        """Collect information about connected monitors."""
        monitors = []

        try:
            edid_data_list = self.get_edid_data()

            for idx, edid_entry in enumerate(edid_data_list):
                try:
                    edid_bytes = edid_entry.get('edid_data')
                    if not edid_bytes:
                        continue

                    # Parse EDID
                    parser = EDIDParser(edid_bytes)
                    parser.parse()
                    monitor_data = parser.to_flat_dict()

                    # Generate monitor ID
                    monitor_id = generate_monitor_id(
                        manufacturer_id=monitor_data.get('manufacturer_id'),
                        serial_number=monitor_data.get('serial_number'),
                        product_code=monitor_data.get('product_code')
                    )

                    monitor_data['id'] = monitor_id
                    monitor_data['device_id'] = self.device_id
                    monitor_data['connection_type'] = edid_entry.get('connection_type', 'Unknown')
                    monitor_data['connection_port'] = edid_entry.get('port', f'Display-{idx}')
                    monitor_data['is_primary'] = edid_entry.get('is_primary', idx == 0)
                    monitor_data['is_connected'] = True

                    monitors.append(monitor_data)

                except Exception as e:
                    logger.error(f"Error parsing EDID data for monitor {idx}: {e}")

        except Exception as e:
            logger.error(f"Error collecting monitor info: {e}")

        return monitors

    @abstractmethod
    def get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information (model, manufacturer, serial number)."""
        pass

    @abstractmethod
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information."""
        pass

    @abstractmethod
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information."""
        pass

    @abstractmethod
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information."""
        pass

    @abstractmethod
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information."""
        pass

    @abstractmethod
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information."""
        pass

    @abstractmethod
    def get_edid_data(self) -> List[Dict[str, Any]]:
        """Get EDID data from connected monitors."""
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Get platform name identifier."""
        pass
