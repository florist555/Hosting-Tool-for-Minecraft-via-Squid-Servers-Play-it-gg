import json
import socket
import uuid
from pathlib import Path

from models import WorldProfile

# Everything the app stores lives next to this file, on E:, not C:.
APP_DIR = Path(__file__).resolve().parent / "AppData"
CONFIG_FILE = APP_DIR / "config.json"
BACKUP_DIR = APP_DIR / "backups"
LOG_DIR = APP_DIR / "logs"

# ---------------------------------------------------------------------------
# World / storage profiles. You (the admin) edit this dict directly.
# Friends never see or edit this file. They only type the "code" below
# into the app's Settings screen.
# ---------------------------------------------------------------------------
PROFILES = {
    "MINECRAFT-WORLD": WorldProfile(
        code="MINECRAFT-WORLD",
        remote="mega",
        remote_path="MinecraftShared/MinecraftWorld",
    ),
}

DEFAULT_CONFIG = {
    "server_path": "",
    "world_code": "",
    "backup_count": 3,
}


class ConfigManager:
    def __init__(self):
        APP_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.data = self._load_config()
        self.host_id = self._load_host_id()

    def _load_config(self):
        if not CONFIG_FILE.exists():
            return dict(DEFAULT_CONFIG)
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            result = dict(DEFAULT_CONFIG)
            result.update(data)
            return result
        except Exception:
            return dict(DEFAULT_CONFIG)

    def save(self):
        CONFIG_FILE.write_text(
            json.dumps(self.data, indent=2),
            encoding="utf-8",
        )

    def _load_host_id(self):
        path = APP_DIR / "host_id"
        if path.exists():
            return path.read_text(encoding="utf-8").strip()

        value = f"{socket.gethostname()}-{uuid.uuid4().hex[:10]}"
        path.write_text(value, encoding="utf-8")
        return value

    def profiles(self):
        return PROFILES

    def current_profile(self):
        code = self.data.get("world_code", "").strip()
        return PROFILES.get(code)