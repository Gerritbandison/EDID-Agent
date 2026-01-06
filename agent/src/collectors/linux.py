"""
Linux system information collector
Uses /sys, /proc, lshw, and dmidecode for data collection
"""
import os
import subprocess
import logging
import glob
import re
from typing import Dict, List, Any

from agent.src.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class LinuxCollector(BaseCollector):
    """Collector for Linux systems."""

    def get_platform_name(self) -> str:
        return 'linux'

    def _run_command(self, cmd: List[str], timeout: int = 30, as_root: bool = False) -> str:
        """Run a command and return output."""
        try:
            if as_root and os.geteuid() != 0:
                # Try sudo if not root
                cmd = ['sudo', '-n'] + cmd

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            return ''
        except Exception as e:
            logger.debug(f"Command failed: {' '.join(cmd)}: {e}")
            return ''

    def _read_file(self, path: str) -> str:
        """Read a file and return contents."""
        try:
            with open(path, 'r') as f:
                return f.read().strip()
        except Exception:
            return ''

    def get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware info via DMI/sysfs."""
        info = {}

        # Try reading from sysfs (DMI)
        dmi_paths = {
            'manufacturer': '/sys/class/dmi/id/sys_vendor',
            'model': '/sys/class/dmi/id/product_name',
            'serial_number': '/sys/class/dmi/id/product_serial'
        }

        for key, path in dmi_paths.items():
            value = self._read_file(path)
            if value:
                info[key] = value

        # Fallback to dmidecode
        if not info.get('model'):
            output = self._run_command(['dmidecode', '-s', 'system-product-name'], as_root=True)
            if output:
                info['model'] = output.strip()

        if not info.get('manufacturer'):
            output = self._run_command(['dmidecode', '-s', 'system-manufacturer'], as_root=True)
            if output:
                info['manufacturer'] = output.strip()

        if not info.get('serial_number'):
            output = self._run_command(['dmidecode', '-s', 'system-serial-number'], as_root=True)
            if output:
                info['serial_number'] = output.strip()

        return info

    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU info from /proc/cpuinfo."""
        info = {}

        try:
            cpuinfo = self._read_file('/proc/cpuinfo')

            # Get model name
            for line in cpuinfo.split('\n'):
                if line.startswith('model name'):
                    info['cpu_model'] = line.split(':')[1].strip()
                    break

            # Count physical cores
            physical_ids = set()
            core_ids = set()
            logical_count = 0

            for line in cpuinfo.split('\n'):
                if line.startswith('physical id'):
                    physical_ids.add(line.split(':')[1].strip())
                if line.startswith('core id'):
                    core_ids.add(line.split(':')[1].strip())
                if line.startswith('processor'):
                    logical_count += 1

            # Calculate cores
            if physical_ids and core_ids:
                info['cpu_cores'] = len(physical_ids) * len(core_ids)
            else:
                # Fallback: use nproc or sysfs
                cores = self._read_file('/sys/devices/system/cpu/cpu0/topology/core_cpus_list')
                if cores:
                    # Parse CPU list format (e.g., "0-3" or "0,2,4,6")
                    info['cpu_cores'] = logical_count // 2 or logical_count
                else:
                    info['cpu_cores'] = logical_count

            info['cpu_threads'] = logical_count

        except Exception as e:
            logger.error(f"Error getting CPU info: {e}")
            info['cpu_cores'] = os.cpu_count()

        return info

    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory info from /proc/meminfo."""
        info = {}

        try:
            meminfo = self._read_file('/proc/meminfo')

            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    # Value is in kB
                    kb = int(line.split()[1])
                    info['ram_total_gb'] = round(kb / (1024 * 1024), 2)
                    break

        except Exception as e:
            logger.error(f"Error getting memory info: {e}")

        return info

    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage info from /sys/block."""
        info = {}

        try:
            total_size = 0
            storage_type = 'Unknown'

            # List block devices
            block_devices = glob.glob('/sys/block/[sv]d*') + glob.glob('/sys/block/nvme*')

            for device in block_devices:
                device_name = os.path.basename(device)

                # Get size in 512-byte sectors
                size_path = f'{device}/size'
                size_str = self._read_file(size_path)
                if size_str:
                    sectors = int(size_str)
                    size_bytes = sectors * 512
                    total_size += size_bytes

                # Check if SSD
                rotational_path = f'{device}/queue/rotational'
                rotational = self._read_file(rotational_path)
                if rotational == '0':
                    storage_type = 'SSD'
                elif rotational == '1':
                    if storage_type != 'SSD':
                        storage_type = 'HDD'

                # NVMe is always SSD
                if device_name.startswith('nvme'):
                    storage_type = 'NVMe'

            if total_size > 0:
                info['storage_total_gb'] = round(total_size / (1024 ** 3), 2)
            info['storage_type'] = storage_type

        except Exception as e:
            logger.error(f"Error getting storage info: {e}")

        return info

    def get_network_info(self) -> Dict[str, Any]:
        """Get network info."""
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

        # Get MAC address from primary interface
        try:
            # Find default route interface
            route_output = self._run_command(['ip', 'route', 'get', '8.8.8.8'])
            interface = None

            for part in route_output.split():
                if part.startswith('dev'):
                    continue
                if re.match(r'^[a-z]', part) and part != 'via':
                    interface = part
                    break

            if interface:
                mac_path = f'/sys/class/net/{interface}/address'
                mac = self._read_file(mac_path)
                if mac:
                    info['mac_address'] = mac.upper().replace(':', '-')

        except Exception as e:
            logger.error(f"Error getting MAC address: {e}")

        return info

    def get_user_info(self) -> Dict[str, Any]:
        """Get current user info."""
        info = {}

        try:
            info['assigned_user'] = os.environ.get('USER', os.getlogin())

            # Check for domain join
            # SSSD
            sssd_conf = '/etc/sssd/sssd.conf'
            if os.path.exists(sssd_conf):
                content = self._read_file(sssd_conf)
                for line in content.split('\n'):
                    if 'ad_domain' in line.lower():
                        info['domain'] = line.split('=')[-1].strip()
                        break

            # Realm
            realm_output = self._run_command(['realm', 'list'])
            if realm_output:
                for line in realm_output.split('\n'):
                    if 'realm-name:' in line.lower():
                        info['domain'] = line.split(':')[-1].strip()
                        break

            # Try to get email from LDAP/AD if joined
            if info.get('domain'):
                ldap_output = self._run_command([
                    'ldapsearch', '-Q', '-LLL',
                    f'(sAMAccountName={info["assigned_user"]})',
                    'mail'
                ])
                for line in ldap_output.split('\n'):
                    if line.startswith('mail:'):
                        info['assigned_user_email'] = line.split(':')[-1].strip()
                        break

        except Exception as e:
            logger.error(f"Error getting user info: {e}")

        return info

    def get_edid_data(self) -> List[Dict[str, Any]]:
        """Get EDID data from /sys/class/drm/*/edid."""
        edid_list = []

        try:
            # Find all EDID files
            edid_paths = glob.glob('/sys/class/drm/card*-*/edid')

            for edid_path in edid_paths:
                try:
                    with open(edid_path, 'rb') as f:
                        edid_data = f.read()

                    if len(edid_data) >= 128:
                        # Determine connection type from path
                        connector = os.path.basename(os.path.dirname(edid_path))
                        connection_type = 'Unknown'

                        if 'HDMI' in connector:
                            connection_type = 'HDMI'
                        elif 'DP' in connector:
                            connection_type = 'DisplayPort'
                        elif 'DVI' in connector:
                            connection_type = 'DVI'
                        elif 'VGA' in connector:
                            connection_type = 'VGA'
                        elif 'eDP' in connector:
                            connection_type = 'eDP (Internal)'

                        edid_list.append({
                            'edid_data': edid_data,
                            'port': connector,
                            'connection_type': connection_type
                        })

                except Exception as e:
                    logger.debug(f"Cannot read EDID from {edid_path}: {e}")

            # Alternative: try xrandr if available and no EDID found
            if not edid_list:
                xrandr_output = self._run_command(['xrandr', '--verbose'])
                if xrandr_output:
                    current_output = None
                    edid_hex = []
                    in_edid = False

                    for line in xrandr_output.split('\n'):
                        if ' connected' in line:
                            if current_output and edid_hex:
                                hex_str = ''.join(edid_hex)
                                try:
                                    edid_list.append({
                                        'edid_data': bytes.fromhex(hex_str),
                                        'port': current_output,
                                        'connection_type': self._get_connection_type(current_output)
                                    })
                                except Exception:
                                    pass
                            current_output = line.split()[0]
                            edid_hex = []
                            in_edid = False

                        if 'EDID:' in line:
                            in_edid = True
                            continue

                        if in_edid:
                            stripped = line.strip()
                            if stripped and all(c in '0123456789abcdef' for c in stripped.lower()):
                                edid_hex.append(stripped)
                            else:
                                in_edid = False

                    # Last output
                    if current_output and edid_hex:
                        hex_str = ''.join(edid_hex)
                        try:
                            edid_list.append({
                                'edid_data': bytes.fromhex(hex_str),
                                'port': current_output,
                                'connection_type': self._get_connection_type(current_output)
                            })
                        except Exception:
                            pass

        except Exception as e:
            logger.error(f"Error getting EDID data: {e}")

        # Mark first as primary
        if edid_list:
            edid_list[0]['is_primary'] = True

        return edid_list

    def _get_connection_type(self, output_name: str) -> str:
        """Determine connection type from output name."""
        name_upper = output_name.upper()

        if 'HDMI' in name_upper:
            return 'HDMI'
        elif 'DP' in name_upper or 'DISPLAYPORT' in name_upper:
            return 'DisplayPort'
        elif 'DVI' in name_upper:
            return 'DVI'
        elif 'VGA' in name_upper:
            return 'VGA'
        elif 'EDP' in name_upper:
            return 'eDP (Internal)'
        elif 'LVDS' in name_upper:
            return 'LVDS (Internal)'

        return 'Unknown'
