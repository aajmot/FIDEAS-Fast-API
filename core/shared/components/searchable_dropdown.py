import customtkinter as ctk
import tkinter as tk
from typing import Dict, List, Callable, Optional

class SearchableDropdown(ctk.CTkFrame):
    def __init__(self, parent, values: List[str] = None, command: Callable = None, 
                 width: int = 200, height: int = 28, placeholder_text: str = "Search...", 
                 allow_add_new: bool = False, **kwargs):
        super().__init__(parent, width=width, height=height, **kwargs)
        
        self.values = values or []
        self.filtered_values = self.values[:10]  # Show first 10 by default
        self.command = command
        self.selected_value = ""
        self.dropdown_open = False
        self.allow_add_new = allow_add_new
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Entry widget for typing/searching
        self.entry = ctk.CTkEntry(
            self, 
            placeholder_text=placeholder_text,
            width=width-30,
            height=height
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(2, 0), pady=2)
        
        # Dropdown button
        self.dropdown_btn = ctk.CTkButton(
            self,
            text="▼",
            width=25,
            height=height-4,
            command=self.toggle_dropdown,
            font=ctk.CTkFont(size=12)
        )
        self.dropdown_btn.grid(row=0, column=1, padx=(2, 2), pady=2)
        
        # Dropdown listbox (initially hidden)
        self.dropdown_frame = None
        
        # Bind events
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self.entry.bind("<FocusIn>", self.on_focus_in)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.bind("<FocusOut>", self.on_focus_out)
    
    def configure_values(self, values: List[str]):
        """Update the dropdown values"""
        self.values = values
        self.filtered_values = values[:10]  # Show first 10 by default
        if self.dropdown_open:
            self.update_dropdown()
    
    def on_key_release(self, event):
        """Filter values based on typed text"""
        search_text = self.entry.get().lower()
        
        if not search_text:
            self.filtered_values = self.values[:10]  # Show first 10 by default
        else:
            self.filtered_values = [v for v in self.values if search_text in v.lower()][:20]  # Limit search results
        
        if self.dropdown_open:
            self.update_dropdown()
        elif self.filtered_values:
            self.show_dropdown()
    
    def on_focus_in(self, event):
        """Show dropdown when entry gets focus"""
        if not self.dropdown_open:
            # Reset to first 10 if no search text
            if not self.entry.get().strip():
                self.filtered_values = self.values[:10]
            self.show_dropdown()
    
    def on_enter(self, event):
        """Handle Enter key press"""
        if self.filtered_values:
            self.select_value(self.filtered_values[0])
        elif self.allow_add_new and self.entry.get().strip():
            # Handle Add New
            new_value = self.entry.get().strip()
            self.hide_dropdown()
            if self.command:
                self.command(new_value)
        else:
            self.hide_dropdown()
    
    def toggle_dropdown(self):
        """Toggle dropdown visibility"""
        if self.dropdown_open:
            self.hide_dropdown()
        else:
            self.show_dropdown()
    
    def show_dropdown(self):
        """Show the dropdown list"""
        if not self.filtered_values or self.dropdown_open:
            return
        
        self.dropdown_open = True
        self.dropdown_btn.configure(text="▲")
        
        # Create toplevel window for dropdown
        self.dropdown_window = ctk.CTkToplevel(self)
        self.dropdown_window.wm_overrideredirect(True)
        self.dropdown_window.configure(fg_color="white")
        
        # Position below the entry
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        width = self.winfo_width()
        height = min(200, len(self.filtered_values) * 30 + 20)
        
        self.dropdown_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create scrollable frame inside toplevel
        self.dropdown_frame = ctk.CTkScrollableFrame(self.dropdown_window)
        self.dropdown_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Add items to dropdown
        self.update_dropdown()
        
        # Auto-hide after 10 seconds
        self.after(10000, self.hide_dropdown)
    
    def update_dropdown(self):
        """Update dropdown content"""
        if not self.dropdown_frame:
            return
        
        # Clear existing items
        for widget in self.dropdown_frame.winfo_children():
            widget.destroy()
        
        # Add filtered items
        for value in self.filtered_values:
            item_btn = ctk.CTkButton(
                self.dropdown_frame,
                text=value,
                height=25,
                anchor="w",
                command=lambda v=value: self.select_value(v),
                font=ctk.CTkFont(size=11)
            )
            item_btn.pack(fill="x", padx=2, pady=1)
        
        # Add "Add New" option if enabled and no matches found
        if self.allow_add_new and not self.filtered_values and self.entry.get().strip():
            add_new_btn = ctk.CTkButton(
                self.dropdown_frame,
                text=f"+ Add New: {self.entry.get().strip()}",
                height=25,
                anchor="w",
                command=self.handle_add_new,
                font=ctk.CTkFont(size=11),
                fg_color="#1f538d"
            )
            add_new_btn.pack(fill="x", padx=2, pady=1)
    
    def hide_dropdown(self):
        """Hide the dropdown list"""
        if not self.dropdown_open:
            return
        
        self.dropdown_open = False
        self.dropdown_btn.configure(text="▼")
        
        if hasattr(self, 'dropdown_window') and self.dropdown_window:
            try:
                self.dropdown_window.destroy()
            except:
                pass
            self.dropdown_window = None
        
        self.dropdown_frame = None
    
    def select_value(self, value: str):
        """Select a value from dropdown"""
        self.selected_value = value
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        
        # Force close dropdown immediately
        self.dropdown_open = False
        self.dropdown_btn.configure(text="▼")
        
        if hasattr(self, 'dropdown_window') and self.dropdown_window:
            try:
                self.dropdown_window.withdraw()
                self.dropdown_window.destroy()
            except:
                pass
            self.dropdown_window = None
        
        self.dropdown_frame = None
        
        # Call command after cleanup
        if self.command:
            self.after(1, lambda: self.command(value))
    
    def get(self) -> str:
        """Get current value"""
        return self.entry.get()
    
    def set(self, value: str):
        """Set current value"""
        self.selected_value = value
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
    
    def clear(self):
        """Clear current value"""
        self.selected_value = ""
        self.entry.delete(0, tk.END)
        self.hide_dropdown()
    
    def check_focus(self):
        """Check if focus is still within our widgets"""
        if self.dropdown_open:
            focused = self.focus_get()
            if (focused != self.entry and 
                focused != self.dropdown_btn and
                not self.is_dropdown_child(focused)):
                self.hide_dropdown()
    
    def is_dropdown_child(self, widget):
        """Check if widget is child of dropdown"""
        if not hasattr(self, 'dropdown_window') or not self.dropdown_window or not widget:
            return False
        parent = widget
        while parent:
            if parent == self.dropdown_window or parent == self.dropdown_frame:
                return True
            try:
                parent = parent.master
            except:
                break
        return False
    
    def on_focus_out(self, event):
        """Handle focus out event"""
        # Delay hiding dropdown to allow for clicks on dropdown items
        self.after(150, self.check_focus)
    
    def handle_add_new(self):
        """Handle Add New selection"""
        new_value = self.entry.get().strip()
        if new_value and self.command:
            self.hide_dropdown()
            self.command(new_value)