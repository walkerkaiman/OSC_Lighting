import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from serial.tools import list_ports
import time
import os
import json

class GUI:
    def __init__(self, root, config, on_add_chase_callback):
        self.root = root
        self.config = config
        self.on_add_chase_callback = on_add_chase_callback
        self.chase_blocks = []

        self.setup_gui()

    def setup_gui(self):
        self.root.title("Lighting Control App")
        self.root.geometry("900x700")

        self.setup_global_settings()
        self.setup_chase_area()
        self.setup_console_log()

    def setup_global_settings(self):
        top_frame = ttk.LabelFrame(self.root, text="Global Settings")
        top_frame.pack(fill="x", padx=10, pady=5)

        # COM Port
        ttk.Label(top_frame, text="COM Port:").grid(row=0, column=0, padx=5, pady=5)
        self.com_port_var = tk.StringVar(value=self.config.get("com_port", ""))
        self.com_port_dropdown = ttk.Combobox(top_frame, textvariable=self.com_port_var, values=self.get_serial_ports())
        self.com_port_dropdown.grid(row=0, column=1, padx=5, pady=5)

        # Baud Rate
        ttk.Label(top_frame, text="Baud Rate:").grid(row=0, column=2, padx=5, pady=5)
        self.baud_rate_var = tk.IntVar(value=self.config.get("baud_rate", 250000))
        self.baud_rate_dropdown = ttk.Combobox(top_frame, textvariable=self.baud_rate_var, values=[9600, 115200, 250000])
        self.baud_rate_dropdown.grid(row=0, column=3, padx=5, pady=5)

        # Frame Rate
        ttk.Label(top_frame, text="Framerate (fps):").grid(row=0, column=4, padx=5, pady=5)
        self.framerate_var = tk.IntVar(value=self.config.get("framerate", 30))
        self.framerate_entry = ttk.Entry(top_frame, textvariable=self.framerate_var, width=5)
        self.framerate_entry.grid(row=0, column=5, padx=5, pady=5)

        # Brightness
        ttk.Label(top_frame, text="Master Brightness:").grid(row=0, column=6, padx=5, pady=5)
        self.brightness_var = tk.IntVar(value=self.config.get("brightness", 255))
        self.brightness_slider = ttk.Scale(top_frame, from_=0, to=255, variable=self.brightness_var, orient="horizontal")
        self.brightness_slider.grid(row=0, column=7, padx=5, pady=5)

        # Add Chase Button
        self.add_chase_button = ttk.Button(top_frame, text="Add Light Chase", command=self.on_add_chase_callback)
        self.add_chase_button.grid(row=0, column=8, padx=10, pady=5)

    def setup_chase_area(self):
        chases_frame = ttk.LabelFrame(self.root, text="Light Chases")
        chases_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(chases_frame)
        self.scrollable_frame = ttk.Frame(self.canvas)

        scrollbar = ttk.Scrollbar(chases_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def setup_console_log(self):
        console_frame = ttk.LabelFrame(self.root, text="Console Log")
        console_frame.pack(fill="x", padx=10, pady=5)
        self.console_text = scrolledtext.ScrolledText(console_frame, height=8, state='disabled')
        self.console_text.pack(fill="x")

    def get_serial_ports(self):
        return [port.device for port in list_ports.comports()]

    def log_message(self, message):
        timestamp = time.strftime("[%H:%M:%S]")
        self.console_text.configure(state='normal')
        self.console_text.insert('end', f"{timestamp} {message}\n")
        self.console_text.configure(state='disabled')
        self.console_text.yview_moveto(1)

    def get_global_settings(self):
        return {
            "com_port": self.com_port_var.get(),
            "baud_rate": self.baud_rate_var.get(),
            "framerate": self.framerate_var.get(),
            "brightness": self.brightness_var.get(),
        }
