"""
EDID (Extended Display Identification Data) Parser

Parses binary EDID data from monitors into structured information.
Supports EDID versions 1.3 and 1.4.
"""
import struct
import base64
import math
from typing import Dict, List, Optional, Any


# PNP ID to Manufacturer Name mapping (partial list of common manufacturers)
PNP_MANUFACTURERS = {
    'ACR': 'Acer',
    'ACI': 'ASUS',
    'AOC': 'AOC',
    'APP': 'Apple',
    'AUO': 'AU Optronics',
    'BNQ': 'BenQ',
    'BOE': 'BOE',
    'CMN': 'Chimei Innolux',
    'DEL': 'Dell',
    'EIZ': 'EIZO',
    'ENC': 'Eizo Nanao',
    'GSM': 'LG Electronics',
    'HPN': 'HP',
    'HWP': 'HP',
    'IVM': 'Iiyama',
    'LEN': 'Lenovo',
    'LGD': 'LG Display',
    'MEI': 'Panasonic',
    'MSI': 'MSI',
    'NEC': 'NEC',
    'PHL': 'Philips',
    'SAM': 'Samsung',
    'SDC': 'Samsung Display',
    'SEC': 'Samsung Electronics',
    'SNY': 'Sony',
    'VIZ': 'Vizio',
    'VSC': 'ViewSonic',
}


class EDIDParser:
    """Parser for EDID binary data."""

    def __init__(self, edid_data: bytes):
        """
        Initialize parser with EDID data.

        Args:
            edid_data: Raw EDID binary data (128 or 256 bytes typically)
        """
        if isinstance(edid_data, str):
            # Try to decode as hex string or base64
            try:
                edid_data = bytes.fromhex(edid_data)
            except ValueError:
                try:
                    edid_data = base64.b64decode(edid_data)
                except Exception:
                    raise ValueError("Invalid EDID data format")

        if len(edid_data) < 128:
            raise ValueError(f"EDID data too short: {len(edid_data)} bytes (minimum 128)")

        self.data = edid_data
        self.parsed = {}

    def parse(self) -> Dict[str, Any]:
        """Parse EDID data and return structured information."""
        if not self._validate_header():
            raise ValueError("Invalid EDID header")

        self.parsed = {
            'valid': True,
            'version': self._get_version(),
            'manufacturer': self._parse_manufacturer(),
            'product': self._parse_product(),
            'manufacture_date': self._parse_manufacture_date(),
            'display': self._parse_display_parameters(),
            'features': self._parse_features(),
            'timing': self._parse_timing(),
            'descriptors': self._parse_descriptors(),
            'raw_base64': base64.b64encode(self.data).decode('utf-8')
        }

        return self.parsed

    def _validate_header(self) -> bool:
        """Validate EDID header (first 8 bytes)."""
        expected_header = bytes([0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00])
        return self.data[:8] == expected_header

    def _get_version(self) -> Dict[str, int]:
        """Get EDID version and revision."""
        return {
            'major': self.data[18],
            'minor': self.data[19],
            'string': f"{self.data[18]}.{self.data[19]}"
        }

    def _parse_manufacturer(self) -> Dict[str, str]:
        """Parse manufacturer ID from bytes 8-9."""
        # Manufacturer ID is encoded as 3 5-bit characters
        mfg_bytes = struct.unpack('>H', self.data[8:10])[0]

        char1 = ((mfg_bytes >> 10) & 0x1F) + ord('A') - 1
        char2 = ((mfg_bytes >> 5) & 0x1F) + ord('A') - 1
        char3 = (mfg_bytes & 0x1F) + ord('A') - 1

        pnp_id = chr(char1) + chr(char2) + chr(char3)
        manufacturer_name = PNP_MANUFACTURERS.get(pnp_id, pnp_id)

        return {
            'pnp_id': pnp_id,
            'name': manufacturer_name
        }

    def _parse_product(self) -> Dict[str, Any]:
        """Parse product code and serial number."""
        product_code = struct.unpack('<H', self.data[10:12])[0]
        serial_number = struct.unpack('<I', self.data[12:16])[0]

        return {
            'code': f"{product_code:04X}",
            'code_decimal': product_code,
            'serial_number': serial_number if serial_number != 0 else None,
            'serial_hex': f"{serial_number:08X}" if serial_number != 0 else None
        }

    def _parse_manufacture_date(self) -> Dict[str, Any]:
        """Parse manufacture week and year."""
        week = self.data[16]
        year_offset = self.data[17]

        # Year is offset from 1990
        year = 1990 + year_offset

        # Week 255 means model year
        if week == 255:
            formatted = f"Model Year {year}"
        elif week == 0:
            formatted = f"{year}"
        else:
            formatted = f"Week {week}, {year}"

        return {
            'week': week if week not in (0, 255) else None,
            'year': year,
            'formatted': formatted
        }

    def _parse_display_parameters(self) -> Dict[str, Any]:
        """Parse display parameters from byte 20-24."""
        video_input = self.data[20]

        # Check if digital or analog
        is_digital = bool(video_input & 0x80)

        result = {
            'is_digital': is_digital
        }

        if is_digital:
            # Digital display
            color_depth_map = {
                0: 'undefined',
                1: 6,
                2: 8,
                3: 10,
                4: 12,
                5: 14,
                6: 16,
                7: 'reserved'
            }
            color_depth_bits = (video_input >> 4) & 0x07
            result['color_depth'] = color_depth_map.get(color_depth_bits, 'unknown')

            interface_map = {
                0: 'undefined',
                1: 'DVI',
                2: 'HDMI-a',
                3: 'HDMI-b',
                4: 'MDDI',
                5: 'DisplayPort'
            }
            interface_type = video_input & 0x0F
            result['interface'] = interface_map.get(interface_type, 'unknown')
        else:
            # Analog display
            result['signal_level'] = (video_input >> 5) & 0x03
            result['sync_types'] = video_input & 0x0F

        # Screen size (bytes 21-22)
        width_cm = self.data[21]
        height_cm = self.data[22]

        if width_cm > 0 and height_cm > 0:
            diagonal_cm = math.sqrt(width_cm ** 2 + height_cm ** 2)
            diagonal_inches = round(diagonal_cm / 2.54, 1)

            result['screen_size'] = {
                'width_cm': width_cm,
                'height_cm': height_cm,
                'diagonal_inches': diagonal_inches
            }

            # Calculate aspect ratio
            from math import gcd
            divisor = gcd(width_cm, height_cm)
            ratio_w = width_cm // divisor
            ratio_h = height_cm // divisor
            result['screen_size']['aspect_ratio'] = f"{ratio_w}:{ratio_h}"
        else:
            result['screen_size'] = None

        # Gamma (byte 23)
        gamma_byte = self.data[23]
        if gamma_byte != 255:
            result['gamma'] = round((gamma_byte + 100) / 100, 2)
        else:
            result['gamma'] = None

        return result

    def _parse_features(self) -> Dict[str, bool]:
        """Parse feature support byte (byte 24)."""
        features = self.data[24]

        return {
            'dpms_standby': bool(features & 0x80),
            'dpms_suspend': bool(features & 0x40),
            'dpms_active_off': bool(features & 0x20),
            'display_type': (features >> 3) & 0x03,
            'srgb_default': bool(features & 0x04),
            'preferred_timing': bool(features & 0x02),
            'continuous_frequency': bool(features & 0x01)
        }

    def _parse_timing(self) -> Dict[str, Any]:
        """Parse timing information."""
        result = {
            'established': self._parse_established_timings(),
            'standard': self._parse_standard_timings()
        }

        return result

    def _parse_established_timings(self) -> List[str]:
        """Parse established timing bitmaps (bytes 35-37)."""
        timings = []

        # Established timing I (byte 35)
        et1 = self.data[35]
        if et1 & 0x80:
            timings.append("720x400@70Hz")
        if et1 & 0x40:
            timings.append("720x400@88Hz")
        if et1 & 0x20:
            timings.append("640x480@60Hz")
        if et1 & 0x10:
            timings.append("640x480@67Hz")
        if et1 & 0x08:
            timings.append("640x480@72Hz")
        if et1 & 0x04:
            timings.append("640x480@75Hz")
        if et1 & 0x02:
            timings.append("800x600@56Hz")
        if et1 & 0x01:
            timings.append("800x600@60Hz")

        # Established timing II (byte 36)
        et2 = self.data[36]
        if et2 & 0x80:
            timings.append("800x600@72Hz")
        if et2 & 0x40:
            timings.append("800x600@75Hz")
        if et2 & 0x20:
            timings.append("832x624@75Hz")
        if et2 & 0x10:
            timings.append("1024x768@87Hz")
        if et2 & 0x08:
            timings.append("1024x768@60Hz")
        if et2 & 0x04:
            timings.append("1024x768@70Hz")
        if et2 & 0x02:
            timings.append("1024x768@75Hz")
        if et2 & 0x01:
            timings.append("1280x1024@75Hz")

        # Manufacturer's timing (byte 37)
        et3 = self.data[37]
        if et3 & 0x80:
            timings.append("1152x870@75Hz")

        return timings

    def _parse_standard_timings(self) -> List[Dict[str, int]]:
        """Parse standard timing identifications (bytes 38-53)."""
        timings = []

        for i in range(8):
            offset = 38 + (i * 2)
            byte1 = self.data[offset]
            byte2 = self.data[offset + 1]

            # Skip unused entries
            if byte1 == 0x01 and byte2 == 0x01:
                continue
            if byte1 == 0x00:
                continue

            # Calculate horizontal resolution
            h_res = (byte1 + 31) * 8

            # Get aspect ratio
            aspect = (byte2 >> 6) & 0x03
            aspect_ratios = {
                0: (16, 10),
                1: (4, 3),
                2: (5, 4),
                3: (16, 9)
            }

            ar = aspect_ratios.get(aspect, (16, 9))
            v_res = h_res * ar[1] // ar[0]

            # Get refresh rate
            refresh = (byte2 & 0x3F) + 60

            timings.append({
                'width': h_res,
                'height': v_res,
                'refresh': refresh,
                'string': f"{h_res}x{v_res}@{refresh}Hz"
            })

        return timings

    def _parse_descriptors(self) -> Dict[str, Any]:
        """Parse 18-byte descriptor blocks (bytes 54-125)."""
        result = {
            'monitor_name': None,
            'serial_string': None,
            'range_limits': None,
            'detailed_timings': []
        }

        for i in range(4):
            offset = 54 + (i * 18)
            descriptor = self.data[offset:offset + 18]

            # Check if it's a timing descriptor or display descriptor
            if descriptor[0] == 0 and descriptor[1] == 0:
                # Display descriptor
                desc_type = descriptor[3]

                if desc_type == 0xFC:
                    # Monitor name
                    name_bytes = descriptor[5:18]
                    result['monitor_name'] = self._decode_descriptor_string(name_bytes)

                elif desc_type == 0xFF:
                    # Serial number string
                    serial_bytes = descriptor[5:18]
                    result['serial_string'] = self._decode_descriptor_string(serial_bytes)

                elif desc_type == 0xFD:
                    # Range limits
                    result['range_limits'] = {
                        'min_v_rate': descriptor[5],
                        'max_v_rate': descriptor[6],
                        'min_h_rate': descriptor[7],
                        'max_h_rate': descriptor[8],
                        'max_pixel_clock': descriptor[9] * 10
                    }

                elif desc_type == 0xFE:
                    # Unspecified text (often manufacturer info)
                    pass

            else:
                # Detailed timing descriptor
                timing = self._parse_detailed_timing(descriptor)
                if timing:
                    result['detailed_timings'].append(timing)

        return result

    def _decode_descriptor_string(self, data: bytes) -> str:
        """Decode a descriptor string, removing padding."""
        # Find newline (0x0A) which terminates the string
        try:
            end = data.index(0x0A)
            data = data[:end]
        except ValueError:
            pass

        # Remove trailing spaces and null bytes
        return data.decode('ascii', errors='ignore').strip('\x00 ')

    def _parse_detailed_timing(self, data: bytes) -> Optional[Dict[str, Any]]:
        """Parse a detailed timing descriptor."""
        if len(data) < 18:
            return None

        # Pixel clock in 10 kHz units
        pixel_clock = struct.unpack('<H', data[0:2])[0]
        if pixel_clock == 0:
            return None

        pixel_clock_mhz = pixel_clock * 0.01

        # Horizontal
        h_active = data[2] | ((data[4] & 0xF0) << 4)
        h_blanking = data[3] | ((data[4] & 0x0F) << 8)

        # Vertical
        v_active = data[5] | ((data[7] & 0xF0) << 4)
        v_blanking = data[6] | ((data[7] & 0x0F) << 8)

        # Image size in mm
        h_size_mm = data[12] | ((data[14] & 0xF0) << 4)
        v_size_mm = data[13] | ((data[14] & 0x0F) << 8)

        # Calculate refresh rate
        h_total = h_active + h_blanking
        v_total = v_active + v_blanking
        if h_total > 0 and v_total > 0:
            refresh_rate = round((pixel_clock_mhz * 1000000) / (h_total * v_total), 2)
        else:
            refresh_rate = 0

        return {
            'pixel_clock_mhz': pixel_clock_mhz,
            'width': h_active,
            'height': v_active,
            'h_blanking': h_blanking,
            'v_blanking': v_blanking,
            'h_size_mm': h_size_mm,
            'v_size_mm': v_size_mm,
            'refresh_rate': refresh_rate,
            'string': f"{h_active}x{v_active}@{int(refresh_rate)}Hz"
        }

    def get_native_resolution(self) -> Optional[Dict[str, int]]:
        """Get the native resolution (first detailed timing)."""
        if not self.parsed:
            self.parse()

        timings = self.parsed.get('descriptors', {}).get('detailed_timings', [])
        if timings:
            first = timings[0]
            return {
                'width': first['width'],
                'height': first['height'],
                'refresh_rate': first['refresh_rate'],
                'string': first['string']
            }

        return None

    def get_monitor_name(self) -> Optional[str]:
        """Get monitor name from descriptors."""
        if not self.parsed:
            self.parse()

        return self.parsed.get('descriptors', {}).get('monitor_name')

    def get_serial_string(self) -> Optional[str]:
        """Get serial number string from descriptors."""
        if not self.parsed:
            self.parse()

        return self.parsed.get('descriptors', {}).get('serial_string')

    def to_flat_dict(self) -> Dict[str, Any]:
        """Return a flattened dictionary suitable for API submission."""
        if not self.parsed:
            self.parse()

        native = self.get_native_resolution()
        display = self.parsed.get('display', {})
        screen_size = display.get('screen_size') or {}
        mfg = self.parsed.get('manufacturer', {})
        product = self.parsed.get('product', {})
        mfg_date = self.parsed.get('manufacture_date', {})
        descriptors = self.parsed.get('descriptors', {})
        range_limits = descriptors.get('range_limits') or {}
        timing = self.parsed.get('timing', {})

        # Collect all supported resolutions
        supported = []
        for t in timing.get('established', []):
            supported.append(t)
        for t in timing.get('standard', []):
            supported.append(t.get('string', ''))
        for t in descriptors.get('detailed_timings', []):
            supported.append(t.get('string', ''))

        return {
            'manufacturer_id': mfg.get('pnp_id'),
            'manufacturer_name': mfg.get('name'),
            'product_code': product.get('code'),
            'serial_number': descriptors.get('serial_string') or str(product.get('serial_number') or ''),
            'model_name': descriptors.get('monitor_name'),
            'manufacture_week': mfg_date.get('week'),
            'manufacture_year': mfg_date.get('year'),
            'manufacture_date_formatted': mfg_date.get('formatted'),
            'native_resolution_width': native.get('width') if native else None,
            'native_resolution_height': native.get('height') if native else None,
            'native_resolution': native.get('string') if native else None,
            'screen_width_cm': screen_size.get('width_cm'),
            'screen_height_cm': screen_size.get('height_cm'),
            'diagonal_inches': screen_size.get('diagonal_inches'),
            'aspect_ratio': screen_size.get('aspect_ratio'),
            'max_horizontal_freq_khz': range_limits.get('max_h_rate'),
            'max_vertical_freq_hz': range_limits.get('max_v_rate'),
            'max_pixel_clock_mhz': range_limits.get('max_pixel_clock'),
            'color_bit_depth': display.get('color_depth') if isinstance(display.get('color_depth'), int) else None,
            'edid_version': self.parsed.get('version', {}).get('string'),
            'edid_raw': self.parsed.get('raw_base64'),
            'supported_resolutions': list(set(supported))
        }


def parse_edid(data: bytes) -> Dict[str, Any]:
    """Convenience function to parse EDID data."""
    parser = EDIDParser(data)
    return parser.parse()


def parse_edid_to_flat(data: bytes) -> Dict[str, Any]:
    """Convenience function to parse EDID to flat dict for API."""
    parser = EDIDParser(data)
    parser.parse()
    return parser.to_flat_dict()
