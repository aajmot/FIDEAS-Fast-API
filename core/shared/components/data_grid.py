import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

class DataGrid(ctk.CTkFrame):
    def __init__(self, parent, columns, on_row_select=None, on_delete=None, items_per_page=100, use_enhanced=False, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.columns = columns  # [{'key': 'id', 'title': 'ID', 'width': 40}, ...]
        self.on_row_select = on_row_select
        self.on_delete = on_delete
        self.items_per_page = items_per_page
        self.use_enhanced = use_enhanced
        
        # Data variables
        self.all_data = []
        self.filtered_data = []
        self.selected_rows = set()
        self.current_page = 1
        self.sort_column = columns[0]['key'] if columns else 'id'
        self.sort_reverse = False
        self.search_term = ''
        
        if use_enhanced:
            self.setup_enhanced_ui()
        else:
            self.setup_ui()
    
    def setup_ui(self):
        # Search bar with export icon
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=5, pady=5)
        
        # Excel export icon
        export_btn = ctk.CTkButton(search_frame, text="📊", width=30, height=25, font=ctk.CTkFont(size=12), command=self.export_to_excel)
        export_btn.pack(side="left", padx=5, pady=5)
        self.create_tooltip(export_btn, "Export data to Excel")
        
        ctk.CTkLabel(search_frame, text="Search:", font=ctk.CTkFont(size=10)).pack(side="right", padx=(20,5), pady=5)
        self.search_input = ctk.CTkEntry(search_frame, width=150, height=25, font=ctk.CTkFont(size=10))
        self.search_input.pack(side="right", padx=5, pady=5)
        self.search_input.bind("<KeyRelease>", self.on_search)
        
        # Grid header
        header_frame = ctk.CTkFrame(self, fg_color="#e0e0e0")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        for col in self.columns:
            header = ctk.CTkLabel(
                header_frame, 
                text=f"{col['title']} ↕", 
                font=ctk.CTkFont(size=9, weight="bold"), 
                text_color="#333333", 
                width=col['width'], 
                cursor="hand2"
            )
            header.pack(side="left", padx=3, pady=3)
            header.bind("<Button-1>", lambda e, key=col['key']: self.sort_data(key))
        
        # Scrollable data frame
        self.data_frame = ctk.CTkScrollableFrame(self, height=250)
        self.data_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Pagination
        pagination_frame = ctk.CTkFrame(self)
        pagination_frame.pack(fill="x", padx=5, pady=5)
        
        self.prev_btn = ctk.CTkButton(pagination_frame, text="◀", width=30, height=20, font=ctk.CTkFont(size=8), command=self.prev_page)
        self.prev_btn.pack(side="left", padx=5)
        
        self.page_label = ctk.CTkLabel(pagination_frame, text="Page 1 of 1", font=ctk.CTkFont(size=9))
        self.page_label.pack(side="left", padx=10)
        
        self.next_btn = ctk.CTkButton(pagination_frame, text="▶", width=30, height=20, font=ctk.CTkFont(size=8), command=self.next_page)
        self.next_btn.pack(side="left", padx=5)
    
    def set_data(self, data):
        """Set data for the grid"""
        self.all_data = data
        self.selected_rows.clear()
        if self.use_enhanced:
            self.refresh_enhanced_data()
        else:
            self.current_page = 1
            self.display_data()
    

    
    def display_data(self):
        # Clear existing data
        for widget in self.data_frame.winfo_children():
            widget.destroy()
        
        # Filter data based on search
        filtered_data = []
        for item in self.all_data:
            match = False
            for col in self.columns:
                if self.search_term.lower() in str(item.get(col['key'], '')).lower():
                    match = True
                    break
            if match or not self.search_term:
                filtered_data.append(item)
        
        # Sort data
        filtered_data.sort(key=lambda x: x.get(self.sort_column, ''), reverse=self.sort_reverse)
        
        # Pagination
        total_items = len(filtered_data)
        total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_data = filtered_data[start_idx:end_idx]
        
        # Display rows
        for i, row_data in enumerate(page_data):
            row_color = "#f8f9fa" if i % 2 == 0 else "#ffffff"
            row_frame = ctk.CTkFrame(self.data_frame, fg_color=row_color, height=22)
            row_frame.pack(fill="x", padx=1, pady=0.5)
            row_frame.pack_propagate(False)
            
            # Row data
            for col in self.columns:
                value = str(row_data.get(col['key'], ''))
                ctk.CTkLabel(
                    row_frame, 
                    text=value, 
                    font=ctk.CTkFont(size=8), 
                    text_color="#555555", 
                    width=col['width'], 
                    anchor="w"
                ).pack(side="left", padx=3, pady=2)
            
            # Make row clickable
            if self.on_row_select:
                row_frame.bind("<Button-1>", lambda e, data=row_data: self.on_row_select(data))
                for child in row_frame.winfo_children():
                    child.bind("<Button-1>", lambda e, data=row_data: self.on_row_select(data))
        
        # Update pagination info
        self.page_label.configure(text=f"Page {self.current_page} of {total_pages}")
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")
    
    def sort_data(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.current_page = 1
        self.display_data()
    
    def on_search(self, event):
        self.search_term = self.search_input.get()
        self.current_page = 1
        self.display_data()
    
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.display_data()
    
    def next_page(self):
        filtered_count = len([item for item in self.all_data 
                             if any(self.search_term.lower() in str(item.get(col['key'], '')).lower() 
                                   for col in self.columns) or not self.search_term])
        total_pages = max(1, (filtered_count + self.items_per_page - 1) // self.items_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self.display_data()
    
    def refresh(self):
        self.display_data()
    
    def get_data(self):
        """Return all data in the grid"""
        return self.all_data
    
    def create_tooltip(self, widget, text):
        """Create tooltip for widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 8))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def setup_enhanced_ui(self):
        """Setup enhanced UI with scrollbars, checkboxes, and delete functionality"""
        # Top frame with controls
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
        self.search_input.bind("<KeyRelease>", self.on_enhanced_search)
        
        # Pagination controls at bottom - compact design
        pagination_frame = ctk.CTkFrame(self, height=35)
        pagination_frame.pack(fill="x", padx=5, pady=3, side="bottom")
        pagination_frame.pack_propagate(False)
        
        # Navigation controls - left side
        self.prev_btn = ctk.CTkButton(pagination_frame, text="◀", width=40, height=25, font=ctk.CTkFont(size=10), command=self.prev_page_enhanced)
        self.prev_btn.pack(side="left", padx=5, pady=5)
        
        self.page_label = ctk.CTkLabel(pagination_frame, text="Page 1 of 1", font=ctk.CTkFont(size=10))
        self.page_label.pack(side="left", padx=8, pady=5)
        
        self.next_btn = ctk.CTkButton(pagination_frame, text="▶", width=40, height=25, font=ctk.CTkFont(size=10), command=self.next_page_enhanced)
        self.next_btn.pack(side="left", padx=5, pady=5)
        
        # Rows per page selector - right side
        ctk.CTkLabel(pagination_frame, text="Rows:", font=ctk.CTkFont(size=9)).pack(side="right", padx=3, pady=5)
        from core.shared.utils.dropdown_migration import create_searchable_dropdown
        self.rows_combo = create_searchable_dropdown(
            pagination_frame, 
            values=["10", "20", "50", "100"], 
            width=60, 
            height=25, 
            placeholder_text="Rows",
            command=self.change_page_size
        )
        self.rows_combo.set(str(self.items_per_page))
        self.rows_combo.pack(side="right", padx=5, pady=5)
        
        # Treeview with scrollbars - now pack after pagination
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create treeview with fixed height to leave room for pagination
        tree_columns = ["select"] + [col['key'] for col in self.columns] + ["actions"]
        self.tree = ttk.Treeview(tree_frame, columns=tree_columns, show="tree headings", height=15)
        
        # Configure columns
        self.tree.column("#0", width=0, stretch=False)  # Hide tree column
        
        # Select all checkbox column
        self.tree.heading("select", text="☐", command=self.toggle_select_all)
        self.tree.column("select", width=50, minwidth=50, stretch=False, anchor="center")
        
        # Data columns
        for col in self.columns:
            self.tree.heading(col['key'], text=col['title'], command=lambda c=col['key']: self.sort_enhanced_column(c))
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
        if self.use_enhanced:
            self.refresh_enhanced_data()
        else:
            self.current_page = 1
            self.display_data()
    
    def refresh_enhanced_data(self):
        """Refresh the enhanced grid data with pagination"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Filter data based on search
        search_term = self.search_input.get().lower() if hasattr(self, 'search_input') else ''
        self.filtered_data = []
        
        for item in self.all_data:
            if not search_term:
                self.filtered_data.append(item)
            else:
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
        if hasattr(self, 'page_label'):
            self.page_label.configure(text=f"Page {self.current_page} of {total_pages} ({total_items} total)")
            self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
            self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")
        
        # Update UI state
        self.update_delete_button()
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
        else:
            self.tree.heading("select", text="☐")
    
    def update_delete_button(self):
        """Update delete button state"""
        if hasattr(self, 'delete_btn'):
            if self.selected_rows:
                self.delete_btn.configure(state="normal")
            else:
                self.delete_btn.configure(state="disabled")
    
    def delete_single_row(self, item):
        """Delete a single row"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?"):
            row_data = self.get_row_data(item)
            if row_data and self.on_delete:
                if self.on_delete([row_data]):
                    self.all_data = [d for d in self.all_data if d != row_data]
                    self.selected_rows.discard(item)
                    self.refresh_enhanced_data()
    
    def delete_selected(self):
        """Delete all selected rows"""
        if not self.selected_rows:
            return
        
        count = len(self.selected_rows)
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {count} item(s)?"):
            selected_data = []
            for item in self.selected_rows:
                row_data = self.get_row_data(item)
                if row_data:
                    selected_data.append(row_data)
            
            if selected_data and self.on_delete:
                if self.on_delete(selected_data):
                    for data in selected_data:
                        if data in self.all_data:
                            self.all_data.remove(data)
                    self.selected_rows.clear()
                    self.refresh_enhanced_data()
    
    def get_row_data(self, item):
        """Get original data for a tree item"""
        try:
            if self.use_enhanced:
                # Get the actual index from the item id
                item_index = int(item)
                if hasattr(self, 'filtered_data') and 0 <= item_index < len(self.filtered_data):
                    return self.filtered_data[item_index]
            else:
                # Original method for non-enhanced mode
                for data in self.all_data:
                    match = True
                    for col in self.columns:
                        tree_value = self.tree.set(item, col['key'])
                        data_value = str(data.get(col['key'], ''))
                        if tree_value != data_value:
                            match = False
                            break
                    if match:
                        return data
        except:
            pass
        return None
    
    def on_enhanced_search(self, event):
        """Handle enhanced search input"""
        self.selected_rows.clear()
        self.current_page = 1
        self.refresh_enhanced_data()
    
    def prev_page_enhanced(self):
        """Go to previous page in enhanced mode"""
        if self.current_page > 1:
            self.current_page -= 1
            self.selected_rows.clear()
            self.refresh_enhanced_data()
    
    def next_page_enhanced(self):
        """Go to next page in enhanced mode"""
        total_pages = max(1, (len(self.filtered_data) + self.items_per_page - 1) // self.items_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self.selected_rows.clear()
            self.refresh_enhanced_data()
    
    def change_page_size(self, value):
        """Change the number of items per page"""
        self.items_per_page = int(value)
        self.current_page = 1
        self.selected_rows.clear()
        self.refresh_enhanced_data()
    
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
    
    def sort_enhanced_column(self, col):
        """Sort by column in enhanced mode"""
        reverse = getattr(self, f'_sort_{col}_reverse', False)
        self.all_data.sort(key=lambda x: str(x.get(col, '')), reverse=reverse)
        setattr(self, f'_sort_{col}_reverse', not reverse)
        self.refresh_enhanced_data()
    
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