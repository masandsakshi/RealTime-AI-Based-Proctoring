import datetime
import json
import requests as req


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
        self.suspicious_count = 0
        self.last_event_time = 0
        self.EVENT_THRESHOLD = 0.5
        self.internal_widgets = set()
        self.focus_was_lost = False
        self.lost_focus_time = None

    def register_internal_widget(self, widget):
        """Register widgets that are part of the exam interface"""
        self.internal_widgets.add(str(widget))

    def _is_internal_widget(self, widget):
        """Check if the widget is part of our application"""
        if not widget:
            return False
        widget_str = str(widget)
        return any(internal in widget_str for internal in self.internal_widgets)

    def _should_log_event(self):
        """Check if enough time has passed since last event to log a new one"""
        current_time = datetime.datetime.now().timestamp()
        if current_time - self.last_event_time > self.EVENT_THRESHOLD:
            self.last_event_time = current_time
            return True
        return False

    def on_focus_out(self, event):
        focused_widget = self.widget.focus_get()

        if focused_widget and self._is_internal_widget(focused_widget):
            return

        if not focused_widget and self._should_log_event():
            timestamp = datetime.datetime.now().timestamp()
            self.suspicious_count += 1
            self.focus_was_lost = True
            self.lost_focus_time = timestamp

            entry = {
                "timestamp": f"{timestamp:.3f}",
                "key_value": f"SUSPICIOUS ACTIVITY #{self.suspicious_count}: Window lost focus",
                "key_event": "suspicious_activity",
            }

            print(f"\nWARNING: Suspicious Activity #{self.suspicious_count} detected!")
            print(f"Student switched away from exam window at {timestamp:.3f}")

            payload = {
                "Type": "focus",
                "Value": ["false", f"{timestamp:.3f}"],
            }

            print(json.dumps(payload))
            self.log_callback(entry)

    def on_focus_in(self, event):
        if self.focus_was_lost and self._should_log_event():
            timestamp = datetime.datetime.now().timestamp()

            entry = {
                "timestamp": f"{timestamp:.3f}",
                "key_value": "Window focus restored",
                "key_event": "focus_restore",
            }

            print(f"focus restored {timestamp:.3f}")

            payload = {
                "Type": "focus",
                "Value": ["true", f"{timestamp:.3f}"],
            }
            print(json.dumps(payload))

            if self.lost_focus_time:
                lost_duration = int((timestamp - self.lost_focus_time) * 1000)

                focus_duration_entry = {
                    "timestamp": f"{timestamp:.3f}",
                    "key_value": f"Focus lost duration: {lost_duration}ms",
                    "key_event": "focus_duration",
                    "duration": lost_duration,
                }

                payload = {
                    "Type": "focus",
                    "Value": [f"{lost_duration:.3f}"],
                }
                print(json.dumps(payload))
                self.log_callback(focus_duration_entry)

            self.log_callback(entry)

            self.focus_was_lost = False
            self.lost_focus_time = None
