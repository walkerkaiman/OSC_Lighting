import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import json
import os
import time
import signal
import sys
from serial.tools import list_ports
from dmx_serial import DMXSerial
from osc_handler import OSCHandler
from chase_player import ChasePlayer

CONFIG_FILE = "config.json"

class LightingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OSC Lighting")
        self.root.geometry("750x700")
        self.root.resizable(False, True)
        self.root.configure(bg="#111")

        self.config = self.load_config()
        self.chase_blocks = []
        self.chase_players = []

        self.dmx = DMXSerial(self.config["com_port"], self.config["baud_rate"], self.log_message)
        self.osc = OSCHandler(8000, self.log_message)

        self.setup_gui()
        self.setup_signal_handlers()
        self.dmx.open()
        self.osc.start()

        self.log_message("App started.")
        
    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.graceful_shutdown)
        signal.signal(signal.SIGTERM, self.graceful_shutdown)

    def graceful_shutdown(self, signum, frame):
        self.log_message("🔌 KeyboardInterrupt or termination signal received. Shutting down...")
        self.save_config()
        self.root.quit()
        sys.exit(0)

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ JSON error in config file: {e}")
            return {
                "com_port": "",
                "baud_rate": 115200,
                "framerate": 30,
                "brightness": 255,
                "chases": []
            }

    def save_config(self):
        self.config["com_port"] = self.com_port_var.get()
        self.config["baud_rate"] = self.baud_rate_var.get()
        self.config["framerate"] = self.framerate_var.get()
        self.config["brightness"] = self.brightness_var.get()

        # Serialize chase block data if it's not already a list of dicts
        serialized_chases = []
        for block in self.chase_blocks:
            if isinstance(block, dict):
                serialized_chases.append(block)
            elif hasattr(block, 'get'):
                serialized_chases.append(block.get())
            else:
                self.log_message("⚠️ Could not serialize a chase block.")
        
        self.config["chases"] = serialized_chases

        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.log_message("💾 Config saved successfully.")
        except Exception as e:
            self.log_message(f"❌ Failed to save config: {e}")

    def setup_gui(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TFrame", background="#111")
        style.configure("TLabel", background="#111", foreground="white", font=("Segoe UI", 10))
        style.configure("TButton", background="#333", foreground="white", font=("Segoe UI", 10))
        style.configure("TEntry", fieldbackground="#222", foreground="white")
        style.configure("TCheckbutton", background="#111", foreground="white")
        style.configure("TLabelframe", background="#111", foreground="white", font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", foreground="white")

        top_frame = ttk.LabelFrame(self.root, text="Global Settings")
        top_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(top_frame, text="COM Port:").grid(row=0, column=0, padx=5, pady=5)
        self.com_port_var = tk.StringVar(value=self.config["com_port"])
        self.com_port_dropdown = ttk.Combobox(top_frame, textvariable=self.com_port_var, values=self.get_serial_ports(), width=15)
        self.com_port_dropdown.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(top_frame, text="Baud Rate:").grid(row=0, column=2, padx=5, pady=5)
        self.baud_rate_var = tk.IntVar(value=self.config["baud_rate"])
        self.baud_rate_dropdown = ttk.Combobox(top_frame, textvariable=self.baud_rate_var, values=[9600, 115200, 250000], width=10)
        self.baud_rate_dropdown.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(top_frame, text="Framerate (fps):").grid(row=0, column=4, padx=5, pady=5)
        self.framerate_var = tk.IntVar(value=self.config["framerate"])
        self.framerate_entry = ttk.Entry(top_frame, textvariable=self.framerate_var, width=5)
        self.framerate_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(top_frame, text="Master Brightness:").grid(row=0, column=6, padx=5, pady=5)
        self.brightness_var = tk.IntVar(value=self.config["brightness"])
        self.brightness_slider = ttk.Scale(top_frame, from_=0, to=255, variable=self.brightness_var, orient="horizontal", length=100)
        self.brightness_slider.grid(row=0, column=7, padx=5, pady=5)

        chases_frame = ttk.LabelFrame(self.root, text="Light Chases")
        chases_frame.pack(fill="both", expand=True, padx=10, pady=(5, 0))
        self.canvas = tk.Canvas(chases_frame, bg="#111", highlightthickness=0)
        self.scrollable_frame = ttk.Frame(self.canvas)

        scrollbar = ttk.Scrollbar(chases_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        for chase in self.config["chases"]:
            self.add_chase_block(chase)

        self.add_chase_button = ttk.Button(self.root, text="Add Light Chase", command=self.add_chase_block)
        self.add_chase_button.pack(pady=5)

        console_frame = ttk.LabelFrame(self.root, text="Console Log")
        console_frame.pack(fill="x", padx=10, pady=(0, 5))
        self.console_text = scrolledtext.ScrolledText(console_frame, height=8, state='disabled', background="#111", foreground="white", insertbackground="white")
        self.console_text.pack(fill="x")

    def get_serial_ports(self):
        return [port.device for port in list_ports.comports()]

    def log_message(self, message):
        timestamp = time.strftime("[%H:%M:%S]")
        if hasattr(self, "console_text"):
            self.console_text.configure(state='normal')
            self.console_text.insert('end', f"{timestamp} {message}\n")
            self.console_text.configure(state='disabled')
            self.console_text.yview_moveto(1)
        else:
            print(f"{timestamp} {message}")

    def add_chase_block(self, chase_data=None):
        frame = ttk.LabelFrame(self.scrollable_frame, text="Chase")
        frame.pack(fill="x", padx=5, pady=5)

        osc_var = tk.StringVar(value=chase_data.get("osc", "") if chase_data else "")
        file_var = tk.StringVar(value=chase_data.get("file", "") if chase_data else "")
        loop_var = tk.BooleanVar(value=chase_data.get("loop", False) if chase_data else False)
        mute_var = tk.BooleanVar(value=chase_data.get("mute", False) if chase_data else False)

        def toggle_loop():
            loop_var.set(not loop_var.get())
            loop_btn.config(text="Loop" if loop_var.get() else "Play Once")

        ttk.Label(frame, text="OSC Address:").grid(row=0, column=0, padx=5, pady=2)
        osc_entry = ttk.Entry(frame, textvariable=osc_var, width=15)
        osc_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(frame, text="CSV File:").grid(row=0, column=2, padx=5, pady=2)
        file_entry = ttk.Entry(frame, textvariable=file_var, width=25)
        file_entry.grid(row=0, column=3, padx=5, pady=2)
        ttk.Button(frame, text="Browse", command=lambda: self.select_file(file_var)).grid(row=0, column=4, padx=5)

        loop_btn = ttk.Button(frame, text="Loop" if loop_var.get() else "Play Once", command=toggle_loop, width=10)
        loop_btn.grid(row=1, column=0, padx=5)

        ttk.Checkbutton(frame, text="Mute", variable=mute_var).grid(row=1, column=1, padx=5)
        ttk.Button(frame, text="Play", command=lambda: self.play_chase(file_var.get(), loop_var.get(), mute_var.get())).grid(row=1, column=2, padx=5)
        ttk.Button(frame, text="Remove", command=lambda: self.remove_chase_block(frame, chase_data)).grid(row=1, column=3, padx=5)

        player = ChasePlayer(file_var.get(), loop_var.get(), mute_var.get(), self.framerate_var.get(), self.brightness_var.get(), self.dmx, self.log_message)
        self.chase_players.append(player)

        self.osc.register_chase(osc_var.get(), lambda addr, *args: player.play())

        self.log_message("Added new chase block.")
        if not chase_data:
            self.config["chases"].append({"osc": osc_var.get(), "file": file_var.get(), "loop": loop_var.get(), "mute": mute_var.get()})
            self.save_config()

    def select_file(self, var):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            var.set(path)

    def play_chase(self, filepath, loop, mute):
        player = ChasePlayer(filepath, loop, mute, self.framerate_var.get(), self.brightness_var.get(), self.dmx, self.log_message)
        player.play()

    def remove_chase_block(self, frame, chase_data):
        frame.destroy()
        if chase_data in self.config["chases"]:
            self.config["chases"].remove(chase_data)
            self.save_config()
        self.log_message("Removed chase block.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LightingApp(root)
    root.mainloop()