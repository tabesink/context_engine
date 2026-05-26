import logging
import time

from app.core.config import get_settings
from app.workers.tasks import poll_lightrag_statuses

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    interval_seconds = max(settings.lightrag_status_poll_interval_seconds, 1.0)
    logger.info("Starting LightRAG status poller with interval=%ss", interval_seconds)
    while True:
        try:
            poll_lightrag_statuses()
        except Exception:
            logger.exception("LightRAG status poll iteration failed")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
