import logging

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class TxtExtractor(BaseExtractor):

    def extract(self, file_path: str, progress_callback=None) -> str:
        logger.info(f"Extracting text from TXT file '{file_path}'")
        progress_callback(20, 100)  # Initial progress update
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()