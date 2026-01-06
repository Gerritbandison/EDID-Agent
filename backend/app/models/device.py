"""
Device Model - Represents laptops/computers in the inventory
"""
from datetime import datetime, timezone
from app import db


class Device(db.Model):
    """Device/Laptop model for inventory tracking."""
    __tablename__ = 'devices'

    id = db.Column(db.String(64), primary_key=True)  # UUID from agent
    hostname = db.Column(db.String(255), nullable=False, index=True)
    serial_number = db.Column(db.String(255), index=True)
    model = db.Column(db.String(255))
    manufacturer = db.Column(db.String(255), index=True)

    # Hardware specifications
    cpu_model = db.Column(db.String(255))
    cpu_cores = db.Column(db.Integer)
    cpu_threads = db.Column(db.Integer)
    ram_total_gb = db.Column(db.Float)
    storage_total_gb = db.Column(db.Float)
    storage_type = db.Column(db.String(50))  # SSD, HDD, NVMe

    # Operating System
    os_name = db.Column(db.String(100))
    os_version = db.Column(db.String(100))
    os_build = db.Column(db.String(100))
    os_architecture = db.Column(db.String(20))

    # Network
    ip_address = db.Column(db.String(45))
    mac_address = db.Column(db.String(17))

    # User Information
    assigned_user = db.Column(db.String(255), index=True)
    assigned_user_email = db.Column(db.String(255))
    domain = db.Column(db.String(255))

    # Active Directory / Entra ID
    ad_distinguished_name = db.Column(db.Text)
    ad_organizational_unit = db.Column(db.String(255))
    entra_device_id = db.Column(db.String(255))
    entra_tenant_id = db.Column(db.String(255))

    # Location (if available)
    location = db.Column(db.String(255))
    department = db.Column(db.String(255))

    # Timestamps
    first_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_check_in = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    monitors = db.relationship('Monitor', backref='device', lazy='dynamic', cascade='all, delete-orphan')
    agent_status = db.relationship('AgentStatus', backref='device', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Device {self.hostname} ({self.serial_number})>'

    def to_dict(self, include_monitors=False, include_agent_status=False):
        """Convert device to dictionary representation."""
        data = {
            'id': self.id,
            'hostname': self.hostname,
            'serial_number': self.serial_number,
            'model': self.model,
            'manufacturer': self.manufacturer,
            'hardware': {
                'cpu_model': self.cpu_model,
                'cpu_cores': self.cpu_cores,
                'cpu_threads': self.cpu_threads,
                'ram_total_gb': self.ram_total_gb,
                'storage_total_gb': self.storage_total_gb,
                'storage_type': self.storage_type
            },
            'os': {
                'name': self.os_name,
                'version': self.os_version,
                'build': self.os_build,
                'architecture': self.os_architecture
            },
            'network': {
                'ip_address': self.ip_address,
                'mac_address': self.mac_address
            },
            'user': {
                'assigned_user': self.assigned_user,
                'email': self.assigned_user_email,
                'domain': self.domain
            },
            'directory_info': {
                'ad_distinguished_name': self.ad_distinguished_name,
                'ad_organizational_unit': self.ad_organizational_unit,
                'entra_device_id': self.entra_device_id,
                'entra_tenant_id': self.entra_tenant_id
            },
            'location': self.location,
            'department': self.department,
            'timestamps': {
                'first_seen': self.first_seen.isoformat() if self.first_seen else None,
                'last_check_in': self.last_check_in.isoformat() if self.last_check_in else None,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
        }

        if include_monitors:
            data['monitors'] = [m.to_dict() for m in self.monitors]
            data['monitor_count'] = self.monitors.count()

        if include_agent_status and self.agent_status:
            data['agent_status'] = self.agent_status.to_dict()

        return data

    @classmethod
    def get_status(cls, device):
        """Determine device status based on last check-in time."""
        if not device.last_check_in:
            return 'unknown'

        now = datetime.now(timezone.utc)
        last_check_in = device.last_check_in.replace(tzinfo=timezone.utc) if device.last_check_in.tzinfo is None else device.last_check_in
        delta = now - last_check_in

        if delta.total_seconds() < 3600:  # Less than 1 hour
            return 'online'
        elif delta.total_seconds() < 86400:  # Less than 24 hours
            return 'idle'
        else:
            return 'offline'
