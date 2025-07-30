import customtkinter as ctk
from config import COLORS

class ChannelDisplay(ctk.CTkFrame):
    def __init__(self, parent, channel_num, on_click=None):
        super().__init__(parent, corner_radius=10, fg_color=COLORS['card'], 
                         border_width=2, border_color=COLORS['primary'])
        self.channel_num = channel_num
        self.on_click = on_click
        self.configure(height=180)
        
        # Only make clickable if on_click is provided
        if self.on_click:
            self.configure(cursor="hand2")
            self.bind("<Button-1>", self.handle_click)

        # Title
        header = ctk.CTkLabel(self, text=f"OUT{channel_num:02d}", 
                              font=ctk.CTkFont(size=16, weight="bold"),
                              text_color=COLORS['primary'])
        header.pack(pady=(15, 10))
        if self.on_click:
            header.bind("<Button-1>", self.handle_click)

        # Value Label
        self.value_label = ctk.CTkLabel(self, text="---.--", 
                                        font=ctk.CTkFont(size=18, weight="bold"),
                                        text_color=COLORS['text'])
        self.value_label.pack(pady=(0, 2))
        if self.on_click:
            self.value_label.bind("<Button-1>", self.handle_click)

        self.unit_label = ctk.CTkLabel(self, text="μm", 
                                       font=ctk.CTkFont(size=12),
                                       text_color="gray70")
        self.unit_label.pack(pady=(0, 10))
        if self.on_click:
            self.unit_label.bind("<Button-1>", self.handle_click)

        # Judge Frame
        self.judge_frame = ctk.CTkFrame(self, corner_radius=8, height=30)
        self.judge_frame.pack(pady=(10, 15), padx=15, fill="x")
        self.judge_frame.pack_propagate(False)
        if self.on_click:
            self.judge_frame.bind("<Button-1>", self.handle_click)

        self.judge_label = ctk.CTkLabel(self.judge_frame, text="STANDBY", 
                                        font=ctk.CTkFont(size=12, weight="bold"))
        self.judge_label.pack(expand=True)
        if self.on_click:
            self.judge_label.bind("<Button-1>", self.handle_click)

    def handle_click(self, event):
        if self.on_click:
            self.on_click(self.channel_num)

    def update_data(self, value, judge):
        if value == -9999.98:
            self.value_label.configure(text="----.--")
        else:
            self.value_label.configure(text=f"{value:7.2f}")

        judge_colors = {
            "GO": (COLORS['success'], "gray10"),
            "HI": (COLORS['danger'], "white"), 
            "LO": (COLORS['danger'], "white"),
            "STANDBY": (COLORS['warning'], "white"),
            "??": ("gray50", "white")
        }

        text_color, bg_color = judge_colors.get(judge, ("gray50", "white"))
        self.judge_frame.configure(fg_color=text_color)
        self.judge_label.configure(text=judge, text_color=bg_color)

class ModernStatusCard(ctk.CTkFrame):
    def __init__(self, parent, title, value="--", icon="📊"):
        super().__init__(parent, corner_radius=16, fg_color=COLORS['card'], 
                         border_width=1, border_color=("gray40", "gray30"))
        self.configure(height=50, width=280)  # Reduced width slightly to fit better

        # Content container
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=12, pady=8)  # Reduced padding

        # Left side — Icon + Title
        left_frame = ctk.CTkFrame(content, fg_color="transparent")
        left_frame.pack(side="left")

        icon_label = ctk.CTkLabel(left_frame, text=icon, 
                                  font=ctk.CTkFont(size=14),  # Slightly smaller icon
                                  text_color=COLORS['primary'])
        icon_label.pack(side="left", padx=(0, 5))

        self.title_label = ctk.CTkLabel(left_frame, text=title, 
                                        font=ctk.CTkFont(size=12),  # Slightly smaller text
                                        text_color=("gray70", "gray60"))
        self.title_label.pack(side="left")

        # Middle separator — THIN GREEN BAR
        separator = ctk.CTkFrame(content, width=2, height=20, fg_color=COLORS['primary'])
        separator.pack(side="left", padx=8, pady=4)  # Reduced padding

        # Right side — Value
        self.value_label = ctk.CTkLabel(content, text=value, 
                                        font=ctk.CTkFont(size=13, weight="bold"),  # Slightly smaller
                                        text_color=COLORS['text'])
        self.value_label.pack(side="left")

    def update_value(self, value, color=None):
        self.value_label.configure(text=value)
        if color:
            self.value_label.configure(text_color=color)