from .factory import get_extractor


def extract_text(file_path: str, progress_callback=None) -> str:
    extractor = get_extractor(file_path)
    return extractor.extract(file_path, progress_callback=progress_callback)