import logging
from config import LOG_DIR


def get_logger():
    logger = logging.getLogger("MinecraftHostHandoff")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(
        LOG_DIR / "handoff.log",
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(handler)
    return logger