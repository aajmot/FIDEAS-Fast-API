import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

class EnhancedDataGrid(ctk.CTkFrame):
    def __init__(self, parent, columns, on_row_select=None, on_delete=None, items_per_page=100, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.columns = columns  # [{'key': 'id', 'title': 'ID', 'width': 100}, ...]
        self.on_row_select = on_row_select
        self.on_delete = on_delete
        self.items_per_page = items_per_page
        
        # Data variables
        self.all_data = []
        self.filtered_data = []
        self.selected_rows = set()
        self.current_page = 1
        
        self.setup_ui()
    
    def setup_ui(self):
        # Top frame with search and delete button
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=5, pady=5)
        
        # Delete selected button with icon
        self.delete_btn = ctk.CTkButton(
            top_frame, 
            text="🗑 Delete", 
            width=100, 
            height=30,
            command=self.delete_selected,
            state="disabled"
        )
        self.delete_btn.pack(side="left", padx=5, pady=5)
        self.create_tooltip(self.delete_btn, "Delete selected rows")
        
        # Export button
        export_btn = ctk.CTkButton(
            top_frame, 
            text="📊 Export", 
            width=80, 
            height=30, 
            command=self.export_to_excel
        )
        export_btn.pack(side="left", padx=5, pady=5)
        
        # Search
        ctk.CTkLabel(top_frame, text="Search:", font=ctk.CTkFont(size=12)).pack(side="right", padx=(20,5), pady=5)
        self.search_input = ctk.CTkEntry(top_frame, width=200, height=30)
        self.search_input.pack(side="right", padx=5, pady=5)
        self.search_input.bind("<KeyRelease>", self.on_search)
        
        # Treeview with scrollbars
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create treeview
        tree_columns = ["select"] + [col['key'] for col in self.columns] + ["actions"]
        self.tree = ttk.Treeview(tree_frame, columns=tree_columns, show="tree headings", height=15)
        
        # Configure columns
        self.tree.column("#0", width=0, stretch=False)  # Hide tree column
        
        # Select all checkbox column
        self.tree.heading("select", text="☐", command=self.toggle_select_all)
        self.tree.column("select", width=50, minwidth=50, stretch=False, anchor="center")
        
        # Data columns
        for col in self.columns:
            self.tree.heading(col['key'], text=col['title'], command=lambda c=col['key']: self.sort_column(c))
            self.tree.column(col['key'], width=col.get('width', 100), minwidth=50, anchor="w")
        
        # Actions column
        self.tree.heading("actions", text="Actions")
        self.tree.column("actions", width=80, minwidth=80, stretch=False, anchor="center")
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Pagination controls
        pagination_frame = ctk.CTkFrame(self)
        pagination_frame.pack(fill="x", padx=5, pady=5)
        
        self.prev_btn = ctk.CTkButton(pagination_frame, text="◀", width=30, height=25, command=self.prev_page)
        self.prev_btn.pack(side="left", padx=5)
        
        self.page_label = ctk.CTkLabel(pagination_frame, text="Page 1 of 1", font=ctk.CTkFont(size=12))
        self.page_label.pack(side="left", padx=10)
        
        self.next_btn = ctk.CTkButton(pagination_frame, text="▶", width=30, height=25, command=self.next_page)
        self.next_btn.pack(side="left", padx=5)
        
        # Bind events
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Style configuration
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
    
    def set_data(self, data):
        """Set data for the grid"""
        self.all_data = data
        self.selected_rows.clear()
        self.refresh_data()
    
    def refresh_data(self):
        """Refresh the displayed data with pagination"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Filter data based on search
        search_term = self.search_input.get().lower()
        self.filtered_data = []
        
        for item in self.all_data:
            if not search_term:
                self.filtered_data.append(item)
            else:
                # Search in all columns
                for col in self.columns:
                    if search_term in str(item.get(col['key'], '')).lower():
                        self.filtered_data.append(item)
                        break
        
        # Calculate pagination
        total_items = len(self.filtered_data)
        total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_items)
        page_data = self.filtered_data[start_idx:end_idx]
        
        # Insert page data
        for i, row_data in enumerate(page_data):
            item_id = self.tree.insert("", "end", iid=str(start_idx + i))
            
            # Checkbox column
            checkbox = "☑" if str(start_idx + i) in self.selected_rows else "☐"
            self.tree.set(item_id, "select", checkbox)
            
            # Data columns
            for col in self.columns:
                self.tree.set(item_id, col['key'], str(row_data.get(col['key'], '')))
            
            # Actions column
            self.tree.set(item_id, "actions", "🗑")
        
        # Update pagination info
        self.page_label.configure(text=f"Page {self.current_page} of {total_pages} ({total_items} total)")
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")
        
        # Update delete button state
        self.update_delete_button()
        
        # Update select all checkbox
        self.update_select_all_checkbox()
    
    def on_tree_click(self, event):
        """Handle tree click events"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            
            if column == "#1":  # Select column
                self.toggle_row_selection(item)
            elif column == f"#{len(self.columns) + 2}":  # Actions column
                self.delete_single_row(item)
    
    def on_double_click(self, event):
        """Handle double click for row selection"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if item and self.on_row_select:
            row_data = self.get_row_data(item)
            if row_data:
                self.on_row_select(row_data)
    
    def toggle_row_selection(self, item):
        """Toggle selection of a single row"""
        if item in self.selected_rows:
            self.selected_rows.remove(item)
            self.tree.set(item, "select", "☐")
        else:
            self.selected_rows.add(item)
            self.tree.set(item, "select", "☑")
        
        self.update_delete_button()
        self.update_select_all_checkbox()
    
    def toggle_select_all(self):
        """Toggle selection of all rows"""
        all_items = self.tree.get_children()
        
        if len(self.selected_rows) == len(all_items):
            # Deselect all
            self.selected_rows.clear()
            for item in all_items:
                self.tree.set(item, "select", "☐")
            self.tree.heading("select", text="☐")
        else:
            # Select all
            self.selected_rows = set(all_items)
            for item in all_items:
                self.tree.set(item, "select", "☑")
            self.tree.heading("select", text="☑")
        
        self.update_delete_button()
    
    def update_select_all_checkbox(self):
        """Update the select all checkbox state"""
        all_items = self.tree.get_children()
        if not all_items:
            self.tree.heading("select", text="☐")
        elif len(self.selected_rows) == len(all_items):
            self.tree.heading("select", text="☑")
        elif len(self.selected_rows) > 0:
            self.tree.heading("select", text="☑")  # Partially selected
        else:
            self.tree.heading("select", text="☐")
    
    def update_delete_button(self):
        """Update delete button state"""
        if self.selected_rows:
            self.delete_btn.configure(state="normal")
        else:
            self.delete_btn.configure(state="disabled")
    
    def delete_single_row(self, item):
        """Delete a single row"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?"):\n            row_data = self.get_row_data(item)
            if row_data and self.on_delete:
                if self.on_delete([row_data]):
                    # Remove from data and refresh
                    self.all_data = [d for d in self.all_data if d != row_data]
                    self.selected_rows.discard(item)
                    self.refresh_data()
    
    def delete_selected(self):
        """Delete all selected rows"""
        if not self.selected_rows:
            return
        
        count = len(self.selected_rows)
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {count} item(s)?"):
            # Get data for selected rows
            selected_data = []
            for item in self.selected_rows:
                row_data = self.get_row_data(item)
                if row_data:
                    selected_data.append(row_data)
            
            if selected_data and self.on_delete:
                if self.on_delete(selected_data):
                    # Remove from data and refresh
                    for data in selected_data:
                        if data in self.all_data:
                            self.all_data.remove(data)
                    self.selected_rows.clear()
                    self.refresh_data()
    
    def get_row_data(self, item):
        """Get original data for a tree item"""
        try:
            # Get the actual index from the item id
            item_index = int(item)
            if 0 <= item_index < len(self.filtered_data):
                return self.filtered_data[item_index]
        except:
            pass
        return None
    
    def on_search(self, event):
        """Handle search input"""
        self.selected_rows.clear()
        self.current_page = 1
        self.refresh_data()
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.selected_rows.clear()
            self.refresh_data()
    
    def next_page(self):
        """Go to next page"""
        total_pages = max(1, (len(self.filtered_data) + self.items_per_page - 1) // self.items_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self.selected_rows.clear()
            self.refresh_data()
    
    def create_tooltip(self, widget, text):
        """Create tooltip for widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def sort_column(self, col):
        """Sort by column"""
        # Simple sort implementation
        reverse = getattr(self, f'_sort_{col}_reverse', False)
        self.all_data.sort(key=lambda x: str(x.get(col, '')), reverse=reverse)
        setattr(self, f'_sort_{col}_reverse', not reverse)
        self.refresh_data()
    
    def get_selected_data(self):
        """Get data for selected rows"""
        selected_data = []
        for item in self.selected_rows:
            row_data = self.get_row_data(item)
            if row_data:
                selected_data.append(row_data)
        return selected_data
    
    def export_to_excel(self):
        """Export grid data to Excel"""
        try:
            import pandas as pd
            from tkinter import filedialog
            from datetime import datetime
            
            if not self.all_data:
                messagebox.showwarning("No Data", "No data to export")
                return
            
            df = pd.DataFrame(self.all_data)
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if filename:
                df.to_excel(filename, index=False)
                messagebox.showinfo("Success", f"{len(self.all_data)} records exported to {filename}")
                
        except ImportError:
            messagebox.showerror("Error", "pandas library required. Install with: pip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")