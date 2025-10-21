import customtkinter as ctk
import tkinter as tk
from datetime import datetime, date
import calendar

class ModernCalendar(ctk.CTkToplevel):
    def __init__(self, parent, callback, initial_date=None):
        super().__init__(parent)
        self.callback = callback
        self.current_date = initial_date or date.today()
        self.selected_date = None
        
        self.setup_window()
        self.setup_ui()
        self.update_calendar()
        
    def setup_window(self):
        self.title("Select Date")
        self.geometry("320x380")
        self.resizable(False, False)
        self.grab_set()
        self.transient(self.master)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
    def setup_ui(self):
        # Header with year and month navigation
        header_frame = ctk.CTkFrame(self, height=50)
        header_frame.pack(fill="x", padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        # Year navigation
        year_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        year_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(year_frame, text="<<", width=30, height=25, 
                     command=lambda: self.change_year(-1)).pack(side="left", padx=2)
        
        self.year_label = ctk.CTkLabel(year_frame, text=str(self.current_date.year), 
                                      font=ctk.CTkFont(size=16, weight="bold"))
        self.year_label.pack(side="left", expand=True)
        
        ctk.CTkButton(year_frame, text=">>", width=30, height=25,
                     command=lambda: self.change_year(1)).pack(side="right", padx=2)
        
        # Month navigation
        month_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        month_frame.pack(fill="x")
        
        ctk.CTkButton(month_frame, text="<", width=30, height=25,
                     command=lambda: self.change_month(-1)).pack(side="left", padx=2)
        
        self.month_label = ctk.CTkLabel(month_frame, 
                                       text=calendar.month_name[self.current_date.month],
                                       font=ctk.CTkFont(size=14, weight="bold"))
        self.month_label.pack(side="left", expand=True)
        
        ctk.CTkButton(month_frame, text=">", width=30, height=25,
                     command=lambda: self.change_month(1)).pack(side="right", padx=2)
        
        # Calendar grid
        self.calendar_frame = ctk.CTkFrame(self)
        self.calendar_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Day headers
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            label = ctk.CTkLabel(self.calendar_frame, text=day, 
                               font=ctk.CTkFont(size=12, weight="bold"))
            label.grid(row=0, column=i, padx=2, pady=5, sticky="nsew")
        
        # Configure grid weights
        for i in range(7):
            self.calendar_frame.grid_columnconfigure(i, weight=1)
        for i in range(7):
            self.calendar_frame.grid_rowconfigure(i, weight=1)
            
        # Action buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(button_frame, text="Today", width=80, height=30,
                     command=self.select_today).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="Cancel", width=80, height=30,
                     command=self.destroy).pack(side="right", padx=5)
        
    def change_year(self, delta):
        new_year = self.current_date.year + delta
        try:
            self.current_date = self.current_date.replace(year=new_year)
        except ValueError:
            # Handle leap year edge case
            self.current_date = date(new_year, self.current_date.month, 28)
        self.update_calendar()
        
    def change_month(self, delta):
        new_month = self.current_date.month + delta
        new_year = self.current_date.year
        
        if new_month > 12:
            new_month = 1
            new_year += 1
        elif new_month < 1:
            new_month = 12
            new_year -= 1
            
        try:
            self.current_date = self.current_date.replace(year=new_year, month=new_month)
        except ValueError:
            # Handle month with fewer days
            last_day = calendar.monthrange(new_year, new_month)[1]
            self.current_date = date(new_year, new_month, min(self.current_date.day, last_day))
        
        self.update_calendar()
        
    def update_calendar(self):
        # Update labels
        self.year_label.configure(text=str(self.current_date.year))
        self.month_label.configure(text=calendar.month_name[self.current_date.month])
        
        # Clear existing date buttons
        for widget in self.calendar_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.destroy()
                
        # Get calendar data
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        today = date.today()
        
        # Create date buttons
        for week_num, week in enumerate(cal, 1):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                    
                # Create date for this button
                button_date = date(self.current_date.year, self.current_date.month, day)
                
                # Determine button appearance
                is_today = button_date == today
                is_selected = button_date == self.selected_date
                
                if is_today:
                    fg_color = ("gray75", "gray25")
                    text_color = ("gray10", "gray90")
                elif is_selected:
                    fg_color = ("blue", "blue")
                    text_color = ("white", "white")
                else:
                    fg_color = ("gray90", "gray20")
                    text_color = ("gray10", "gray90")
                
                btn = ctk.CTkButton(
                    self.calendar_frame,
                    text=str(day),
                    width=35,
                    height=35,
                    fg_color=fg_color,
                    text_color=text_color,
                    font=ctk.CTkFont(size=12),
                    command=lambda d=day: self.select_date(d)
                )
                btn.grid(row=week_num, column=day_num, padx=2, pady=2, sticky="nsew")
                
    def select_date(self, day):
        selected = date(self.current_date.year, self.current_date.month, day)
        self.selected_date = selected
        self.callback(selected.strftime('%Y-%m-%d'))
        self.destroy()
        
    def select_today(self):
        today = date.today()
        self.callback(today.strftime('%Y-%m-%d'))
        self.destroy()