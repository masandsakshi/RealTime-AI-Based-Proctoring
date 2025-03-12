# focus.py
import datetime


class FocusMonitor:
    def __init__(self, widget, log_callback):
        """
        Initialize the FocusMonitor.

        :param widget: The Tkinter widget (typically root) to monitor.
        :param log_callback: A callback function that accepts a dictionary log entry.
        """
        self.widget = widget
        self.log_callback = log_callback
        self.widget.bind("<FocusOut>", self.on_focus_out)
        self.widget.bind("<FocusIn>", self.on_focus_in)

    def on_focus_out(self, event):
        timestamp = datetime.datetime.now().timestamp()
        entry = {
            "timestamp": f"{timestamp:.3f}",
            "key_value": "Window lost focus",
            "key_event": "focus_out",
        }
        print(f"Suspicious Activity: Window lost focus at {timestamp:.3f}")
        self.log_callback(entry)

    def on_focus_in(self, event):
        timestamp = datetime.datetime.now().timestamp()
        entry = {
            "timestamp": f"{timestamp:.3f}",
            "key_value": "Window gained focus",
            "key_event": "focus_in",
        }
        print(f"Window gained focus at {timestamp:.3f}")
        self.log_callback(entry)
