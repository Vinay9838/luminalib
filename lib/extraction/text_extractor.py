import logging

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class TxtExtractor(BaseExtractor):

    def extract(self, file_path: str) -> str:
        logger.info(f"Extracting text from TXT file '{file_path}'")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()