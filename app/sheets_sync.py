import gspread
from app.config import GOOGLE_SHEETS_ENABLED, GOOGLE_SHEETS_ID

class SheetsSync:
    def __init__(self, credentials_file='credentials.json', sheet_id=GOOGLE_SHEETS_ID):
        self.enabled = GOOGLE_SHEETS_ENABLED
        self.sheet_id = sheet_id
        self.client = None
        self.sheet = None
        if self.enabled:
            try:
                self.client = gspread.service_account(filename=credentials_file)
                self.sheet = self.client.open_by_key(self.sheet_id).sheet1
            except Exception as e:
                print(f"Error connecting to Google Sheets: {e}")
                self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    def sync_attendance(self, date: str, attendance_records: list):
        if not self.is_enabled():
            return
        
        try:
            # attendance_records should be dict mapping roll_number to bool
            headers = self.sheet.row_values(1)
            if not headers:
                headers = ["Roll No", "Name"]
                self.sheet.append_row(headers)
            
            if date not in headers:
                headers.append(date)
                # Update headers
                cell_range = f"{gspread.utils.rowcol_to_a1(1, 1)}:{gspread.utils.rowcol_to_a1(1, len(headers))}"
                self.sheet.update(cell_range, [headers])
                
            date_col_idx = headers.index(date) + 1
            
            all_records = self.sheet.get_all_records()
            roll_to_row = {str(record.get('Roll No', '')): idx + 2 for idx, record in enumerate(all_records)}
            
            cells_to_update = []
            
            # For each record in list (assuming dict with roll_number, name, present)
            for record in attendance_records:
                roll = str(record['roll_number'])
                present = "P" if record['present'] else "A"
                if roll in roll_to_row:
                    row_idx = roll_to_row[roll]
                    cells_to_update.append(gspread.Cell(row=row_idx, col=date_col_idx, value=present))
                else:
                    # Append new row
                    new_row = [roll, record.get('name', '')] + [""] * (len(headers) - 2)
                    new_row[date_col_idx - 1] = present
                    self.sheet.append_row(new_row)
                    roll_to_row[roll] = len(all_records) + 2
                    all_records.append({'Roll No': roll, 'Name': record.get('name', '')})
                    
            if cells_to_update:
                self.sheet.update_cells(cells_to_update)
        except Exception as e:
            print(f"Failed to sync attendance to sheets: {e}")
