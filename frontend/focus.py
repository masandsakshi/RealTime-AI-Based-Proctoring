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
        self.suspicious_count = 0  # Track number of focus losses
        self.last_event_time = 0
        self.EVENT_THRESHOLD = 0.5  # Increased threshold to 500ms
        self.internal_widgets = set()  # Track internal widgets
        self.focus_was_lost = False  # Track if focus was actually lost

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

        # Ignore if focus is moving to an internal widget
        if focused_widget and self._is_internal_widget(focused_widget):
            return

        # Only log if focus is truly lost to external window
        if not focused_widget and self._should_log_event():
            timestamp = datetime.datetime.now().timestamp()
            self.suspicious_count += 1
            self.focus_was_lost = True  # Set flag when focus is truly lost
            entry = {
                "timestamp": f"{timestamp:.3f}",
                "key_value": f"SUSPICIOUS ACTIVITY #{self.suspicious_count}: Window lost focus",
                "key_event": "suspicious_activity",
            }
            print(f"\nWARNING: Suspicious Activity #{self.suspicious_count} detected!")
            print(f"Student switched away from exam window at {timestamp:.3f}")
            self.log_callback(entry)

    def on_focus_in(self, event):
        # Only log focus restoration if we previously lost focus
        if self.focus_was_lost and self._should_log_event():
            timestamp = datetime.datetime.now().timestamp()
            entry = {
                "timestamp": f"{timestamp:.3f}",
                "key_value": "Window focus restored",
                "key_event": "focus_restore",
            }
            print(f"Student returned to exam window at {timestamp:.3f}")
            self.log_callback(entry)
            self.focus_was_lost = False  # Reset the flag
