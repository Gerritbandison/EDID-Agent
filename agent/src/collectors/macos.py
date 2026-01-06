"""
macOS system information collector
Uses system_profiler and ioreg for data collection
"""
import os
import subprocess
import plistlib
import logging
import re
from typing import Dict, List, Any

from agent.src.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class MacOSCollector(BaseCollector):
    """Collector for macOS systems."""

    def get_platform_name(self) -> str:
        return 'macos'

    def _run_command(self, cmd: List[str], timeout: int = 30) -> str:
        """Run a command and return output."""
        try:
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
            logger.error(f"Command failed: {' '.join(cmd)}: {e}")
            return ''

    def _run_command_plist(self, cmd: List[str]) -> Dict:
        """Run a command that returns plist XML and parse it."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout:
                return plistlib.loads(result.stdout)
        except Exception as e:
            logger.error(f"Plist command failed: {e}")
        return {}

    def get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware info via system_profiler."""
        info = {}

        try:
            hw_info = self._run_command_plist([
                'system_profiler', 'SPHardwareDataType', '-xml'
            ])

            if hw_info and len(hw_info) > 0:
                items = hw_info[0].get('_items', [])
                if items:
                    hw = items[0]
                    info['model'] = hw.get('machine_model', '')
                    info['manufacturer'] = 'Apple'
                    info['serial_number'] = hw.get('serial_number', '')

                    # Get marketing name
                    model_name = hw.get('machine_name', '')
                    if model_name:
                        info['model'] = model_name

        except Exception as e:
            logger.error(f"Error getting hardware info: {e}")

        return info

    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU info via sysctl and system_profiler."""
        info = {}

        try:
            # Get CPU name
            result = self._run_command(['sysctl', '-n', 'machdep.cpu.brand_string'])
            if result:
                info['cpu_model'] = result.strip()

            # Get core count
            result = self._run_command(['sysctl', '-n', 'hw.physicalcpu'])
            if result:
                info['cpu_cores'] = int(result.strip())

            # Get thread count
            result = self._run_command(['sysctl', '-n', 'hw.logicalcpu'])
            if result:
                info['cpu_threads'] = int(result.strip())

        except Exception as e:
            logger.error(f"Error getting CPU info: {e}")

        return info

    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory info via sysctl."""
        info = {}

        try:
            result = self._run_command(['sysctl', '-n', 'hw.memsize'])
            if result:
                mem_bytes = int(result.strip())
                info['ram_total_gb'] = round(mem_bytes / (1024 ** 3), 2)
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")

        return info

    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage info via diskutil."""
        info = {}

        try:
            # Get disk info
            result = self._run_command(['diskutil', 'info', '-all'])

            total_size = 0
            storage_type = 'Unknown'

            for line in result.split('\n'):
                if 'Disk Size:' in line:
                    match = re.search(r'\((\d+) Bytes\)', line)
                    if match:
                        total_size = max(total_size, int(match.group(1)))

                if 'Solid State:' in line:
                    if 'Yes' in line:
                        storage_type = 'SSD'
                    elif 'No' in line:
                        storage_type = 'HDD'

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
            result = self._run_command(['ifconfig', 'en0'])
            for line in result.split('\n'):
                if 'ether' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        info['mac_address'] = parts[1].upper().replace(':', '-')
                    break
        except Exception as e:
            logger.error(f"Error getting MAC address: {e}")

        return info

    def get_user_info(self) -> Dict[str, Any]:
        """Get current user info."""
        info = {}

        try:
            info['assigned_user'] = os.environ.get('USER', os.getlogin())

            # Try to get directory info
            result = self._run_command(['dscl', '.', '-read', f'/Users/{info["assigned_user"]}'])

            for line in result.split('\n'):
                if 'EMailAddress:' in line:
                    info['assigned_user_email'] = line.split(':')[-1].strip()
                if 'RealName:' in line:
                    pass  # Could capture full name

            # Check domain binding
            result = self._run_command(['dsconfigad', '-show'])
            if result:
                for line in result.split('\n'):
                    if 'Active Directory Domain' in line:
                        info['domain'] = line.split('=')[-1].strip()
                    if 'Computer Account' in line:
                        info['ad_distinguished_name'] = line.split('=')[-1].strip()

        except Exception as e:
            logger.error(f"Error getting user info: {e}")

        return info

    def get_edid_data(self) -> List[Dict[str, Any]]:
        """Get EDID data from ioreg."""
        edid_list = []

        try:
            # Get display info from ioreg
            result = self._run_command(['ioreg', '-lw0', '-r', '-c', 'IODisplayConnect'])

            # Parse ioreg output to find EDID data
            current_display = {}
            in_display = False

            for line in result.split('\n'):
                if 'IODisplayConnect' in line:
                    if current_display.get('edid_data'):
                        edid_list.append(current_display)
                    current_display = {}
                    in_display = True

                if in_display:
                    if 'IODisplayEDID' in line:
                        # Extract hex EDID data
                        match = re.search(r'<([0-9a-fA-F]+)>', line)
                        if match:
                            hex_data = match.group(1)
                            current_display['edid_data'] = bytes.fromhex(hex_data)

                    if 'IODisplayLocation' in line:
                        # Determine connection type
                        if 'HDMI' in line:
                            current_display['connection_type'] = 'HDMI'
                        elif 'DP' in line or 'DisplayPort' in line:
                            current_display['connection_type'] = 'DisplayPort'
                        elif 'Thunderbolt' in line or 'USB' in line:
                            current_display['connection_type'] = 'USB-C/Thunderbolt'
                        else:
                            current_display['connection_type'] = 'Unknown'

            # Don't forget the last display
            if current_display.get('edid_data'):
                edid_list.append(current_display)

            # Alternative method using system_profiler
            if not edid_list:
                displays_info = self._run_command_plist([
                    'system_profiler', 'SPDisplaysDataType', '-xml'
                ])

                if displays_info and len(displays_info) > 0:
                    items = displays_info[0].get('_items', [])
                    for item in items:
                        displays = item.get('spdisplays_ndrvs', [])
                        for idx, display in enumerate(displays):
                            # system_profiler may not have raw EDID
                            # but we can try to extract what's available
                            edid_hex = display.get('_spdisplays_edid')
                            if edid_hex:
                                edid_list.append({
                                    'edid_data': bytes.fromhex(edid_hex),
                                    'connection_type': display.get('spdisplays_connection_type', 'Unknown'),
                                    'port': f'Display-{idx}'
                                })

        except Exception as e:
            logger.error(f"Error getting EDID data: {e}")

        # Mark first as primary
        if edid_list:
            edid_list[0]['is_primary'] = True

        return edid_list
