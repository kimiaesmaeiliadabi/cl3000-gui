import customtkinter as ctk
from datetime import datetime
from config import COLORS
from ui_components import ChannelDisplay, ModernStatusCard
from graph_widget import MultiChannelGraphWidget
from data_manager import GraphDataManager, LiveDataManager
from logger import CL3000Logger
from tkinter import BooleanVar
import CL3wrap
from zeroing_page import ZeroingPage

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
        self.live_data_manager = LiveDataManager(num_channels=self.out_channels)
        self.current_graph_widget = None
        self.viewing_graph = False
        self.logging_start_time = None
        
        # Set up live data manager callbacks
        self.live_data_manager.set_callbacks(
            data_update_callback=self._on_live_data_update,
            connection_change_callback=self._on_connection_change
        )
        
        self.setup_ui()
        
        # Start live data reading immediately
        self.live_data_manager.start_live_reading()

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
        self.content_frame.pack(fill="both", expand=True)

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
        
        # Create a horizontal frame for the buttons
        button_row = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_row.pack(fill="x")
        
        self.start_button = ctk.CTkButton(button_row, text="▶ START LOGGING", 
                                         command=self.start_logging,
                                         height=45,
                                         font=ctk.CTkFont(size=15, weight="bold"),
                                         fg_color=COLORS['success'],
                                         hover_color=COLORS['primary'],
                                         text_color="white")
        self.start_button.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.stop_button = ctk.CTkButton(button_row, text="⏹ STOP LOGGING", 
                                        command=self.stop_logging,
                                        height=45,
                                        font=ctk.CTkFont(size=15, weight="bold"),
                                        fg_color=COLORS['danger'],
                                        hover_color="#D32F2F",
                                        text_color="white",
                                        state="disabled")
        self.stop_button.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Add some spacing before status cards
        ctk.CTkLabel(input_frame, text="", height=15).pack()

        # Status cards directly in the control panel - make them more compact
        status_cards_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        status_cards_frame.pack(fill="x", pady=(5, 0))

        self.status_card = ModernStatusCard(status_cards_frame, "Logging Status", "🟡 IDLE", "📝")
        self.status_card.pack(pady=3)

        self.connection_card = ModernStatusCard(status_cards_frame, "Device Status", "🔴 Disconnected", "🔌")
        self.connection_card.pack(pady=3)

        self.samples_card = ModernStatusCard(status_cards_frame, "Data Points", "0", "📊")
        self.samples_card.pack(pady=3)

        self.runtime_card = ModernStatusCard(status_cards_frame, "Elapsed Time", "00:00:00", "⏱️")
        self.runtime_card.pack(pady=3)

        # Right Side (Live Channel Data or Graph) - Changed from COLORS['dark'] to transparent
        self.right_frame = ctk.CTkFrame(self.content_frame, corner_radius=15, fg_color="transparent")
        self.right_frame.pack(side="right", fill="both", expand=True)

        # Initialize with channel grid view
        self.setup_channel_grid()

    def setup_channel_grid(self):
        # Clear existing content
        for widget in self.right_frame.winfo_children():
            widget.destroy()
            
        # Create a container with card background for the grid view only
        grid_container = ctk.CTkFrame(self.right_frame, corner_radius=15, fg_color=COLORS['card'])
        grid_container.pack(fill="both", expand=True)
            
        data_title = ctk.CTkLabel(grid_container, text="🔴 Live Channel Data", 
                                 font=ctk.CTkFont(size=18, weight="bold"),
                                 text_color=COLORS['primary'])
        data_title.pack(pady=(20, 15))

        # Horizontal button container
        button_row = ctk.CTkFrame(grid_container, fg_color="transparent")
        button_row.pack(pady=(0, 20))

        # View Graph Button
        graph_button = ctk.CTkButton(button_row, text="📊 View Multi-Channel Graph", 
                                    command=self.show_multi_channel_graph,
                                    height=45,
                                    font=ctk.CTkFont(size=16, weight="bold"),
                                    fg_color=COLORS['primary'],
                                    hover_color=COLORS['success'],
                                    text_color="white")
        graph_button.pack(side="left", padx=10)

        # Zero Channels Button
        zeroing_btn = ctk.CTkButton(button_row, text="⚙️ Zero Channels", 
                                    command=self.show_zeroing_page,
                                    height=45,
                                    font=ctk.CTkFont(size=16, weight="bold"),
                                    fg_color=COLORS['warning'],
                                    hover_color=COLORS['accent'],
                                    text_color="black")
        zeroing_btn.pack(side="left", padx=10)

        # Channels container
        self.channels_container = ctk.CTkFrame(grid_container, fg_color="transparent")
        self.channels_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        self.update_channel_displays()

    def update_channel_displays(self):
        for display in self.channel_displays:
            display.destroy()
        self.channel_displays.clear()
        
        rows = (self.out_channels + 3) // 4
        for i in range(self.out_channels):
            # Pass None instead of click handler to disable clicking
            display = ChannelDisplay(self.channels_container, i + 1, on_click=None)
            display.grid(row=i // 4, column=i % 4, padx=15, pady=15, sticky="nsew")
            # Initialize with IDLE status
            display.update_data(-9999.98, "IDLE")
            self.channel_displays.append(display)
        
        for i in range(rows):
            self.channels_container.grid_rowconfigure(i, weight=1, minsize=180)
        for i in range(4):
            self.channels_container.grid_columnconfigure(i, weight=1)

    def show_multi_channel_graph(self):
        """Switch to multi-channel graph view"""
        print("Switching to multi-channel graph view")
        
        # Clear existing content
        for widget in self.right_frame.winfo_children():
            widget.destroy()
            
        # Create multi-channel graph widget directly in right_frame (no dark background)
        self.current_graph_widget = MultiChannelGraphWidget(
            self.right_frame, 
            self.out_channels, 
            self.graph_data_manager, 
            self,
            live_data_manager=self.live_data_manager
        )
        
        # Set start time if logging is active
        if hasattr(self, 'logging_start_time') and self.logging_start_time:
            self.current_graph_widget.set_start_time(self.logging_start_time)
        
        self.current_graph_widget.pack(fill="both", expand=True)
        
        self.current_graph_widget.update_graph()

        self.viewing_graph = True
        
        print("Multi-channel graph view active")
        
    def show_channel_grid(self):
        """Switch back to channel grid view"""
        print("Switching back to grid view")
        self.viewing_graph = False
        self.current_graph_widget = None
        self.setup_channel_grid()

    def show_zeroing_page(self):
        """Switch to zeroing page view"""
        print("Switching to zeroing page")

        # Clear right side
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        try:
            # Create and pack zeroing page - pass the existing logger instance and channel count
            from config import DEVICE_ID
            zero_page = ZeroingPage(self.right_frame, DEVICE_ID, go_back_callback=self.show_channel_grid, 
                                   logger=self.logger, num_channels=self.out_channels)
            zero_page.pack(fill="both", expand=True)
            print("Zeroing page created and packed successfully")
        except Exception as e:
            print(f"Error creating zeroing page: {e}")
            # Fallback: show error message
            error_label = ctk.CTkLabel(self.right_frame, text=f"Error loading zeroing page: {str(e)}", 
                                     text_color=COLORS['danger'])
            error_label.pack(expand=True)

    def update_channel_count(self, value):
        self.out_channels = int(value)
        
        # Update live data manager
        self.live_data_manager.update_channel_count(self.out_channels)
        
        if not self.viewing_graph:
            self.update_channel_displays()
        elif self.current_graph_widget:
            # Update the graph widget with new channel count
            self.current_graph_widget.update_channel_count(self.out_channels)
        
        # Initialize graph data for all channels
        for i in range(1, self.out_channels + 1):
            self.graph_data_manager.add_channel(i)
            
        # Update logger's channel count, if needed
        self.logger.out_channels = self.out_channels

    def _on_live_data_update(self, data):
        """Callback for live data updates"""
        # Update channel displays if in grid view
        if not self.viewing_graph and hasattr(self, 'channel_displays'):
            for i, display in enumerate(self.channel_displays):
                if i < len(self.channel_displays):
                    channel_num = i + 1
                    if channel_num in data:
                        value = data[channel_num]['value']
                        judge = data[channel_num]['judge']
                        display.update_data(value, judge)
                    else:
                        # Show IDLE when no data available (disconnected)
                        display.update_data(-9999.98, "IDLE")
        
        # Update multi-channel graph if viewing it
        elif self.viewing_graph and self.current_graph_widget:
            try:
                self.current_graph_widget.update_graph()
            except Exception as e:
                print(f"Error updating graph: {e}")

    def _on_connection_change(self, connected):
        """Callback for connection status changes"""
        if connected:
            self.connection_card.update_value("🟢 Connected", COLORS['success'])
        else:
            self.connection_card.update_value("🔴 Disconnected", COLORS['danger'])
            # Set all channel displays to IDLE when disconnected
            if hasattr(self, 'channel_displays'):
                for display in self.channel_displays:
                    display.update_data(-9999.98, "IDLE")

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
        print(f"Update display called - viewing_graph: {self.viewing_graph}")
        
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
            print("Updating channel displays")
            for i, display in enumerate(self.channel_displays):
                if i < len(self.channel_displays):
                    value = row[1 + i * 2]
                    judge = row[2 + i * 2]
                    display.update_data(value, judge)
        
        # Update multi-channel graph if viewing it
        elif self.viewing_graph and self.current_graph_widget:
            print("Updating multi-channel graph")
            try:
                self.current_graph_widget.update_graph()
            except Exception as e:
                print(f"Error updating graph: {e}")

    def start_logging(self):
        try:
            interval = float(self.interval_entry.get())
            duration = self.duration_entry.get()
            duration = float(duration) if duration else None
        except ValueError:
            self.set_status("❌ Invalid Input", COLORS['danger'])
            return

        if self.logger.connect() != 0:
            self.set_status("❌ Connection Failed", COLORS['danger'])
            return

        # Clear existing graph data
        self.graph_data_manager.clear_all()
        
        # Clear graph if viewing it
        if self.viewing_graph and self.current_graph_widget:
            self.current_graph_widget.clear_graph()
        
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
        
        # Reset button states properly
        self.set_status("🟡 Logging Stopped", COLORS['warning'])
        self.enable_start_button()

    def _on_logging_stop(self):
        self.set_status("🟡 Logging Stopped", COLORS['warning'])
        self.enable_start_button()
    
    def on_closing(self):
        """Handle application closing"""
        # Stop live data reading
        self.live_data_manager.stop_live_reading()
        
        # Close the application
        self.quit()