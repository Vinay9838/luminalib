import os
import logging
from venv import logger

from .pdf_extractor import PdfExtractor
from .text_extractor import TxtExtractor

logger = logging.getLogger(__name__)


def get_extractor(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    logger.info(f"Determining extractor for file '{file_path}' with extension '{ext}'")
    if ext == ".pdf":
        return PdfExtractor()

    if ext == ".txt":
        return TxtExtractor()

    raise ValueError("Unsupported file type")