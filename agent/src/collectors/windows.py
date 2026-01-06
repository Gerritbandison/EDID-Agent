"""
Windows system information collector
Uses WMI and Windows Registry for data collection
"""
import os
import logging
import ctypes
from typing import Dict, List, Any

from agent.src.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class WindowsCollector(BaseCollector):
    """Collector for Windows systems."""

    def __init__(self):
        super().__init__()
        self._wmi = None

    @property
    def wmi(self):
        """Lazy-load WMI connection."""
        if self._wmi is None:
            try:
                import wmi
                self._wmi = wmi.WMI()
            except ImportError:
                logger.warning("WMI module not available, using fallback methods")
                self._wmi = False
        return self._wmi

    def get_platform_name(self) -> str:
        return 'windows'

    def get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware info via WMI."""
        info = {}

        if self.wmi:
            try:
                for system in self.wmi.Win32_ComputerSystem():
                    info['manufacturer'] = system.Manufacturer
                    info['model'] = system.Model

                for bios in self.wmi.Win32_BIOS():
                    info['serial_number'] = bios.SerialNumber
            except Exception as e:
                logger.error(f"WMI hardware query failed: {e}")

        return info

    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU info via WMI."""
        info = {}

        if self.wmi:
            try:
                for cpu in self.wmi.Win32_Processor():
                    info['cpu_model'] = cpu.Name
                    info['cpu_cores'] = cpu.NumberOfCores
                    info['cpu_threads'] = cpu.NumberOfLogicalProcessors
                    break
            except Exception as e:
                logger.error(f"WMI CPU query failed: {e}")
        else:
            # Fallback
            info['cpu_cores'] = os.cpu_count()

        return info

    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory info via WMI."""
        info = {}

        if self.wmi:
            try:
                for os_info in self.wmi.Win32_OperatingSystem():
                    total_memory_kb = int(os_info.TotalVisibleMemorySize)
                    info['ram_total_gb'] = round(total_memory_kb / (1024 * 1024), 2)
                    break
            except Exception as e:
                logger.error(f"WMI memory query failed: {e}")
        else:
            try:
                kernel32 = ctypes.windll.kernel32
                c_ulonglong = ctypes.c_ulonglong

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', c_ulonglong),
                        ('ullAvailPhys', c_ulonglong),
                        ('ullTotalPageFile', c_ulonglong),
                        ('ullAvailPageFile', c_ulonglong),
                        ('ullTotalVirtual', c_ulonglong),
                        ('ullAvailVirtual', c_ulonglong),
                        ('ullAvailExtendedVirtual', c_ulonglong),
                    ]

                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(stat)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                info['ram_total_gb'] = round(stat.ullTotalPhys / (1024 ** 3), 2)
            except Exception as e:
                logger.error(f"Memory info fallback failed: {e}")

        return info

    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage info via WMI."""
        info = {}

        if self.wmi:
            try:
                total_size = 0
                storage_type = 'Unknown'

                for disk in self.wmi.Win32_DiskDrive():
                    if disk.Size:
                        total_size += int(disk.Size)
                    if disk.MediaType:
                        if 'SSD' in str(disk.MediaType).upper():
                            storage_type = 'SSD'
                        elif 'HDD' in str(disk.MediaType).upper():
                            storage_type = 'HDD'

                info['storage_total_gb'] = round(total_size / (1024 ** 3), 2)
                info['storage_type'] = storage_type
            except Exception as e:
                logger.error(f"WMI storage query failed: {e}")

        return info

    def get_network_info(self) -> Dict[str, Any]:
        """Get network info via WMI."""
        import socket
        info = {}

        # Get IP address
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            info['ip_address'] = s.getsockname()[0]
            s.close()
        except Exception:
            info['ip_address'] = '127.0.0.1'

        # Get MAC address
        if self.wmi:
            try:
                for adapter in self.wmi.Win32_NetworkAdapterConfiguration(IPEnabled=True):
                    if adapter.MACAddress:
                        info['mac_address'] = adapter.MACAddress
                        break
            except Exception as e:
                logger.error(f"WMI network query failed: {e}")

        return info

    def get_user_info(self) -> Dict[str, Any]:
        """Get current user and domain info."""
        info = {}

        try:
            info['assigned_user'] = os.environ.get('USERNAME', os.getlogin())
            info['domain'] = os.environ.get('USERDOMAIN')

            # Try to get user's email from AD
            if self.wmi:
                try:
                    import subprocess
                    result = subprocess.run(
                        ['whoami', '/upn'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        info['assigned_user_email'] = result.stdout.strip()
                except Exception:
                    pass

            # Try to get AD/Entra info
            try:
                import subprocess
                result = subprocess.run(
                    ['dsregcmd', '/status'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    output = result.stdout
                    for line in output.split('\n'):
                        if 'TenantId' in line:
                            info['entra_tenant_id'] = line.split(':')[-1].strip()
                        if 'DeviceId' in line:
                            info['entra_device_id'] = line.split(':')[-1].strip()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error getting user info: {e}")

        return info

    def get_edid_data(self) -> List[Dict[str, Any]]:
        """Get EDID data from Windows registry."""
        edid_list = []

        try:
            import winreg

            # EDID data is stored in the registry under display keys
            display_key_path = r'SYSTEM\CurrentControlSet\Enum\DISPLAY'

            try:
                display_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, display_key_path)
            except WindowsError:
                logger.warning("Cannot access display registry key")
                return edid_list

            # Iterate through display devices
            i = 0
            while True:
                try:
                    device_name = winreg.EnumKey(display_key, i)
                    device_path = f'{display_key_path}\\{device_name}'

                    device_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, device_path)

                    # Iterate through device instances
                    j = 0
                    while True:
                        try:
                            instance_name = winreg.EnumKey(device_key, j)
                            instance_path = f'{device_path}\\{instance_name}'

                            # Check for Device Parameters\EDID
                            try:
                                edid_path = f'{instance_path}\\Device Parameters'
                                edid_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, edid_path)

                                try:
                                    edid_data, _ = winreg.QueryValueEx(edid_key, 'EDID')
                                    if edid_data:
                                        edid_list.append({
                                            'edid_data': bytes(edid_data),
                                            'port': f'{device_name}_{instance_name}',
                                            'connection_type': self._determine_connection_type(device_name)
                                        })
                                except WindowsError:
                                    pass

                                winreg.CloseKey(edid_key)
                            except WindowsError:
                                pass

                            j += 1
                        except WindowsError:
                            break

                    winreg.CloseKey(device_key)
                    i += 1
                except WindowsError:
                    break

            winreg.CloseKey(display_key)

        except ImportError:
            logger.error("winreg module not available")
        except Exception as e:
            logger.error(f"Error reading EDID from registry: {e}")

        # Mark first as primary
        if edid_list:
            edid_list[0]['is_primary'] = True

        return edid_list

    def _determine_connection_type(self, device_name: str) -> str:
        """Determine connection type from device name."""
        name_upper = device_name.upper()

        if 'HDMI' in name_upper:
            return 'HDMI'
        elif 'DP' in name_upper or 'DISPLAYPORT' in name_upper:
            return 'DisplayPort'
        elif 'DVI' in name_upper:
            return 'DVI'
        elif 'VGA' in name_upper or 'ANALOG' in name_upper:
            return 'VGA'
        elif 'USB' in name_upper:
            return 'USB-C'

        return 'Unknown'
