import customtkinter as ctk
from config import COLORS
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from scipy.interpolate import interp1d

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
        
        # Zoom controls
        zoom_frame = ctk.CTkFrame(self, fg_color="transparent")
        zoom_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Time zoom controls (X-axis)
        time_label = ctk.CTkLabel(zoom_frame, text="Time Zoom:", 
                                 font=ctk.CTkFont(size=12, weight="bold"),
                                 text_color=COLORS['text'])
        time_label.pack(side="left", padx=(0, 5))
        
        self.time_zoom_in_button = ctk.CTkButton(zoom_frame, text="⏱+", width=40, height=30,
                                                command=self.time_zoom_in,
                                                font=ctk.CTkFont(size=12),
                                                fg_color=COLORS['info'],
                                                hover_color=COLORS['primary'])
        self.time_zoom_in_button.pack(side="left", padx=2)
        
        self.time_zoom_out_button = ctk.CTkButton(zoom_frame, text="⏱-", width=40, height=30,
                                                 command=self.time_zoom_out,
                                                 font=ctk.CTkFont(size=12),
                                                 fg_color=COLORS['info'],
                                                 hover_color=COLORS['primary'])
        self.time_zoom_out_button.pack(side="left", padx=(2, 15))
        
        # Y-axis zoom controls
        y_label = ctk.CTkLabel(zoom_frame, text="Y-Axis Zoom:", 
                              font=ctk.CTkFont(size=12, weight="bold"),
                              text_color=COLORS['text'])
        y_label.pack(side="left", padx=(0, 5))
        
        self.zoom_in_button = ctk.CTkButton(zoom_frame, text="🔍+", width=40, height=30,
                                           command=self.zoom_in,
                                           font=ctk.CTkFont(size=12),
                                           fg_color=COLORS['primary'],
                                           hover_color=COLORS['success'])
        self.zoom_in_button.pack(side="left", padx=2)
        
        self.zoom_out_button = ctk.CTkButton(zoom_frame, text="🔍-", width=40, height=30,
                                            command=self.zoom_out,
                                            font=ctk.CTkFont(size=12),
                                            fg_color=COLORS['primary'],
                                            hover_color=COLORS['success'])
        self.zoom_out_button.pack(side="left", padx=(2, 15))
        
        # Control buttons
        self.auto_zoom_button = ctk.CTkButton(zoom_frame, text="Auto Fit", width=70, height=30,
                                             command=self.auto_zoom,
                                             font=ctk.CTkFont(size=12),
                                             fg_color=COLORS['accent'],
                                             hover_color=COLORS['primary'])
        self.auto_zoom_button.pack(side="left", padx=5)
        
        # Auto-update toggle button
        self.auto_update_enabled = True
        self.auto_update_button = ctk.CTkButton(zoom_frame, text="🔄 Auto-Update ON", width=100, height=30,
                                               command=self.toggle_auto_update,
                                               font=ctk.CTkFont(size=12),
                                               fg_color=COLORS['success'],
                                               hover_color=COLORS['primary'])
        self.auto_update_button.pack(side="left", padx=5)
        
        # Instructions label
        instructions = ctk.CTkLabel(zoom_frame, text="💡 Drag=Pan | Wheel=Zoom Both", 
                                   font=ctk.CTkFont(size=10),
                                   text_color="gray60")
        instructions.pack(side="right", padx=10)
        
        # Create matplotlib figure with dark theme
        plt.style.use('dark_background')
        self.figure = Figure(figsize=(10, 5), dpi=100, facecolor='#2D2D2D')
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
        
        # Initialize empty line with smooth curves
        self.line, = self.ax.plot([], [], color=COLORS['primary'], linewidth=2, label='Measurement', 
                                 linestyle='-', marker='o', markersize=3, alpha=0.8)
        self.go_points = self.ax.scatter([], [], c=COLORS['success'], s=40, alpha=0.8, label='GO', zorder=5)
        self.hi_points = self.ax.scatter([], [], c=COLORS['danger'], s=40, alpha=0.8, label='HI', zorder=5)
        self.lo_points = self.ax.scatter([], [], c=COLORS['warning'], s=40, alpha=0.8, label='LO', zorder=5)
        
        self.ax.legend(loc='upper right', facecolor='#2D2D2D', edgecolor=COLORS['text'])
        
        # Zoom state
        self.manual_x_limits = None
        self.manual_y_limits = None
        self.auto_zoom_enabled = True
        
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
        
        # Initialize with any existing data and auto-fit immediately
        self._initial_fit()
        
    def _initial_fit(self):
        """Perform initial auto-fit of all available data"""
        try:
            print(f"Initial fit for channel {self.channel_num}")
            self.auto_zoom_enabled = True
            self.manual_x_limits = None
            self.manual_y_limits = None
            self.auto_zoom_button.configure(fg_color=COLORS['accent'], text="Auto Fit")
            self.auto_zoom()  # Directly call auto_zoom to ensure initial fit
        except Exception as e:
            print(f"Error in initial fit: {e}")
            self.ax.set_xlim(0, 10)
            self.ax.set_ylim(0, 100)
            self.update_x_axis_ticks()
            self.canvas.draw_idle()

    def go_back(self):
        if self.app_ref:
            self.app_ref.show_channel_grid()
        
    def set_start_time(self, start_time):
        self.start_time = start_time
        print(f"Start time set to: {start_time}")
        
    def time_zoom_in(self):
        self.auto_zoom_enabled = False
        self.auto_update_enabled = False
        self.auto_update_button.configure(text="⏸️ Auto-Update OFF", fg_color=COLORS['warning'])
        current_limits = self.ax.get_xlim()
        center = (current_limits[0] + current_limits[1]) / 2
        range_val = (current_limits[1] - current_limits[0]) / 2
        new_range = range_val * 0.7
        
        x_min = max(0, center - new_range)
        x_max = center + new_range
        
        self.manual_x_limits = (x_min, x_max)
        self.ax.set_xlim(self.manual_x_limits)
        self.update_x_axis_ticks()
        self.canvas.draw_idle()
        self.auto_zoom_button.configure(fg_color=COLORS['warning'], text="Manual")
        print(f"Manual X limits set: {self.manual_x_limits}")
        
    def time_zoom_out(self):
        self.auto_zoom_enabled = False
        self.auto_update_enabled = False
        self.auto_update_button.configure(text="⏸️ Auto-Update OFF", fg_color=COLORS['warning'])
        current_limits = self.ax.get_xlim()
        center = (current_limits[0] + current_limits[1]) / 2
        range_val = (current_limits[1] - current_limits[0]) / 2
        new_range = range_val * 1.3
        
        x_min = max(0, center - new_range)
        x_max = center + new_range
        
        self.manual_x_limits = (x_min, x_max)
        self.ax.set_xlim(self.manual_x_limits)
        self.update_x_axis_ticks()
        self.canvas.draw_idle()
        self.auto_zoom_button.configure(fg_color=COLORS['warning'], text="Manual")
        print(f"Manual X limits set: {self.manual_x_limits}")
        
    def zoom_in(self):
        self.auto_zoom_enabled = False
        self.auto_update_enabled = False
        self.auto_update_button.configure(text="⏸️ Auto-Update OFF", fg_color=COLORS['warning'])
        current_limits = self.ax.get_ylim()
        center = (current_limits[0] + current_limits[1]) / 2
        range_val = (current_limits[1] - current_limits[0]) / 2
        new_range = range_val * 0.7
        
        self.manual_y_limits = (center - new_range, center + new_range)
        self.ax.set_ylim(self.manual_y_limits)
        self.canvas.draw_idle()
        self.auto_zoom_button.configure(fg_color=COLORS['warning'], text="Manual")
        print(f"Manual Y limits set: {self.manual_y_limits}")
        
    def zoom_out(self):
        self.auto_zoom_enabled = False
        self.auto_update_enabled = False
        self.auto_update_button.configure(text="⏸️ Auto-Update OFF", fg_color=COLORS['warning'])
        current_limits = self.ax.get_ylim()
        center = (current_limits[0] + current_limits[1]) / 2
        range_val = (current_limits[1] - current_limits[0]) / 2
        new_range = range_val * 1.3
        
        self.manual_y_limits = (center - new_range, center + new_range)
        self.ax.set_ylim(self.manual_y_limits)
        self.canvas.draw_idle()
        self.auto_zoom_button.configure(fg_color=COLORS['warning'], text="Manual")
        print(f"Manual Y limits set: {self.manual_y_limits}")
        
    def toggle_auto_update(self):
        self.auto_update_enabled = not self.auto_update_enabled
        if self.auto_update_enabled:
            self.auto_update_button.configure(text="🔄 Auto-Update ON", fg_color=COLORS['success'])
            self.auto_zoom_enabled = True
            self.manual_x_limits = None
            self.manual_y_limits = None
            self.auto_zoom_button.configure(fg_color=COLORS['accent'], text="Auto Fit")
            print("Auto-update and auto-zoom ENABLED")
            self.auto_zoom()  # Force auto-zoom when turning on auto-update
        else:
            self.auto_update_button.configure(text="⏸️ Auto-Update OFF", fg_color=COLORS['warning'])
            print("Auto-update DISABLED")
    
    def auto_zoom(self):
        """Auto-fit all data in view"""
        try:
            self.auto_zoom_enabled = True
            self.manual_x_limits = None
            self.manual_y_limits = None
            self.auto_zoom_button.configure(fg_color=COLORS['accent'], text="Auto Fit")
            
            timestamps, values, judges = self.graph_data_manager.get_channel_data(self.channel_num)
            if timestamps and values:
                valid_data = [(t, v) for t, v in zip(timestamps, values) if v != -9999.98]
                if valid_data:
                    plot_times, plot_values = zip(*valid_data)
                    if self.first_data_time is None:
                        self.first_data_time = plot_times[0]
                    relative_times = [(t - self.first_data_time).total_seconds() for t in plot_times]
                    if relative_times and min(relative_times) < 0:
                        time_offset = abs(min(relative_times))
                        relative_times = [t + time_offset for t in relative_times]
                    
                    time_min, time_max = min(relative_times), max(relative_times)
                    time_range = time_max - time_min
                    time_padding = max(0.5, time_range * 0.05)
                    self.ax.set_xlim(max(0, time_min - time_padding), time_max + time_padding)
                    
                    y_min, y_max = min(plot_values), max(plot_values)
                    y_range = y_max - y_min
                    y_padding = 1.0 if y_range == 0 else y_range * 0.1
                    self.ax.set_ylim(y_min - y_padding, y_max + y_padding)
                    
                    self.update_x_axis_ticks()
                    self.canvas.draw_idle()
                    print(f"Auto zoom: X: ({time_min - time_padding:.2f}, {time_max + time_padding:.2f}), Y: ({y_min - y_padding:.2f}, {y_max + y_padding:.2f})")
                    return
            # Fallback for no data
            self.ax.set_xlim(0, 10)
            self.ax.set_ylim(0, 100)
            self.update_x_axis_ticks()
            self.canvas.draw_idle()
            print("No valid data for auto zoom")
        except Exception as e:
            print(f"Error in auto_zoom: {e}")
        
    def create_smooth_curve(self, x_data, y_data):
        if len(x_data) < 2:
            return x_data, y_data
        try:
            f = interp1d(x_data, y_data, kind='cubic', bounds_error=False, fill_value='extrapolate')
            x_min, x_max = min(x_data), max(x_data)
            num_points = min(200, len(x_data) * 10)
            x_smooth = [x_min + i * (x_max - x_min) / (num_points - 1) for i in range(num_points)]
            y_smooth = f(x_smooth)
            return x_smooth, y_smooth
        except ImportError:
            if len(x_data) >= 3:
                x_smooth = []
                y_smooth = []
                for i in range(len(x_data) - 1):
                    x_smooth.append(x_data[i])
                    y_smooth.append(y_data[i])
                    for j in range(1, 3):
                        ratio = j / 3.0
                        x_interp = x_data[i] + ratio * (x_data[i + 1] - x_data[i])
                        y_interp = y_data[i] + ratio * (y_data[i + 1] - y_data[i])
                        x_smooth.append(x_interp)
                        y_smooth.append(y_interp)
                x_smooth.append(x_data[-1])
                y_smooth.append(y_data[-1])
                return x_smooth, y_smooth
            return x_data, y_data
        
    def update_x_axis_ticks(self):
        x_min, x_max = self.ax.get_xlim()
        time_range = x_max - x_min
        if time_range <= 10:
            tick_interval = 1
        elif time_range <= 30:
            tick_interval = 2
        elif time_range <= 60:
            tick_interval = 5
        elif time_range <= 300:
            tick_interval = 30
        elif time_range <= 600:
            tick_interval = 60
        else:
            tick_interval = 120
        
        start_tick = max(0, int(x_min / tick_interval) * tick_interval)
        ticks = []
        current_tick = start_tick
        while current_tick <= x_max:
            ticks.append(current_tick)
            current_tick += tick_interval
        
        if x_min <= 0 <= x_max and 0 not in ticks:
            ticks.insert(0, 0)
            ticks.sort()
        
        self.ax.set_xticks(ticks)
        if tick_interval >= 60:
            labels = [f"{int(t//60)}:{int(t%60):02d}" for t in ticks]
        else:
            labels = [f"{int(t)}" for t in ticks]
        self.ax.set_xticklabels(labels)
        
    def on_scroll(self, event):
        if event.inaxes != self.ax:
            return
        self.auto_zoom_enabled = False
        self.auto_update_enabled = False
        self.auto_update_button.configure(text="⏸️ Auto-Update OFF", fg_color=COLORS['warning'])
        self.auto_zoom_button.configure(fg_color=COLORS['warning'], text="Manual")
        
        zoom_factor = 1.15 if event.step > 0 else 1/1.15
        mouse_x, mouse_y = event.xdata, event.ydata
        if mouse_x is None or mouse_y is None:
            return
        
        x_min, x_max = self.ax.get_xlim()
        x_range = x_max - x_min
        new_x_range = x_range * zoom_factor
        x_center_ratio = (mouse_x - x_min) / x_range if x_range > 0 else 0.5
        new_x_min = mouse_x - new_x_range * x_center_ratio
        new_x_max = mouse_x + new_x_range * (1 - x_center_ratio)
        
        if new_x_min < 0:
            new_x_max += abs(new_x_min)
            new_x_min = 0
            
        self.manual_x_limits = (new_x_min, new_x_max)
        self.ax.set_xlim(self.manual_x_limits)
        
        y_min, y_max = self.ax.get_ylim()
        y_range = y_max - y_min
        new_y_range = y_range * zoom_factor
        y_center_ratio = (mouse_y - y_min) / y_range if y_range > 0 else 0.5
        new_y_min = mouse_y - new_y_range * y_center_ratio
        new_y_max = mouse_y + new_y_range * (1 - y_center_ratio)
        
        self.manual_y_limits = (new_y_min, new_y_max)
        self.ax.set_ylim(self.manual_y_limits)
        
        self.update_x_axis_ticks()
        self.canvas.draw_idle()
        print(f"Manual limits set - X: {self.manual_x_limits}, Y: {self.manual_y_limits}")
        
    def on_button_press(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
        self.auto_zoom_enabled = False
        self.auto_update_enabled = False
        self.auto_update_button.configure(text="⏸️ Auto-Update OFF", fg_color=COLORS['warning'])
        self.auto_zoom_button.configure(fg_color=COLORS['warning'], text="Manual")
        self.is_panning = True
        self.pan_start = (event.xdata, event.ydata)
        self.pan_start_xlim = self.ax.get_xlim()
        self.pan_start_ylim = self.ax.get_ylim()
        self.canvas.get_tk_widget().configure(cursor="fleur")
        
    def on_mouse_motion(self, event):
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
            
        self.manual_x_limits = (new_x_min, new_x_max)
        self.manual_y_limits = (y_min + dy, y_max + dy)
        
        self.ax.set_xlim(self.manual_x_limits)
        self.ax.set_ylim(self.manual_y_limits)
        self.update_x_axis_ticks()
        self.canvas.draw_idle()
        
    def on_button_release(self, event):
        self.is_panning = False
        self.pan_start = None
        self.pan_start_xlim = None
        self.pan_start_ylim = None
        self.canvas.get_tk_widget().configure(cursor="")
        
    def update_graph(self, current_value=None, current_judge=None):
        """Update graph with new data, auto-fitting if enabled"""
        try:
            timestamps, values, judges = self.graph_data_manager.get_channel_data(self.channel_num)
            print(f"Updating graph for channel {self.channel_num} - {len(timestamps)} points")
            
            if not timestamps:
                print("No data to plot")
                self.ax.set_xlim(0, 10)
                self.ax.set_ylim(0, 100)
                self.update_x_axis_ticks()
                self.canvas.draw_idle()
                return
                
            if current_value is not None and current_value != -9999.98:
                self.current_value_label.configure(text=f"Current: {current_value:7.2f} μm ({current_judge})")
            
            valid_data = [(t, v, j) for t, v, j in zip(timestamps, values, judges) if v != -9999.98]
            if not valid_data:
                print("No valid data to plot")
                self.ax.set_xlim(0, 10)
                self.ax.set_ylim(0, 100)
                self.update_x_axis_ticks()
                self.canvas.draw_idle()
                return
                
            plot_times, plot_values, plot_judges = zip(*valid_data)
            
            if self.first_data_time is None:
                self.first_data_time = plot_times[0]
                print(f"First data time set to: {self.first_data_time}")
                
            relative_times = [(t - self.first_data_time).total_seconds() for t in plot_times]
            if relative_times and min(relative_times) < 0:
                time_offset = abs(min(relative_times))
                relative_times = [t + time_offset for t in relative_times]
            
            if len(relative_times) >= 2:
                smooth_times, smooth_values = self.create_smooth_curve(relative_times, plot_values)
                self.line.set_data(smooth_times, smooth_values)
            else:
                self.line.set_data(relative_times, plot_values)
            
            go_data = [(rt, v) for rt, v, j in zip(relative_times, plot_values, plot_judges) if j == "GO"]
            hi_data = [(rt, v) for rt, v, j in zip(relative_times, plot_values, plot_judges) if j == "HI"]
            lo_data = [(rt, v) for rt, v, j in zip(relative_times, plot_values, plot_judges) if j == "LO"]
            
            self.go_points.set_offsets(list(zip(*go_data)) if go_data else [])
            self.hi_points.set_offsets(list(zip(*hi_data)) if hi_data else [])
            self.lo_points.set_offsets(list(zip(*lo_data)) if lo_data else [])
            
            if self.auto_update_enabled:
                self.auto_zoom_enabled = True
                self.manual_x_limits = None
                self.manual_y_limits = None
                self.auto_zoom_button.configure(fg_color=COLORS['accent'], text="Auto Fit")
                self.auto_zoom()
            else:
                if self.manual_x_limits:
                    self.ax.set_xlim(self.manual_x_limits)
                if self.manual_y_limits:
                    self.ax.set_ylim(self.manual_y_limits)
                self.update_x_axis_ticks()
                self.canvas.draw_idle()
            
            print("Graph updated successfully")
            
        except Exception as e:
            print(f"Error in update_graph: {e}")
            import traceback
            traceback.print_exc()