from .factory import get_extractor


def extract_text(file_path: str) -> str:
    extractor = get_extractor(file_path)
    return extractor.extract(file_path)