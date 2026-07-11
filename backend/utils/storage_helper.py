from pathlib import Path

from config.storage import ALL_STORAGE_DIRS


def create_storage_directories():

    for directory in ALL_STORAGE_DIRS:
        directory.mkdir(
            parents=True,
            exist_ok=True
        )