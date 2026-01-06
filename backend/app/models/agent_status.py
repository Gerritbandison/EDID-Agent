"""
Agent Status Model - Tracks agent health and connection status
"""
from datetime import datetime, timezone
from app import db


class AgentStatus(db.Model):
    """Agent status model for tracking agent health."""
    __tablename__ = 'agent_statuses'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(64), db.ForeignKey('devices.id'), unique=True, nullable=False)

    # Agent Information
    agent_version = db.Column(db.String(20))
    agent_platform = db.Column(db.String(50))  # windows, macos, linux

    # Connection Status
    connection_status = db.Column(db.String(20), default='unknown')  # online, idle, offline, unknown
    last_heartbeat = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_successful_sync = db.Column(db.DateTime)

    # Check-in Statistics
    total_check_ins = db.Column(db.Integer, default=0)
    successful_check_ins = db.Column(db.Integer, default=0)
    failed_check_ins = db.Column(db.Integer, default=0)
    consecutive_failures = db.Column(db.Integer, default=0)

    # Configuration
    check_in_interval_seconds = db.Column(db.Integer, default=1800)  # 30 minutes

    # Error tracking
    last_error = db.Column(db.Text)
    last_error_time = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<AgentStatus device={self.device_id} status={self.connection_status}>'

    def update_heartbeat(self):
        """Update heartbeat timestamp and status."""
        self.last_heartbeat = datetime.now(timezone.utc)
        self.connection_status = 'online'
        self.consecutive_failures = 0

    def record_check_in(self, success=True, error=None):
        """Record a check-in attempt."""
        # Initialize counters if None (new record not yet committed)
        if self.total_check_ins is None:
            self.total_check_ins = 0
        if self.successful_check_ins is None:
            self.successful_check_ins = 0
        if self.failed_check_ins is None:
            self.failed_check_ins = 0
        if self.consecutive_failures is None:
            self.consecutive_failures = 0

        self.total_check_ins += 1
        if success:
            self.successful_check_ins += 1
            self.last_successful_sync = datetime.now(timezone.utc)
            self.consecutive_failures = 0
        else:
            self.failed_check_ins += 1
            self.consecutive_failures += 1
            if error:
                self.last_error = str(error)
                self.last_error_time = datetime.now(timezone.utc)

    def calculate_status(self):
        """Calculate current status based on last heartbeat."""
        if not self.last_heartbeat:
            return 'unknown'

        now = datetime.now(timezone.utc)
        last_hb = self.last_heartbeat.replace(tzinfo=timezone.utc) if self.last_heartbeat.tzinfo is None else self.last_heartbeat
        delta = now - last_hb

        if delta.total_seconds() < 3600:  # Less than 1 hour
            return 'online'
        elif delta.total_seconds() < 86400:  # Less than 24 hours
            return 'idle'
        else:
            return 'offline'

    def to_dict(self):
        """Convert agent status to dictionary representation."""
        return {
            'device_id': self.device_id,
            'agent_version': self.agent_version,
            'agent_platform': self.agent_platform,
            'connection_status': self.calculate_status(),
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'last_successful_sync': self.last_successful_sync.isoformat() if self.last_successful_sync else None,
            'statistics': {
                'total_check_ins': self.total_check_ins,
                'successful_check_ins': self.successful_check_ins,
                'failed_check_ins': self.failed_check_ins,
                'success_rate': round(self.successful_check_ins / self.total_check_ins * 100, 2) if self.total_check_ins > 0 else 0,
                'consecutive_failures': self.consecutive_failures
            },
            'check_in_interval_seconds': self.check_in_interval_seconds,
            'last_error': self.last_error,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None
        }
