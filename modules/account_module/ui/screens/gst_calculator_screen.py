"""GST Calculator Screen"""
import customtkinter as ctk
from modules.account_module.services.gst_service import GSTService

class GSTCalculatorScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.setup_ui()
    
    def setup_ui(self):
        title = ctk.CTkLabel(self, text="GST Calculator", font=("Arial", 20, "bold"))
        title.pack(pady=20)
        
        # Input frame
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(padx=20, pady=10, fill="x")
        
        # Subtotal
        ctk.CTkLabel(input_frame, text="Subtotal (₹):").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.subtotal_entry = ctk.CTkEntry(input_frame, width=200)
        self.subtotal_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # GST Rate
        ctk.CTkLabel(input_frame, text="GST Rate (%):").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.gst_rate = ctk.CTkComboBox(input_frame, values=["5", "12", "18", "28"], width=200)
        self.gst_rate.set("18")
        self.gst_rate.grid(row=1, column=1, padx=10, pady=10)
        
        # Transaction Type
        ctk.CTkLabel(input_frame, text="Transaction Type:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.transaction_type = ctk.CTkComboBox(input_frame, 
            values=["Intrastate (CGST+SGST)", "Interstate (IGST)"], width=200)
        self.transaction_type.set("Intrastate (CGST+SGST)")
        self.transaction_type.grid(row=2, column=1, padx=10, pady=10)
        
        # Calculate button
        ctk.CTkButton(input_frame, text="Calculate", command=self.calculate, 
                     width=200).grid(row=3, column=0, columnspan=2, pady=20)
        
        # Result frame
        self.result_frame = ctk.CTkFrame(self)
        self.result_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(self.result_frame, text="Calculation Results", 
                    font=("Arial", 16, "bold")).pack(pady=10)
    
    def calculate(self):
        try:
            subtotal = float(self.subtotal_entry.get())
            gst_rate = float(self.gst_rate.get())
            is_interstate = "Interstate" in self.transaction_type.get()
            
            result = GSTService.calculate_gst(subtotal, gst_rate, is_interstate)
            
            # Clear previous results
            for widget in self.result_frame.winfo_children()[1:]:
                widget.destroy()
            
            # Display results
            result_text = ctk.CTkFrame(self.result_frame)
            result_text.pack(padx=20, pady=10, fill="both", expand=True)
            
            row = 0
            if is_interstate:
                self.add_result_row(result_text, "IGST Rate:", f"{result['igst_rate']}%", row)
                row += 1
                self.add_result_row(result_text, "IGST Amount:", f"₹{result['igst_amount']:,.2f}", row)
                row += 1
            else:
                self.add_result_row(result_text, "CGST Rate:", f"{result['cgst_rate']}%", row)
                row += 1
                self.add_result_row(result_text, "CGST Amount:", f"₹{result['cgst_amount']:,.2f}", row)
                row += 1
                self.add_result_row(result_text, "SGST Rate:", f"{result['sgst_rate']}%", row)
                row += 1
                self.add_result_row(result_text, "SGST Amount:", f"₹{result['sgst_amount']:,.2f}", row)
                row += 1
            
            self.add_result_row(result_text, "Total GST:", f"₹{result['total_gst']:,.2f}", row, bold=True)
            row += 1
            self.add_result_row(result_text, "Total Amount:", f"₹{result['total_amount']:,.2f}", row, bold=True)
            
        except ValueError:
            ctk.CTkLabel(self.result_frame, text="Please enter valid numbers", 
                        text_color="red").pack(pady=10)
    
    def add_result_row(self, parent, label, value, row, bold=False):
        font = ("Arial", 14, "bold") if bold else ("Arial", 12)
        ctk.CTkLabel(parent, text=label, font=font).grid(row=row, column=0, padx=20, pady=5, sticky="e")
        ctk.CTkLabel(parent, text=value, font=font).grid(row=row, column=1, padx=20, pady=5, sticky="w")
