"""
Monitor Model - Represents displays/monitors with parsed EDID data
"""
from datetime import datetime, timezone
from app import db


class Monitor(db.Model):
    """Monitor model with parsed EDID information."""
    __tablename__ = 'monitors'

    id = db.Column(db.String(64), primary_key=True)  # Generated from EDID data
    device_id = db.Column(db.String(64), db.ForeignKey('devices.id'), nullable=False, index=True)

    # EDID Manufacturer Information
    manufacturer_id = db.Column(db.String(10))  # 3-letter PNP ID
    manufacturer_name = db.Column(db.String(255), index=True)
    product_code = db.Column(db.String(20))
    serial_number = db.Column(db.String(255), index=True)
    model_name = db.Column(db.String(255))

    # Manufacturing Date
    manufacture_week = db.Column(db.Integer)
    manufacture_year = db.Column(db.Integer, index=True)
    manufacture_date_formatted = db.Column(db.String(50))

    # Display Specifications
    native_resolution_width = db.Column(db.Integer)
    native_resolution_height = db.Column(db.Integer)
    native_resolution = db.Column(db.String(20))  # e.g., "1920x1080"

    # Physical dimensions
    screen_width_cm = db.Column(db.Float)
    screen_height_cm = db.Column(db.Float)
    diagonal_inches = db.Column(db.Float)
    aspect_ratio = db.Column(db.String(10))  # e.g., "16:9"

    # Display capabilities
    max_horizontal_freq_khz = db.Column(db.Integer)
    max_vertical_freq_hz = db.Column(db.Integer)
    max_pixel_clock_mhz = db.Column(db.Float)
    color_bit_depth = db.Column(db.Integer)
    hdr_supported = db.Column(db.Boolean, default=False)

    # Connection
    connection_type = db.Column(db.String(50))  # HDMI, DisplayPort, USB-C, VGA, DVI
    connection_port = db.Column(db.String(50))

    # Raw EDID data (base64 encoded)
    edid_raw = db.Column(db.Text)
    edid_version = db.Column(db.String(10))

    # Supported resolutions (JSON array)
    supported_resolutions = db.Column(db.Text)

    # Status
    is_primary = db.Column(db.Boolean, default=False)
    is_connected = db.Column(db.Boolean, default=True)

    # Timestamps
    first_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Monitor {self.manufacturer_name} {self.model_name} ({self.serial_number})>'

    def calculate_age_years(self):
        """Calculate monitor age in years from manufacture date."""
        if not self.manufacture_year:
            return None
        current_year = datetime.now().year
        return current_year - self.manufacture_year

    def to_dict(self):
        """Convert monitor to dictionary representation."""
        import json

        return {
            'id': self.id,
            'device_id': self.device_id,
            'manufacturer': {
                'id': self.manufacturer_id,
                'name': self.manufacturer_name,
                'product_code': self.product_code
            },
            'serial_number': self.serial_number,
            'model_name': self.model_name,
            'manufacture_date': {
                'week': self.manufacture_week,
                'year': self.manufacture_year,
                'formatted': self.manufacture_date_formatted,
                'age_years': self.calculate_age_years()
            },
            'display': {
                'native_resolution': self.native_resolution,
                'width': self.native_resolution_width,
                'height': self.native_resolution_height,
                'screen_width_cm': self.screen_width_cm,
                'screen_height_cm': self.screen_height_cm,
                'diagonal_inches': self.diagonal_inches,
                'aspect_ratio': self.aspect_ratio,
                'color_bit_depth': self.color_bit_depth,
                'hdr_supported': self.hdr_supported
            },
            'timing': {
                'max_horizontal_freq_khz': self.max_horizontal_freq_khz,
                'max_vertical_freq_hz': self.max_vertical_freq_hz,
                'max_pixel_clock_mhz': self.max_pixel_clock_mhz
            },
            'connection': {
                'type': self.connection_type,
                'port': self.connection_port
            },
            'edid': {
                'version': self.edid_version,
                'raw': self.edid_raw
            },
            'supported_resolutions': json.loads(self.supported_resolutions) if self.supported_resolutions else [],
            'status': {
                'is_primary': self.is_primary,
                'is_connected': self.is_connected
            },
            'timestamps': {
                'first_seen': self.first_seen.isoformat() if self.first_seen else None,
                'last_seen': self.last_seen.isoformat() if self.last_seen else None
            }
        }
