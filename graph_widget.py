import customtkinter as ctk
from config import COLORS
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

class MultiChannelGraphWidget(ctk.CTkFrame):
    def __init__(self, parent, max_channels, graph_data_manager, app_ref=None):
        super().__init__(parent, corner_radius=15, fg_color=COLORS['card'])
        self.max_channels = max_channels
        self.graph_data_manager = graph_data_manager
        self.start_time = None
        self.first_data_time = None
        self.app_ref = app_ref
        self.auto_update_enabled = True
        self.after_id = None
        self._update_in_progress = False  # Prevent concurrent updates
        
        # Channel colors (8 distinct colors)
        self.channel_colors = [
            '#00FF7F',  # Spring Green
            '#FF6B6B',  # Light Red
            '#4ECDC4',  # Teal
            '#FFE66D',  # Yellow
            '#A8E6CF',  # Light Green
            '#FF8B94',  # Pink
            '#B4A7D6',  # Light Purple
            '#FFD3A5'   # Light Orange
        ]
        
        # Track which channels are selected for display
        self.selected_channels = {i: True for i in range(1, max_channels + 1)}
        self.channel_checkboxes = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header with back button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        
        self.back_button = ctk.CTkButton(header_frame, text="← Back to Grid", 
                                        command=self.go_back,
                                        height=35, width=120,
                                        font=ctk.CTkFont(size=13, weight="bold"),
                                        fg_color=COLORS['secondary'],
                                        hover_color=COLORS['primary'])
        self.back_button.pack(side="left")
        
        title_label = ctk.CTkLabel(header_frame, text="Multi-Channel Live Data Graph", 
                                  font=ctk.CTkFont(size=18, weight="bold"),
                                  text_color=COLORS['primary'])
        title_label.pack(side="left", padx=(20, 0))
        
        # Auto-update toggle button
        self.auto_update_button = ctk.CTkButton(header_frame, text="🔄 Auto-Update ON", width=140, height=35,
                                               command=self.toggle_auto_update,
                                               font=ctk.CTkFont(size=12, weight="bold"),
                                               fg_color=COLORS['success'],
                                               hover_color=COLORS['primary'])
        self.auto_update_button.pack(side="right", padx=(0, 10))
        
        # Channel selection frame
        selection_frame = ctk.CTkFrame(self, fg_color="transparent")
        selection_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        selection_label = ctk.CTkLabel(selection_frame, text="Select Channels to Display:", 
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      text_color=COLORS['text'])
        selection_label.pack(side="left", padx=(0, 15))
        
        # Create checkboxes for each channel
        checkbox_frame = ctk.CTkFrame(selection_frame, fg_color="transparent")
        checkbox_frame.pack(side="left")
        
        for i in range(1, self.max_channels + 1):
            color = self.channel_colors[(i-1) % len(self.channel_colors)]
            # Fixed: Use a proper closure to capture the channel number
            def make_toggle_command(channel_num):
                return lambda: self.toggle_channel(channel_num)
            
            checkbox = ctk.CTkCheckBox(checkbox_frame, 
                                      text=f"OUT{i:02d}",
                                      command=make_toggle_command(i),
                                      font=ctk.CTkFont(size=12, weight="bold"),
                                      text_color=color,
                                      fg_color=color,
                                      hover_color=color,
                                      checkmark_color="white")
            checkbox.pack(side="left", padx=8)
            checkbox.select()  # All channels selected by default
            self.channel_checkboxes[i] = checkbox
        
        # Add Select All / Deselect All buttons
        button_frame = ctk.CTkFrame(selection_frame, fg_color="transparent")
        button_frame.pack(side="left", padx=(15, 0))
        
        select_all_btn = ctk.CTkButton(button_frame, text="Select All", width=80, height=25,
                                      command=self.select_all_channels,
                                      font=ctk.CTkFont(size=10),
                                      fg_color=COLORS['success'],
                                      hover_color=COLORS['primary'])
        select_all_btn.pack(side="top", pady=(0, 2))
        
        deselect_all_btn = ctk.CTkButton(button_frame, text="Deselect All", width=80, height=25,
                                        command=self.deselect_all_channels,
                                        font=ctk.CTkFont(size=10),
                                        fg_color=COLORS['danger'],
                                        hover_color="#D32F2F")
        deselect_all_btn.pack(side="top")
        
        # Control buttons frame
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Zoom controls
        zoom_label = ctk.CTkLabel(controls_frame, text="Controls:", 
                                 font=ctk.CTkFont(size=12, weight="bold"),
                                 text_color=COLORS['text'])
        zoom_label.pack(side="left", padx=(0, 10))
        
        self.zoom_in_button = ctk.CTkButton(controls_frame, text="🔍+", width=50, height=30,
                                           command=self.zoom_in,
                                           font=ctk.CTkFont(size=12),
                                           fg_color=COLORS['primary'],
                                           hover_color=COLORS['success'])
        self.zoom_in_button.pack(side="left", padx=2)
        
        self.zoom_out_button = ctk.CTkButton(controls_frame, text="🔍-", width=50, height=30,
                                            command=self.zoom_out,
                                            font=ctk.CTkFont(size=12),
                                            fg_color=COLORS['primary'],
                                            hover_color=COLORS['success'])
        self.zoom_out_button.pack(side="left", padx=2)
        
        self.auto_fit_button = ctk.CTkButton(controls_frame, text="Auto Fit", width=80, height=30,
                                            command=self.manual_auto_fit,
                                            font=ctk.CTkFont(size=12),
                                            fg_color=COLORS['accent'],
                                            hover_color=COLORS['primary'])
        self.auto_fit_button.pack(side="left", padx=5)
        
        # Clear graph button
        self.clear_button = ctk.CTkButton(controls_frame, text="Clear Graph", width=100, height=30,
                                         command=self.clear_graph,
                                         font=ctk.CTkFont(size=12),
                                         fg_color=COLORS['danger'],
                                         hover_color="#D32F2F")
        self.clear_button.pack(side="left", padx=5)
        
        # Instructions
        instructions = ctk.CTkLabel(controls_frame, text="💡 Drag=Pan | Wheel=Zoom | Select channels above", 
                                   font=ctk.CTkFont(size=10),
                                   text_color="gray60")
        instructions.pack(side="right", padx=10)
        
        # Create matplotlib figure with dark theme
        plt.style.use('dark_background')
        self.figure = Figure(figsize=(12, 6), dpi=100, facecolor='#2D2D2D')
        self.ax = self.figure.add_subplot(111, facecolor='#1A1A1A')
        
        # Configure plot appearance
        self.ax.set_xlabel('Time (s)', color=COLORS['text'], fontsize=12)
        self.ax.set_ylabel('Thickness (μm)', color=COLORS['text'], fontsize=12)
        self.ax.tick_params(colors=COLORS['text'])
        self.ax.grid(True, alpha=0.3, color='gray')
        self.ax.spines['bottom'].set_color(COLORS['text'])
        self.ax.spines['top'].set_color(COLORS['text'])
        self.ax.spines['right'].set_color(COLORS['text'])
        self.ax.spines['left'].set_color(COLORS['text'])
        
        # Initialize lines and scatter plots for each channel
        self.lines = {}
        self.go_points = {}
        self.hi_points = {}
        self.lo_points = {}
        
        for i in range(1, self.max_channels + 1):
            color = self.channel_colors[(i-1) % len(self.channel_colors)]
            line, = self.ax.plot([], [], color=color, linewidth=2, 
                               label=f'OUT{i:02d}', alpha=0.8)
            self.lines[i] = line
            
            # Create scatter plots for judge points (smaller and more transparent)
            self.go_points[i] = self.ax.scatter([], [], c=color, s=20, alpha=0.6, 
                                              marker='o', edgecolors='white', linewidth=0.5)
            self.hi_points[i] = self.ax.scatter([], [], c=color, s=25, alpha=0.8, 
                                              marker='^', edgecolors='red', linewidth=1)
            self.lo_points[i] = self.ax.scatter([], [], c=color, s=25, alpha=0.8, 
                                              marker='v', edgecolors='orange', linewidth=1)
        
        # Create legend
        self.update_legend()
        
        # Embed plot in tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Connect mouse events for zooming and panning
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_motion)
        self.canvas.mpl_connect('button_release_event', self.on_button_release)
        
        # Pan state
        self.is_panning = False
        self.pan_start = None
        self.pan_start_xlim = None
        self.pan_start_ylim = None
        
        # Initial setup
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 100)
        self.canvas.draw()
        
        # Start auto-update timer immediately
        self.start_auto_update()
    
    def select_all_channels(self):
        """Select all channel checkboxes"""
        print("Selecting all channels")
        for i in range(1, self.max_channels + 1):
            if i in self.channel_checkboxes:
                self.channel_checkboxes[i].select()
                self.selected_channels[i] = True
        self.update_legend()
        # Don't call update_graph here to avoid interfering with auto-update
        print("All channels selected")
    
    def deselect_all_channels(self):
        """Deselect all channel checkboxes"""
        print("Deselecting all channels")
        for i in range(1, self.max_channels + 1):
            if i in self.channel_checkboxes:
                self.channel_checkboxes[i].deselect()
                self.selected_channels[i] = False
        self.update_legend()
        # Don't call update_graph here to avoid interfering with auto-update
        print("All channels deselected")
    
    def update_channel_count(self, new_count):
        """Update the widget when channel count changes"""
        old_count = self.max_channels
        self.max_channels = new_count
        
        # Hide/show checkboxes based on new count
        for i in range(1, 9):  # Max 8 channels
            if i in self.channel_checkboxes:
                if i <= new_count:
                    self.channel_checkboxes[i].pack(side="left", padx=8)
                else:
                    self.channel_checkboxes[i].pack_forget()
        
        # Update selected channels dict
        for i in range(new_count + 1, old_count + 1):
            if i in self.selected_channels:
                del self.selected_channels[i]
        
        for i in range(1, new_count + 1):
            if i not in self.selected_channels:
                self.selected_channels[i] = True
        
        self.update_legend()
        print(f"Channel count updated to {new_count}")
        
    def toggle_channel(self, channel_num):
        """Toggle visibility of a specific channel"""
        print(f"DEBUG: toggle_channel called for channel {channel_num}")
        
        # Get the actual checkbox state and ensure it's properly synchronized
        if channel_num in self.channel_checkboxes:
            checkbox_state = self.channel_checkboxes[channel_num].get()
            self.selected_channels[channel_num] = bool(checkbox_state)
            print(f"Channel {channel_num} {'enabled' if self.selected_channels[channel_num] else 'disabled'} (checkbox state: {checkbox_state})")
        else:
            # Fallback: toggle the stored state
            self.selected_channels[channel_num] = not self.selected_channels[channel_num]
            print(f"Channel {channel_num} {'enabled' if self.selected_channels[channel_num] else 'disabled'} (fallback)")
        
        # Debug: Print current state of all channels
        print(f"Current selected channels: {[i for i in range(1, self.max_channels + 1) if self.selected_channels.get(i, False)]}")
        print(f"Current first_data_time: {self.first_data_time}")
        
        # Force recalculation of first_data_time when any channel is toggled
        # This ensures we don't depend on any specific channel
        self._recalculate_first_data_time()
        
        # Additional debugging for OUT1 specifically
        if channel_num == 1:
            print(f"OUT1 DEBUG: selected_channels[1] = {self.selected_channels.get(1, False)}")
            print(f"OUT1 DEBUG: checkbox state = {self.channel_checkboxes[1].get() if 1 in self.channel_checkboxes else 'N/A'}")
            print(f"OUT1 DEBUG: first_data_time after recalculation = {self.first_data_time}")
        
        self.update_legend()
        # Force an immediate graph update to show the change
        self.update_graph()
        print(f"Channel {channel_num} toggle complete")
    
    def _recalculate_first_data_time(self):
        """Recalculate first_data_time based on currently selected channels"""
        print("DEBUG: Recalculating first_data_time...")
        first_times = []
        
        for channel_num in range(1, self.max_channels + 1):
            if self.selected_channels.get(channel_num, False):
                timestamps, values, judges = self.graph_data_manager.get_channel_data(channel_num)
                valid_times = [t for t, v in zip(timestamps, values) if v is not None and v != -9999.98 and str(v).lower() != 'nan']
                if valid_times:
                    first_times.append(valid_times[0])
                    print(f"DEBUG: Channel {channel_num} contributes first time: {valid_times[0]}")
        
        if first_times:
            new_first_time = min(first_times)
            if self.first_data_time != new_first_time:
                print(f"DEBUG: Updating first_data_time from {self.first_data_time} to {new_first_time}")
                self.first_data_time = new_first_time
            else:
                print(f"DEBUG: first_data_time unchanged: {self.first_data_time}")
        else:
            print("DEBUG: No valid first times found, setting first_data_time to None")
            self.first_data_time = None
    
    def update_legend(self):
        """Update the legend to show only selected channels"""
        handles = []
        labels = []
        
        for i in range(1, self.max_channels + 1):
            if self.selected_channels.get(i, False):
                handles.append(self.lines[i])
                labels.append(f'OUT{i:02d}')
        
        if handles:
            self.ax.legend(handles, labels, loc='upper right', 
                          facecolor='#2D2D2D', edgecolor=COLORS['text'],
                          framealpha=0.9)
        else:
            legend = self.ax.legend()
            if legend:
                legend.set_visible(False)
        
    def toggle_auto_update(self):
        """Toggle auto-update mode"""
        self.auto_update_enabled = not self.auto_update_enabled
        if self.auto_update_enabled:
            self.auto_update_button.configure(text="🔄 Auto-Update ON", fg_color=COLORS['success'])
            self.start_auto_update()
            print("Auto-update ENABLED")
        else:
            self.auto_update_button.configure(text="⏸️ Auto-Update OFF", fg_color=COLORS['warning'])
            self.stop_auto_update()
            print("Auto-update DISABLED")
    
    def start_auto_update(self):
        """Start or restart the auto-update timer"""
        if not self.auto_update_enabled:
            return
            
        # Cancel existing timer if any
        self.stop_auto_update()
        
        # Start new timer
        self.after_id = self.after(500, self.update_graph_with_timer)
        print(f"Auto-update timer started with ID: {self.after_id}")
    
    def stop_auto_update(self):
        """Stop the auto-update timer"""
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
            print("Auto-update timer stopped")
    
    def update_graph_with_timer(self):
        """Update graph and schedule next update"""
        if not self.auto_update_enabled or self._update_in_progress:
            return
            
        try:
            self._update_in_progress = True
            self.update_graph()
        except Exception as e:
            print(f"Error in update_graph_with_timer: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._update_in_progress = False
        
        # Schedule next update if auto-update is still enabled
        if self.auto_update_enabled:
            self.after_id = self.after(500, self.update_graph_with_timer)
    
    def go_back(self):
        """Return to channel grid view"""
        # Don't stop auto-update timer - let it continue running
        # The timer should continue updating the graph even when not visible
        # This prevents interference with data logging
        
        if self.app_ref:
            self.app_ref.show_channel_grid()
    
    def set_start_time(self, start_time):
        """Set the logging start time"""
        self.start_time = start_time
        print(f"Start time set to: {start_time}")
    
    def clear_graph(self):
        """Clear all data from the graph"""
        print("Clearing graph data...")
        
        # Clear data manager if it has a clear method
        try:
            if hasattr(self.graph_data_manager, 'clear_all_data'):
                self.graph_data_manager.clear_all_data()
            elif hasattr(self.graph_data_manager, 'clear_data'):
                for i in range(1, self.max_channels + 1):
                    self.graph_data_manager.clear_data(i)
        except Exception as e:
            print(f"Error clearing data manager: {e}")
        
        # Reset first data time
        self.first_data_time = None
        
        # Clear all lines and scatter plots
        for i in range(1, self.max_channels + 1):
            self.lines[i].set_data([], [])
            self.go_points[i].set_offsets(np.empty((0, 2)))
            self.hi_points[i].set_offsets(np.empty((0, 2)))
            self.lo_points[i].set_offsets(np.empty((0, 2)))
        
        # Reset axis limits
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 100)
        self.canvas.draw()
        print("Graph cleared successfully")
        
    def manual_auto_fit(self):
        """Manual auto-fit triggered by button"""
        self.auto_fit()
        
    def auto_fit(self):
        """Auto-fit all visible data"""
        try:
            all_times = []
            all_values = []
            
            # First, recalculate first_data_time based on currently selected channels
            # (same logic as in update_graph)
            first_times = []
            for channel_num in range(1, self.max_channels + 1):
                if self.selected_channels.get(channel_num, False):
                    timestamps, values, judges = self.graph_data_manager.get_channel_data(channel_num)
                    valid_times = [t for t, v in zip(timestamps, values) if v is not None and v != -9999.98 and str(v).lower() != 'nan']
                    if valid_times:
                        first_times.append(valid_times[0])
            
            # Update first_data_time if we have valid selected channels
            if first_times:
                new_first_time = min(first_times)
                if self.first_data_time != new_first_time:
                    self.first_data_time = new_first_time
                    print(f"Auto_fit: Updated first_data_time to: {self.first_data_time}")
            
            # Collect data from all selected channels
            for channel_num in range(1, self.max_channels + 1):
                if not self.selected_channels.get(channel_num, False):
                    continue
                    
                timestamps, values, judges = self.graph_data_manager.get_channel_data(channel_num)
                if timestamps and values:
                    # Filter out invalid data points
                    valid_data = [(t, v) for t, v in zip(timestamps, values) if v != -9999.98 and v is not None]
                    if valid_data:
                        plot_times, plot_values = zip(*valid_data)
                        
                        # Use the same fallback logic as update_graph
                        reference_time = self.first_data_time
                        if reference_time is None:
                            # Fallback: use this channel's first timestamp
                            reference_time = plot_times[0]
                            print(f"Auto_fit: Channel {channel_num} using fallback reference time {reference_time}")
                        
                        try:
                            relative_times = [(t - reference_time).total_seconds() for t in plot_times]
                            # Handle negative times by adding offset
                            if relative_times and min(relative_times) < 0:
                                time_offset = abs(min(relative_times))
                                relative_times = [t + time_offset for t in relative_times]
                            
                            all_times.extend(relative_times)
                            all_values.extend(plot_values)
                        except Exception as e:
                            print(f"Error processing times for channel {channel_num}: {e}")
            
            if all_times and all_values:
                time_min, time_max = min(all_times), max(all_times)
                time_range = time_max - time_min
                time_padding = max(1.0, time_range * 0.1)  # Minimum 1 second padding
                
                y_min, y_max = min(all_values), max(all_values)
                y_range = y_max - y_min
                y_padding = 5.0 if y_range == 0 else y_range * 0.1  # Minimum 5 unit padding
                
                self.ax.set_xlim(max(0, time_min - time_padding), time_max + time_padding)
                self.ax.set_ylim(y_min - y_padding, y_max + y_padding)
                
                print(f"Auto fit: X({time_min:.1f} to {time_max:.1f}), Y({y_min:.1f} to {y_max:.1f})")
            else:
                print("No valid data for auto fit - using default ranges")
                self.ax.set_xlim(0, 10)
                self.ax.set_ylim(0, 100)
                
            self.canvas.draw()
                
        except Exception as e:
            print(f"Error in auto_fit: {e}")
            import traceback
            traceback.print_exc()
    
    def zoom_in(self):
        """Zoom in on both axes"""
        self.disable_auto_update()
        
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        
        x_range = (x_max - x_min) * 0.7 / 2
        y_range = (y_max - y_min) * 0.7 / 2
        
        new_x_min = max(0, x_center - x_range)
        new_x_max = x_center + x_range
        
        self.ax.set_xlim(new_x_min, new_x_max)
        self.ax.set_ylim(y_center - y_range, y_center + y_range)
        self.canvas.draw()
    
    def zoom_out(self):
        """Zoom out on both axes"""
        self.disable_auto_update()
        
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        
        x_range = (x_max - x_min) * 1.3 / 2
        y_range = (y_max - y_min) * 1.3 / 2
        
        new_x_min = max(0, x_center - x_range)
        new_x_max = x_center + x_range
        
        self.ax.set_xlim(new_x_min, new_x_max)
        self.ax.set_ylim(y_center - y_range, y_center + y_range)
        self.canvas.draw()
    
    def disable_auto_update(self):
        """Disable auto-update when user manually interacts"""
        if self.auto_update_enabled:
            self.auto_update_enabled = False
            self.auto_update_button.configure(text="⏸️ Auto-Update OFF", fg_color=COLORS['warning'])
            self.stop_auto_update()
            print("Auto-update disabled due to manual interaction")
    
    def on_scroll(self, event):
        """Handle mouse wheel scrolling for zoom"""
        if event.inaxes != self.ax:
            return
            
        self.disable_auto_update()
        
        zoom_factor = 1.15 if event.step > 0 else 1/1.15
        mouse_x, mouse_y = event.xdata, event.ydata
        if mouse_x is None or mouse_y is None:
            return
        
        # Zoom X-axis
        x_min, x_max = self.ax.get_xlim()
        x_range = x_max - x_min
        new_x_range = x_range * zoom_factor
        x_center_ratio = (mouse_x - x_min) / x_range if x_range > 0 else 0.5
        new_x_min = mouse_x - new_x_range * x_center_ratio
        new_x_max = mouse_x + new_x_range * (1 - x_center_ratio)
        
        if new_x_min < 0:
            new_x_max += abs(new_x_min)
            new_x_min = 0
        
        self.ax.set_xlim(new_x_min, new_x_max)
        
        # Zoom Y-axis
        y_min, y_max = self.ax.get_ylim()
        y_range = y_max - y_min
        new_y_range = y_range * zoom_factor
        y_center_ratio = (mouse_y - y_min) / y_range if y_range > 0 else 0.5
        new_y_min = mouse_y - new_y_range * y_center_ratio
        new_y_max = mouse_y + new_y_range * (1 - y_center_ratio)
        
        self.ax.set_ylim(new_y_min, new_y_max)
        self.canvas.draw()
    
    def on_button_press(self, event):
        """Handle mouse button press for panning"""
        if event.inaxes != self.ax or event.button != 1:
            return
            
        self.disable_auto_update()
        
        self.is_panning = True
        self.pan_start = (event.xdata, event.ydata)
        self.pan_start_xlim = self.ax.get_xlim()
        self.pan_start_ylim = self.ax.get_ylim()
        self.canvas.get_tk_widget().configure(cursor="fleur")
    
    def on_mouse_motion(self, event):
        """Handle mouse motion for panning"""
        if not self.is_panning or event.inaxes != self.ax:
            return
        if self.pan_start is None or event.xdata is None or event.ydata is None:
            return
        if self.pan_start_xlim is None or self.pan_start_ylim is None:
            return
        
        dx = self.pan_start[0] - event.xdata
        dy = self.pan_start[1] - event.ydata
        
        x_min, x_max = self.pan_start_xlim
        y_min, y_max = self.pan_start_ylim
        
        new_x_min = x_min + dx
        new_x_max = x_max + dx
        if new_x_min < 0:
            new_x_max += abs(new_x_min)
            new_x_min = 0
        
        self.ax.set_xlim(new_x_min, new_x_max)
        self.ax.set_ylim(y_min + dy, y_max + dy)
        self.canvas.draw()
    
    def on_button_release(self, event):
        """Handle mouse button release"""
        self.is_panning = False
        self.pan_start = None
        self.pan_start_xlim = None
        self.pan_start_ylim = None
        self.canvas.get_tk_widget().configure(cursor="")
    
    def update_graph(self):
        """Update the graph with new data from all channels"""
        if self._update_in_progress:  # Prevent concurrent updates
            return
            
        try:
            any_data_updated = False
            data_points_found = 0
            visible_channels = 0

            # Get list of selected channels for debugging
            selected_list = [i for i in range(1, self.max_channels + 1) if self.selected_channels.get(i, False)]
            print(f"DEBUG: update_graph - selected channels: {selected_list}")
            
            # Always recalculate first_data_time based on currently selected channels
            # This ensures we don't depend on OUT1 or any specific channel
            self._recalculate_first_data_time()

            for channel_num in range(1, self.max_channels + 1):
                if not self.selected_channels.get(channel_num, False):
                    # Hide channel if not selected - make sure it's completely hidden
                    self.lines[channel_num].set_data([], [])
                    self.go_points[channel_num].set_offsets(np.empty((0, 2)))
                    self.hi_points[channel_num].set_offsets(np.empty((0, 2)))
                    self.lo_points[channel_num].set_offsets(np.empty((0, 2)))
                    # Make sure the line is not visible
                    self.lines[channel_num].set_visible(False)
                    any_data_updated = True
                    print(f"DEBUG: Channel {channel_num} is not selected, hiding it")
                    
                    # Additional debugging for OUT1
                    if channel_num == 1:
                        print(f"OUT1 HIDE DEBUG: selected_channels[1] = {self.selected_channels.get(1, False)}")
                        print(f"OUT1 HIDE DEBUG: checkbox state = {self.channel_checkboxes[1].get() if 1 in self.channel_checkboxes else 'N/A'}")
                    
                    continue

                # Make sure the line is visible for selected channels
                self.lines[channel_num].set_visible(True)
                visible_channels += 1
                timestamps, values, judges = self.graph_data_manager.get_channel_data(channel_num)

                if not timestamps or not values:
                    print(f"DEBUG: Channel {channel_num} has no data")
                    continue

                # Filter valid data more carefully
                valid_data = []
                for t, v, j in zip(timestamps, values, judges):
                    if v is not None and v != -9999.98 and str(v).lower() != 'nan':
                        try:
                            float_val = float(v)
                            valid_data.append((t, float_val, j))
                        except (ValueError, TypeError):
                            continue

                if not valid_data:
                    print(f"DEBUG: Channel {channel_num} has no valid data")
                    continue

                plot_times, plot_values, plot_judges = zip(*valid_data)
                data_points_found += len(plot_values)
                print(f"DEBUG: Channel {channel_num} has {len(plot_values)} valid data points")

                # Use the global first_data_time that's based on selected channels
                # If first_data_time is None, use this channel's first timestamp as fallback
                reference_time = self.first_data_time
                if reference_time is None:
                    # Fallback: use this channel's first timestamp
                    reference_time = plot_times[0]
                    print(f"Channel {channel_num}: Using fallback reference time {reference_time}")

                # Convert to relative times
                try:
                    relative_times = [(t - reference_time).total_seconds() for t in plot_times]
                    if relative_times and min(relative_times) < 0:
                        time_offset = abs(min(relative_times))
                        relative_times = [t + time_offset for t in relative_times]
                    print(f"DEBUG: Channel {channel_num} calculated {len(relative_times)} relative times")
                except Exception as e:
                    print(f"Error calculating relative times for channel {channel_num}: {e}")
                    continue

                # Update main line with smoothing if enough points
                if len(relative_times) > 3:
                    try:
                        from scipy.interpolate import make_interp_spline
                        # Use global np import, not local
                        import numpy as np_local
                        xnew = np_local.linspace(min(relative_times), max(relative_times), 300)
                        spl = make_interp_spline(relative_times, plot_values, k=3)
                        y_smooth = spl(xnew)
                        self.lines[channel_num].set_data(xnew, y_smooth)
                    except:
                        # Fallback to non-smoothed if scipy is not available
                        self.lines[channel_num].set_data(relative_times, plot_values)
                else:
                    self.lines[channel_num].set_data(relative_times, plot_values)

                # Update judge markers
                try:
                    go_data = [(rt, v) for rt, v, j in zip(relative_times, plot_values, plot_judges) if j == "GO"]
                    hi_data = [(rt, v) for rt, v, j in zip(relative_times, plot_values, plot_judges) if j == "HI"]
                    lo_data = [(rt, v) for rt, v, j in zip(relative_times, plot_values, plot_judges) if j == "LO"]

                    self.go_points[channel_num].set_offsets(list(zip(*go_data)) if go_data else np.empty((0, 2)))
                    self.hi_points[channel_num].set_offsets(list(zip(*hi_data)) if hi_data else np.empty((0, 2)))
                    self.lo_points[channel_num].set_offsets(list(zip(*lo_data)) if lo_data else np.empty((0, 2)))
                except Exception as e:
                    print(f"Error updating judge markers for channel {channel_num}: {e}")

                any_data_updated = True

            # Always redraw the canvas when data is processed
            if any_data_updated:
                if self.auto_update_enabled and visible_channels > 0 and data_points_found > 0:
                    self.auto_fit()
                else:
                    self.canvas.draw()

            # Print status only occasionally to reduce console spam
            if visible_channels > 0 and data_points_found > 0:
                print(f"Graph updated: {data_points_found} points across {visible_channels} channels (selected: {selected_list})")

        except Exception as e:
            print(f"Error in update_graph: {e}")
            import traceback
            traceback.print_exc()


# Keep the original single-channel widget for backward compatibility
class LiveGraphWidget(ctk.CTkFrame):
    def __init__(self, parent, channel_num, graph_data_manager, app_ref=None):
        super().__init__(parent, corner_radius=15, fg_color=COLORS['card'])
        self.channel_num = channel_num
        self.graph_data_manager = graph_data_manager
        self.start_time = None
        self.first_data_time = None
        self.app_ref = app_ref
        
        # Header with back button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        
        self.back_button = ctk.CTkButton(header_frame, text="← Back to Grid", 
                                        command=self.go_back,
                                        height=35, width=120,
                                        font=ctk.CTkFont(size=13, weight="bold"),
                                        fg_color=COLORS['secondary'],
                                        hover_color=COLORS['primary'])
        self.back_button.pack(side="left")
        
        title_label = ctk.CTkLabel(header_frame, text=f"OUT{channel_num:02d} - Live Data Graph", 
                                  font=ctk.CTkFont(size=18, weight="bold"),
                                  text_color=COLORS['primary'])
        title_label.pack(side="left", padx=(20, 0))
        
        # Current value display
        value_frame = ctk.CTkFrame(header_frame, fg_color=COLORS['dark'], corner_radius=8)
        value_frame.pack(side="right")
        
        self.current_value_label = ctk.CTkLabel(value_frame, text="Current: ----.-- μm", 
                                               font=ctk.CTkFont(size=14, weight="bold"),
                                               text_color=COLORS['text'])
        self.current_value_label.pack(padx=15, pady=8)
        
        # Create matplotlib figure with dark theme
        plt.style.use('dark_background')
        self.figure = Figure(figsize=(10, 5), dpi=100, facecolor='#2D2D2D')
        self.ax = self.figure.add_subplot(111, facecolor='#1A1A1A')
        
        # Configure plot appearance
        self.ax.set_xlabel('Time (s)', color=COLORS['text'], fontsize=12)
        self.ax.set_ylabel('Thickness (μm)', color=COLORS['text'], fontsize=12)
        self.ax.tick_params(colors=COLORS['text'])
        self.ax.grid(True, alpha=0.3, color='gray')
        
        # Initialize empty line
        self.line, = self.ax.plot([], [], color=COLORS['primary'], linewidth=2, label='Measurement')
        
        # Embed plot in tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
    def go_back(self):
        if self.app_ref:
            self.app_ref.show_channel_grid()
        
    def set_start_time(self, start_time):
        self.start_time = start_time
        
    def update_graph(self, current_value=None, current_judge=None):
        """Update graph with new data"""
        try:
            timestamps, values, judges = self.graph_data_manager.get_channel_data(self.channel_num)
            
            if not timestamps:
                return
                
            if current_value is not None and current_value != -9999.98:
                self.current_value_label.configure(text=f"Current: {current_value:7.2f} μm ({current_judge})")
            
            valid_data = [(t, v) for t, v in zip(timestamps, values) if v != -9999.98]
            if not valid_data:
                return
                
            plot_times, plot_values = zip(*valid_data)
            
            if self.first_data_time is None:
                self.first_data_time = plot_times[0]
                
            relative_times = [(t - self.first_data_time).total_seconds() for t in plot_times]
            
            self.line.set_data(relative_times, plot_values)
            
            # Auto-scale
            if relative_times and plot_values:
                self.ax.set_xlim(0, max(relative_times) * 1.1)
                self.ax.set_ylim(min(plot_values) * 0.9, max(plot_values) * 1.1)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error in update_graph: {e}")