import os
import shutil #for CSV processing
import openpyxl  # For XLSX processing

def process_file(input_path: str, output_path: str) -> bool:
    """Processes an XLSX or CSV file.

    For XLSX: Modifies cell A1 to "Hello World".
    For CSV: Copies the file (no modification).

    Args:
        input_path: Path to the original uploaded file.
        output_path: Path to save the processed file.

    Returns:
        True if processing was successful, False otherwise.
    """
    try:
        file_extension = os.path.splitext(input_path)[1].lower()

        if file_extension == ".xlsx":
            workbook = openpyxl.load_workbook(input_path)
            sheet = workbook.active  # Or select a specific sheet
            sheet["A1"] = "Hello World"
            workbook.save(output_path)
        elif file_extension == ".csv":
            shutil.copyfile(input_path, output_path)  # Just copy CSV files
        else:
            return False #Should not happen, but handle just in case

        return True
    except Exception as e:
        print(f"Error processing file: {e}")  # Log errors
        return False
