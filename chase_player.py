import csv
import threading
import time
import os
import signal

class ChasePlayer:
    def __init__(self, filepath, loop=False, mute=False, framerate=30, brightness=255, dmx_sender=None, log_func=print):
        self.filepath = filepath
        self.loop = loop
        self.mute = mute
        self.framerate = framerate
        self.brightness = brightness
        self.dmx_sender = dmx_sender
        self.log = log_func

        self.frames = []
        self.play_thread = None
        self.stop_flag = threading.Event()

        self.valid_csv = self.load_csv()
        signal.signal(signal.SIGINT, self._handle_interrupt)

    def load_csv(self):
        if not self.filepath.lower().endswith(".csv"):
            self.log(f"❌ Invalid file type: {self.filepath}")
            return False

        if not os.path.exists(self.filepath):
            self.log(f"❌ File not found: {self.filepath}")
            return False

        try:
            with open(self.filepath, 'r') as f:
                reader = csv.reader(f)
                self.frames = []
                for row in reader:
                    if len(row) > 512:
                        self.log(f"⚠️ Skipped row with more than 512 channels: {len(row)}")
                        continue
                    frame = [min(255, max(0, int(v))) for v in row if v.strip().isdigit()]
                    self.frames.append(frame)

            self.log(f"✅ Loaded {len(self.frames)} frames from {os.path.basename(self.filepath)}")
            return True if self.frames else False
        except Exception as e:
            self.log(f"❌ Error reading CSV: {e}")
            return False

    def play(self):
        if not self.valid_csv:
            self.log("❌ Cannot play: Invalid or missing CSV file.")
            return

        if self.mute:
            self.log("🔇 Chase is muted. Playback skipped.")
            return

        if not self.dmx_sender or not self.dmx_sender.is_open():
            self.log("⚠️ Serial port is not open. Cannot send DMX.")
            return

        if not self.frames:
            self.log("🚫 No valid frames to play.")
            return

        if self.play_thread and self.play_thread.is_alive():
            self.log("⏳ Chase is already playing.")
            return

        self.stop_flag.clear()
        self.play_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.play_thread.start()

    def _play_loop(self):
        self.log(f"▶️ Playing chase: {os.path.basename(self.filepath)} ({'Looping' if self.loop else 'Once'})")
        interval = 1.0 / max(1, self.framerate)

        try:
            while not self.stop_flag.is_set():
                for frame in self.frames:
                    if self.stop_flag.is_set():
                        break
                    if self.dmx_sender:
                        scaled_frame = [min(255, int(val * self.brightness / 255)) for val in frame]
                        self.dmx_sender.send_dmx_frame(scaled_frame)
                    time.sleep(interval)

                if not self.loop:
                    break
        finally:
            self.log(f"⏹️ Finished chase: {os.path.basename(self.filepath)}")

    def stop(self):
        self.stop_flag.set()
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join()

    def is_playing(self):
        return self.play_thread and self.play_thread.is_alive()

    def _handle_interrupt(self, signum, frame):
        self.log("🔌 KeyboardInterrupt received. Stopping chase playback...")
        self.stop()
        exit(0)
