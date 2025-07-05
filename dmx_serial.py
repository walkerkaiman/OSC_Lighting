import serial
import threading
import time

class DMXSerial:
    def __init__(self, port, baudrate=250000, log_func=print):
        self.port = port
        self.baudrate = baudrate
        self.log = log_func
        self.serial = None
        self.lock = threading.Lock()

    def open(self):
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            self.log(f"✅ Opened serial port {self.port} at {self.baudrate} baud.")
        except serial.SerialException as e:
            self.log(f"❌ Failed to open serial port: {e}")
            self.serial = None

    def close(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.log(f"🔌 Closed serial port {self.port}.")

    def send_dmx_frame(self, dmx_data):
        if not self.serial or not self.serial.is_open:
            self.log("⚠️ Serial port is not open. Cannot send DMX.")
            return

        with self.lock:
            try:
                # DMX BREAK and MARK AFTER BREAK
                self.serial.break_condition = True
                time.sleep(0.0001)  # 100µs break
                self.serial.break_condition = False
                time.sleep(0.000012)  # 12µs MAB

                # DMX START CODE + CHANNELS (max 512)
                frame = bytes([0x00] + list(dmx_data[:512]))
                self.serial.write(frame)
                self.serial.flush()
                self.log(f"➡️ Sent DMX frame with {len(dmx_data[:512])} channels.")

            except serial.SerialException as e:
                self.log(f"❌ Error sending DMX frame: {e}")

    def is_open(self):
        return self.serial is not None and self.serial.is_open
