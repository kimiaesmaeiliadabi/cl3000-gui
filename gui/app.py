import customtkinter as ctk
from datetime import datetime
from config import COLORS
from ui_components import ChannelDisplay, ModernStatusCard
from graph_widget import LiveGraphWidget
from data_manager import GraphDataManager
from logger import CL3000Logger

class CL3000App(ctk.CTk):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.logger.set_callbacks(self.update_display, self._on_logging_stop)
        self.title("Schaeffler CL-3000 Data Logger")
        self.geometry("1600x1000")
        self.configure(padx=20, pady=20)
        
        self.current_filename = None
        self.channel_displays = []
        self.out_channels = 6
        self.graph_data_manager = GraphDataManager()
        self.current_graph_widget = None
        self.viewing_graph = False
        self.logging_start_time = None  # Add this line
        
        self.setup_ui()     

    def setup_ui(self):
        # Header Frame
        header_frame = ctk.CTkFrame(self, corner_radius=15, height=80, fg_color=COLORS['primary'])
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(header_frame, text="SCHAEFFLER CL-3000 DATA LOGGER", 
                                  font=ctk.CTkFont(size=28, weight="bold"),
                                  text_color="white")
        title_label.pack(expand=True)

        # Main Content Area
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Left Side (Control Panel)
        left_frame = ctk.CTkFrame(self.content_frame, corner_radius=15, fg_color=COLORS['card'], width=400)
        left_frame.pack(side="left", fill="y", padx=(0, 20))
        left_frame.pack_propagate(False)

        control_title = ctk.CTkLabel(left_frame, text="⚙️ Control Panel", 
                                    font=ctk.CTkFont(size=18, weight="bold"),
                                    text_color=COLORS['primary'])
        control_title.pack(pady=(20, 15))

        input_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=25, pady=(0, 20))

        # Stack inputs vertically
        interval_container = ctk.CTkFrame(input_frame, fg_color="transparent")
        interval_container.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(interval_container, text="📊 Sample Rate (s)", 
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=COLORS['text']).pack(anchor="w")
        self.interval_entry = ctk.CTkEntry(interval_container, placeholder_text="E.g., 5", 
                                          height=40, font=ctk.CTkFont(size=15))
        self.interval_entry.pack(fill="x", pady=(6, 0))

        duration_container = ctk.CTkFrame(input_frame, fg_color="transparent")
        duration_container.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(duration_container, text="⏱️ Duration (s)", 
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=COLORS['text']).pack(anchor="w")
        self.duration_entry = ctk.CTkEntry(duration_container, placeholder_text="Leave blank for continuous", 
                                          height=40, font=ctk.CTkFont(size=15))
        self.duration_entry.pack(fill="x", pady=(6, 0))

        channels_container = ctk.CTkFrame(input_frame, fg_color="transparent")
        channels_container.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(channels_container, text="🔢 Output Channels", 
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=COLORS['text']).pack(anchor="w")
        self.channels_dropdown = ctk.CTkOptionMenu(channels_container, 
                                                 values=[str(i) for i in range(1, 9)],
                                                 command=self.update_channel_count,
                                                 height=40, font=ctk.CTkFont(size=15),
                                                 fg_color=COLORS['accent'],
                                                 button_color=COLORS['primary'],
                                                 button_hover_color=COLORS['success'])
        self.channels_dropdown.set("6")
        self.channels_dropdown.pack(fill="x", pady=(6, 0))

        # Buttons
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(pady=(15, 0))
        self.start_button = ctk.CTkButton(button_frame, text="▶ START LOGGING", 
                                         command=self.start_logging,
                                         height=45,
                                         font=ctk.CTkFont(size=15, weight="bold"),
                                         fg_color=COLORS['success'],
                                         hover_color=COLORS['primary'],
                                         text_color="white")
        self.start_button.pack(fill="x", pady=(0, 10))
        self.stop_button = ctk.CTkButton(button_frame, text="  ⏹ STOP LOGGING  ", 
                                        command=self.stop_logging,
                                        height=45,
                                        font=ctk.CTkFont(size=15, weight="bold"),
                                        fg_color=COLORS['danger'],
                                        hover_color="#D32F2F",
                                        text_color="white",
                                        state="disabled")
        self.stop_button.pack(fill="x")

        # Right Side (Live Channel Data or Graph)
        self.right_frame = ctk.CTkFrame(self.content_frame, corner_radius=15, fg_color=COLORS['dark'])
        self.right_frame.pack(side="right", fill="both", expand=True)

        # Initialize with channel grid view
        self.setup_channel_grid()

        # Bottom Status Bar (Horizontal)
        status_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=("gray10", "gray5"), height=100)
        status_frame.pack(fill="x", pady=(0, 0))
        status_frame.pack_propagate(False)

        status_title = ctk.CTkLabel(status_frame, text="📈 Live Status", 
                                   font=ctk.CTkFont(size=16, weight="bold"),
                                   text_color=COLORS['primary'])
        status_title.pack(pady=(12, 8))

        # Horizontal status cards container - centered
        status_cards_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_cards_frame.pack(expand=True, pady=(0, 12))

        self.status_card = ModernStatusCard(status_cards_frame, "System Status", "🟡 Idle", "🔧")
        self.status_card.pack(side="left", padx=10)

        self.samples_card = ModernStatusCard(status_cards_frame, "Data Points", "0", "📊")
        self.samples_card.pack(side="left", padx=10)

        self.runtime_card = ModernStatusCard(status_cards_frame, "Elapsed Time", "00:00:00", "⏱️")
        self.runtime_card.pack(side="left", padx=10)

    def setup_channel_grid(self):
        # Clear existing content
        for widget in self.right_frame.winfo_children():
            widget.destroy()
            
        data_title = ctk.CTkLabel(self.right_frame, text="🔴 Live Channel Data", 
                                 font=ctk.CTkFont(size=18, weight="bold"),
                                 text_color=COLORS['primary'])
        data_title.pack(pady=(20, 15))

        # Channels container
        self.channels_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.channels_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        self.update_channel_displays()

    def update_channel_displays(self):
        for display in self.channel_displays:
            display.destroy()
        self.channel_displays.clear()
        
        rows = (self.out_channels + 3) // 4
        for i in range(self.out_channels):
            display = ChannelDisplay(self.channels_container, i + 1, self.show_channel_graph)
            display.grid(row=i // 4, column=i % 4, padx=15, pady=15, sticky="nsew")
            self.channel_displays.append(display)
        
        for i in range(rows):
            self.channels_container.grid_rowconfigure(i, weight=1, minsize=180)
        for i in range(4):
            self.channels_container.grid_columnconfigure(i, weight=1)

    def show_channel_graph(self, channel_num):
        """Switch to graph view for the specified channel"""
        print(f"Switching to graph view for channel {channel_num}")  # Debug
        
        # Clear existing content
        for widget in self.right_frame.winfo_children():
            widget.destroy()
            
        # Create graph widget
        self.current_graph_widget = LiveGraphWidget(self.right_frame, channel_num, self.graph_data_manager, self)
        
        # Set start time if logging is active
        if hasattr(self, 'logging_start_time') and self.logging_start_time:
            self.current_graph_widget.set_start_time(self.logging_start_time)
        
        self.current_graph_widget.pack(fill="both", expand=True)
        
        self.current_graph_widget.update_graph()

        self.viewing_graph = True
        self.current_channel = channel_num
        
        print(f"Graph view active for channel {channel_num}")  # Debug
        
    def show_channel_grid(self):
        """Switch back to channel grid view"""
        print("Switching back to grid view")  # Debug
        self.viewing_graph = False
        self.current_graph_widget = None
        self.setup_channel_grid()

    def update_channel_count(self, value):
        self.out_channels = int(value)
        if not self.viewing_graph:
            self.update_channel_displays()
        
        # Initialize graph data for all channels
        for i in range(1, self.out_channels + 1):
            self.graph_data_manager.add_channel(i)
            
        # Update logger's channel count, if needed
        self.logger.out_channels = self.out_channels

    def set_status(self, msg, color=COLORS['text']):
        self.status_card.update_value(msg, color)

    def enable_start_button(self):
        self.start_button.configure(state="normal", fg_color=COLORS['success'], hover_color=COLORS['primary'])
        self.stop_button.configure(state="disabled")

    def format_runtime(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def update_display(self, row, timestamp, samples, runtime):
        print(f"Update display called - viewing_graph: {self.viewing_graph}")  # Debug
        
        self.samples_card.update_value(f"{samples:,}")
        self.runtime_card.update_value(self.format_runtime(runtime))
        
        # Always store data for graphs first
        for i in range(self.out_channels):
            channel_num = i + 1
            value = row[1 + i * 2]
            judge = row[2 + i * 2]
            
            # Add data to graph manager
            self.graph_data_manager.add_data_point(channel_num, timestamp, value, judge)
        
        # Update channel displays if in grid view
        if not self.viewing_graph and hasattr(self, 'channel_displays'):
            print("Updating channel displays")  # Debug
            for i, display in enumerate(self.channel_displays):
                if i < len(self.channel_displays):
                    value = row[1 + i * 2]
                    judge = row[2 + i * 2]
                    display.update_data(value, judge)
        
        # Update current graph if viewing one
        elif self.viewing_graph and hasattr(self, 'current_channel') and self.current_graph_widget:
            print(f"Updating graph for channel {self.current_channel}")  # Debug
            channel_index = self.current_channel - 1
            if channel_index < self.out_channels:
                value = row[1 + channel_index * 2]
                judge = row[2 + channel_index * 2]
                print(f"Graph update - value: {value}, judge: {judge}")  # Debug
                try:
                    self.current_graph_widget.update_graph(value, judge)
                except Exception as e:
                    print(f"Error updating graph: {e}")  # Debug

    def start_logging(self):
        try:
            interval = float(self.interval_entry.get())
            duration = self.duration_entry.get()
            duration = float(duration) if duration else None
        except ValueError:
            self.set_status("Invalid Input", COLORS['danger'])
            return

        if self.logger.connect() != 0:
            self.set_status("Connection Failed", COLORS['danger'])
            return

        # Clear existing graph data
        self.graph_data_manager.clear_all()
        
        # Record logging start time
        self.logging_start_time = datetime.now()
        
        filename = self.logger.start(interval, duration)
        self.current_filename = filename
        
        self.set_status("🟢 Logging Active", COLORS['success'])
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def stop_logging(self):
        self.logger.stop()
        self.samples_card.update_value("0")
        self.runtime_card.update_value("00:00:00")
        
        # Clear logging start time
        self.logging_start_time = None
        
        # Reset channel displays if in grid view
        if not self.viewing_graph and hasattr(self, 'channel_displays'):
            for display in self.channel_displays:
                display.update_data(-9999.98, "STANDBY")

    def _on_logging_stop(self):
        self.set_status("Stopped", COLORS['warning'])
        self.enable_start_button()
