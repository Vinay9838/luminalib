import logging

import pdfplumber

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class PdfExtractor(BaseExtractor):

    def extract(self, file_path: str) -> str:
        logger.info(f"Extracting text from PDF file '{file_path}'")

        text = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)

        return "\n".join(text)