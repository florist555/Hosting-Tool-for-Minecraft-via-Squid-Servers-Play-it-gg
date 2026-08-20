import json
from datetime import datetime, timezone

from models import SyncStatus


STATUS_FILE = ".sync_status"


def utc_now():
    return datetime.now(timezone.utc)


def iso_now():
    return utc_now().isoformat()


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class SharedLock:
    def __init__(self, rclone, remote_root, host_id, lease_seconds=180):
        self.rclone = rclone
        self.remote_root = remote_root.rstrip("/")
        self.host_id = host_id
        self.lease_seconds = lease_seconds

    @property
    def status_path(self):
        return f"{self.remote_root}/{STATUS_FILE}"

    def read(self):
        result = self.rclone.read_text(self.status_path)
        if not result.ok:
            return SyncStatus(status="READY")

        try:
            data = json.loads(result.stdout)
            return SyncStatus(
                status=data.get("status", "READY"),
                operation=data.get("operation"),
                host_id=data.get("host_id"),
                started_at=data.get("started_at"),
                heartbeat_at=data.get("heartbeat_at"),
                lease_seconds=int(data.get("lease_seconds", self.lease_seconds)),
            )
        except Exception:
            return SyncStatus(status="SYNCING", operation="UNKNOWN")

    def is_stale(self, status):
        if status.status != "SYNCING":
            return False

        heartbeat = parse_time(status.heartbeat_at)
        if heartbeat is None:
            return True

        age = (utc_now() - heartbeat).total_seconds()
        return age > status.lease_seconds

    def acquire(self, operation):
        status = self.read()

        if status.status == "SYNCING":
            if not self.is_stale(status):
                return False, "Another host is currently synchronizing."
            return False, (
                "A stale synchronization lock was detected. "
                "Confirm no other host is syncing, then use Force Clear Lock in Settings."
            )

        payload = SyncStatus(
            status="SYNCING",
            operation=operation,
            host_id=self.host_id,
            started_at=iso_now(),
            heartbeat_at=iso_now(),
            lease_seconds=self.lease_seconds,
        ).to_dict()

        result = self.rclone.write_text(
            self.status_path,
            json.dumps(payload, indent=2),
        )
        if not result.ok:
            return False, result.stderr.strip() or "Unable to acquire synchronization lock."

        confirmed = self.read()
        if confirmed.status != "SYNCING" or confirmed.host_id != self.host_id:
            return False, "Unable to confirm synchronization lock ownership."

        return True, ""

    def heartbeat(self, operation):
        payload = SyncStatus(
            status="SYNCING",
            operation=operation,
            host_id=self.host_id,
            started_at=iso_now(),
            heartbeat_at=iso_now(),
            lease_seconds=self.lease_seconds,
        ).to_dict()
        return self.rclone.write_text(
            self.status_path,
            json.dumps(payload, indent=2),
        )

    def release_ready(self):
        payload = SyncStatus(
            status="READY",
            operation=None,
            host_id=self.host_id,
            started_at=None,
            heartbeat_at=iso_now(),
            lease_seconds=self.lease_seconds,
        ).to_dict()
        return self.rclone.write_text(
            self.status_path,
            json.dumps(payload, indent=2),
        )

    def force_clear(self):
        return self.release_ready()