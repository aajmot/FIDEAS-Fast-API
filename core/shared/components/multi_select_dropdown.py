import tkinter as tk
from tkinter import ttk

class MultiSelectCombobox(ttk.Combobox):
    def __init__(self, parent, **kwargs):
        # Configure style to match CTkEntry
        style = ttk.Style()
        style.configure('MultiSelect.TCombobox',
                       fieldbackground='#343638',
                       background='#343638',
                       foreground='white',
                       borderwidth=1,
                       relief='solid',
                       arrowcolor='white')
        
        super().__init__(parent, state="readonly", style='MultiSelect.TCombobox', **kwargs)
        
        self.options = {}  # {id: name}
        self.selected_items = set()
        self.checkboxes = {}
        
        # Bind events
        self.bind('<Button-1>', self.on_click)
        self.bind('<KeyPress>', lambda e: 'break')  # Disable typing
        
        # Create dropdown window
        self.dropdown_window = None
        
        self.set('')
    
    def set_options(self, options):
        self.options = options
        self.update_display()
    
    def on_click(self, event):
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            self.close_dropdown()
        else:
            self.open_dropdown()
        return 'break'
    
    def open_dropdown(self):
        if self.dropdown_window:
            self.dropdown_window.destroy()
        
        # Create toplevel window
        self.dropdown_window = tk.Toplevel(self)
        self.dropdown_window.wm_overrideredirect(True)
        self.dropdown_window.configure(bg='white', relief='solid', bd=1)
        
        # Position below combobox
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.dropdown_window.geometry(f"200x150+{x}+{y}")
        
        # Create scrollable frame
        canvas = tk.Canvas(self.dropdown_window, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.dropdown_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add checkboxes
        self.checkboxes = {}
        for item_id, item_name in self.options.items():
            var = tk.BooleanVar()
            var.set(item_id in self.selected_items)
            
            checkbox = tk.Checkbutton(
                scrollable_frame,
                text=item_name,
                variable=var,
                bg='white',
                anchor='w',
                font=('Arial', 9),
                command=lambda id=item_id, v=var: self.on_checkbox_change(id, v)
            )
            checkbox.pack(fill='x', padx=5, pady=1)
            self.checkboxes[item_id] = var
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind click outside to close
        self.dropdown_window.bind('<FocusOut>', lambda e: self.close_dropdown())
        self.dropdown_window.focus_set()
        
        # Auto close after 10 seconds
        self.dropdown_window.after(10000, self.close_dropdown)
    
    def close_dropdown(self):
        if self.dropdown_window:
            self.dropdown_window.destroy()
            self.dropdown_window = None
    
    def on_checkbox_change(self, item_id, var):
        if var.get():
            self.selected_items.add(item_id)
        else:
            self.selected_items.discard(item_id)
        self.update_display()
    
    def update_display(self):
        if self.selected_items:
            count = len(self.selected_items)
            selected_names = [self.options[id] for id in self.selected_items if id in self.options]
            if len(selected_names) <= 2:
                text = ', '.join(selected_names)
            else:
                text = f"{count} items selected"
            self.set(text)
        else:
            self.set('Select items...')
    
    def get_selected(self):
        return self.selected_items
    
    def set_selected(self, selected_items):
        self.selected_items = set(selected_items)
        self.update_display()
    
    def clear_selection(self):
        self.selected_items.clear()
        self.update_display()