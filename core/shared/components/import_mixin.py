from tkinter import filedialog, messagebox
from datetime import datetime
import pandas as pd
from core.shared.utils.session_manager import session_manager

class ImportMixin:
    """Mixin class to add Excel import functionality to screens"""
    
    def add_import_button(self, parent_frame):
        """Add import button to the parent frame"""
        import customtkinter as ctk
        ctk.CTkButton(parent_frame, text="Import Excel", command=self.import_from_excel, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(parent_frame, text="Download Template", command=self.download_template, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
    
    def download_template(self):
        """Download Excel template - to be overridden by child classes"""
        messagebox.showinfo("Info", "Template download not implemented for this screen")
    
    def import_from_excel(self):
        """Import data from Excel - to be overridden by child classes"""
        messagebox.showinfo("Info", "Import functionality not implemented for this screen")
    
    def validate_required_columns(self, df, required_columns):
        """Validate that all required columns are present"""
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            messagebox.showerror("Error", f"Missing required columns: {', '.join(missing_columns)}")
            return False
        return True
    
    def create_template_file(self, template_data, filename_prefix):
        """Create and save template file"""
        try:
            df = pd.DataFrame(template_data)
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=f"{filename_prefix}_template.xlsx"
            )
            
            if filename:
                df.to_excel(filename, index=False, sheet_name='Template')
                messagebox.showinfo("Success", f"Template downloaded to {filename}")
                
        except ImportError:
            messagebox.showerror("Error", "pandas library required. Install with: pip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download template: {str(e)}")
    
    def process_import_file(self, required_columns, process_row_func, filename_prefix="data"):
        """Generic import processing"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx *.xls")],
                title="Select Excel file to import"
            )
            
            if not filename:
                return
            
            df = pd.read_excel(filename)
            
            if not self.validate_required_columns(df, required_columns):
                return
            
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    if process_row_func(row, index):
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(f"Row {index + 2}: Processing failed")
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            # Show results
            message = f"Import completed:\\n- Successfully imported: {success_count} records\\n- Errors: {error_count}"
            if errors:
                message += f"\\n\\nErrors:\\n" + "\\n".join(errors[:10])
                if len(errors) > 10:
                    message += f"\\n... and {len(errors) - 10} more errors"
            
            if error_count > 0:
                messagebox.showwarning("Import Results", message)
            else:
                messagebox.showinfo("Success", message)
            
            # Refresh data if method exists
            if hasattr(self, 'load_data'):
                self.load_data()
                
        except ImportError:
            messagebox.showerror("Error", "pandas library required. Install with: pip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {str(e)}")