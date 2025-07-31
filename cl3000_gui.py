import customtkinter as ctk

# ===== Setup CTK Style =====
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

from gui.app import CL3000App
from logger import CL3000Logger

if __name__ == "__main__":
    logger = CL3000Logger(6)  # Default to 6 channels
    app = CL3000App(logger)
    
    # Set up proper closing handler
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    app.mainloop()
