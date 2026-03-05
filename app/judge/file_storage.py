import os

BASE_STORAGE_DIR = os.path.abspath("submissions_storage")


def save_submission_file(submission_id: int, code: str, language: str) -> str:
    os.makedirs(BASE_STORAGE_DIR, exist_ok=True)

    extension_map = {
        "python": "py",
        "cpp": "cpp"
    }

    ext = extension_map.get(language)
    if not ext:
        raise ValueError("Unsupported language")

    file_name = f"{submission_id}.{ext}"
    file_path = os.path.join(BASE_STORAGE_DIR, file_name)

    with open(file_path, "w") as f:
        f.write(code)

    return file_path