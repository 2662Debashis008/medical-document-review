from pathlib import Path

from config.storage import STORAGE_PATHS

print("Prescription Image Folder")

print(STORAGE_PATHS["prescription"]["image"])

print()

print("Xray PDF Folder")

print(STORAGE_PATHS["xray"]["pdf"])

print()

print("Exists?")

print(Path(STORAGE_PATHS["prescription"]["image"]).exists())