from pythonosc import dispatcher, osc_server
import threading

class OSCHandler:
    def __init__(self, port=8000, log_func=print):
        self.port = port
        self.log = log_func
        self.dispatcher = dispatcher.Dispatcher()
        self.server = None
        self.server_thread = None
        self.chase_callbacks = {}  # address -> callback

    def register_chase(self, address, callback):
        if not address.startswith("/"):
            address = f"/{address}"
        self.dispatcher.map(address, callback)
        self.chase_callbacks[address] = callback
        self.log(f"🔗 Registered OSC address: {address}")

    def unregister_chase(self, address):
        if address in self.chase_callbacks:
            self.dispatcher.unmap(address, self.chase_callbacks[address])
            del self.chase_callbacks[address]
            self.log(f"🗑️ Unregistered OSC address: {address}")

    def start(self):
        try:
            self.server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", self.port), self.dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            self.log(f"🎧 OSC Server listening on port {self.port}")
        except Exception as e:
            self.log(f"❌ Failed to start OSC server: {e}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.log("🛑 OSC server stopped.")
