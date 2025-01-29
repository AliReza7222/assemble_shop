import openpyxl
from openpyxl.utils.exceptions import InvalidFileException


def get_data(file):
    """
    Reads an Excel file and returns the headers and rows of the sheet.
    """
    try:
        wb = openpyxl.load_workbook(file, read_only=True)
        sheet = wb.active
        headers = [cell.value for cell in sheet[1] if cell.value]
        rows = [
            row
            for row in sheet.iter_rows(min_row=2, max_col=4, values_only=True)
        ]
        wb.close()
        return headers, rows

    except InvalidFileException:
        raise ValueError("The uploaded file is not a valid file.")
