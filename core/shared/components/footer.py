import customtkinter as ctk

class Footer:
    @staticmethod
    def create(parent):
        """Create footer panel with copyright text"""
        footer_frame = ctk.CTkFrame(parent, height=30, corner_radius=0)
        footer_frame.pack(side="bottom", fill="x")
        footer_frame.pack_propagate(False)
        
        footer_label = ctk.CTkLabel(
            footer_frame,
            text="fideas@2025",
            font=ctk.CTkFont(size=11),
            text_color="gray50"
        )
        footer_label.pack(expand=True)
        
        return footer_frame