from dataclasses import dataclass
from typing import Optional


@dataclass
class WorldProfile:
    code: str
    remote: str
    remote_path: str


@dataclass
class SyncStatus:
    status: str
    operation: Optional[str] = None
    host_id: Optional[str] = None
    started_at: Optional[str] = None
    heartbeat_at: Optional[str] = None
    lease_seconds: int = 180

    def to_dict(self):
        return {
            "status": self.status,
            "operation": self.operation,
            "host_id": self.host_id,
            "started_at": self.started_at,
            "heartbeat_at": self.heartbeat_at,
            "lease_seconds": self.lease_seconds,
        }