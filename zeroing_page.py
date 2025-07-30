import customtkinter as ctk
from config import COLORS
import CL3wrap
import ctypes

OUT_NAMES = [f"OUT{str(i+1).zfill(2)}" for i in range(8)]
OUT_BITMASKS = [0x0001 << i for i in range(8)]  # Bitmasks from OUT01 to OUT08

class ZeroingPage(ctk.CTkFrame):
    def __init__(self, parent, device_id, go_back_callback, logger=None, num_channels=6):
        super().__init__(parent, fg_color=COLORS["card"], corner_radius=15)
        self.device_id = device_id
        self.go_back_callback = go_back_callback
        self.logger = logger
        self.num_channels = num_channels
        
        print(f"Initializing ZeroingPage with {num_channels} channels...")
        
        # Configure the frame to expand properly
        self.pack_propagate(False)
        
        # Create main container with explicit size
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        self.header = ctk.CTkLabel(main_container, text=f"Zero OUT Channels (1-{num_channels})", 
                                  font=ctk.CTkFont(size=18, weight="bold"),
                                  text_color=COLORS["text"])
        self.header.pack(pady=10)

        # Create regular frame for checkboxes (no scrolling)
        checkbox_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        checkbox_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Checkbox list - only show the selected number of channels
        self.check_vars = []
        for i in range(num_channels):
            var = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(checkbox_frame, text=OUT_NAMES[i], variable=var,
                                 text_color=COLORS["text"],
                                 fg_color=COLORS["primary"],
                                 hover_color=COLORS["accent"])
            chk.pack(anchor="w", padx=20, pady=5)
            self.check_vars.append(var)

        # Buttons
        self.button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        self.button_frame.pack(pady=15)

        self.zero_button = ctk.CTkButton(self.button_frame, text="Zero Selected", 
                                        command=self.zero_selected,
                                        fg_color=COLORS["primary"],
                                        hover_color=COLORS["accent"])
        self.zero_button.pack(side="left", padx=10)

        self.zero_all_button = ctk.CTkButton(self.button_frame, text="Zero ALL", 
                                            command=self.zero_all,
                                            fg_color=COLORS["warning"],
                                            hover_color=COLORS["accent"])
        self.zero_all_button.pack(side="left", padx=10)

        self.back_button = ctk.CTkButton(main_container, text="← Back", 
                                        command=self.go_back_callback,
                                        fg_color=COLORS["secondary"],
                                        hover_color=COLORS["accent"])
        self.back_button.pack(pady=5)

        self.status_label = ctk.CTkLabel(main_container, text="", 
                                        text_color=COLORS["text"])
        self.status_label.pack(pady=(5, 0))
        
        print("ZeroingPage initialization complete")

    def _connect_and_prepare(self):
        # Try to connect before zeroing using the existing logger if available
        if self.logger:
            try:
                print("[DEBUG] Using existing logger to connect...")
                result = self.logger.connect()
                print(f"[DEBUG] Logger connect returned: {result}")
                if result != 0:
                    print(f"[DEBUG] Connection failed with result: {result}")
            except Exception as e:
                print(f"[DEBUG] Could not connect using logger: {e}")
        else:
            try:
                print("[DEBUG] No logger provided, attempting direct connection...")
                import logger
                temp_logger = logger.CL3000Logger(8)
                result = temp_logger.connect()
                print(f"[DEBUG] Direct connect returned: {result}")
            except Exception as e:
                print(f"[DEBUG] Could not connect directly: {e}")
        
        # Try to stop measurement before zeroing
        try:
            print("[DEBUG] Attempting to stop measurement before zeroing...")
            CL3wrap.CL3IF_MeasurementControl(self.device_id, ctypes.c_ubyte(0))  # 0 = stop
            print("[DEBUG] Measurement stop call issued.")
        except Exception as e:
            print(f"[DEBUG] Could not stop measurement before zeroing: {e}")

    def zero_selected(self):
        self._connect_and_prepare()
        bitmask = 0
        for i, var in enumerate(self.check_vars):
            if var.get():
                bitmask |= OUT_BITMASKS[i]

        if bitmask == 0:
            self.status_label.configure(text="⚠️ No channels selected.")
            return

        try:
            device_id = ctypes.c_int(self.device_id)
            bitmask_c = ctypes.c_ushort(bitmask)
            on_off = ctypes.c_ubyte(True)  # True = enable auto-zero
            print(f"[DEBUG] Calling CL3IF_AutoZeroMulti with device_id={device_id.value}, bitmask={bitmask_c.value:#04x}, onOff={on_off.value}")
            result = CL3wrap.CL3IF_AutoZeroMulti(device_id, bitmask_c, on_off)
            print(f"[DEBUG] CL3IF_AutoZeroMulti returned {result} (hex: {CL3wrap.CL3IF_hex(result)})")
            if result == 0:
                self.status_label.configure(text=f"✓ Auto-zero enabled for selected channels.")
            else:
                self.status_label.configure(text=f"❌ Auto-zero failed. Error code: {result} (hex: {CL3wrap.CL3IF_hex(result)})")
        except Exception as e:
            self.status_label.configure(text=f"❌ Error: {str(e)}")

    def zero_all(self):
        self._connect_and_prepare()
        try:
            device_id = ctypes.c_int(self.device_id)
            # Create bitmask for only the selected number of channels
            all_channels_bitmask = (1 << self.num_channels) - 1  # e.g., for 6 channels: 0b111111 = 0x3F
            bitmask_c = ctypes.c_ushort(all_channels_bitmask)
            on_off = ctypes.c_ubyte(True)  # True = enable auto-zero
            print(f"[DEBUG] Calling CL3IF_AutoZeroMulti with device_id={device_id.value}, bitmask={bitmask_c.value:#04x}, onOff={on_off.value}")
            result = CL3wrap.CL3IF_AutoZeroMulti(device_id, bitmask_c, on_off)
            print(f"[DEBUG] CL3IF_AutoZeroMulti returned {result} (hex: {CL3wrap.CL3IF_hex(result)})")
            if result == 0:
                self.status_label.configure(text=f"✓ Auto-zero enabled for ALL {self.num_channels} channels.")
            else:
                self.status_label.configure(text=f"❌ Auto-zero failed. Error code: {result} (hex: {CL3wrap.CL3IF_hex(result)})")
        except Exception as e:
            self.status_label.configure(text=f"❌ Error: {str(e)}")
