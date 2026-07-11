from services.file_validator import FileValidator

print("Allowed Categories:")
print(FileValidator.validate_document_category("prescription"))

print("Extension:")
print(FileValidator.validate_extension("report.pdf"))

print("File Type:")
print(FileValidator.validate_file_type(".pdf"))