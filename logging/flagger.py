import time
from collections import deque
import datetime
import os
import json
import math
import threading
import logging
import sys

# Create a single directory for all logs
os.makedirs("checklogs", exist_ok=True)

# Fix for Windows console encoding issues with emoji characters
if sys.platform == "win32":
    # Use ASCII-only emojis/symbols for Windows
    EMOJI_SAFE = True
    # Optional: Set console to UTF-8 mode - may work on newer Windows versions
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # Set to UTF-8
    except:
        pass
else:
    EMOJI_SAFE = False

# Configure logging to use the single directory and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("checklogs/checks.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


class FraudDetectionSystem:
    """Comprehensive system to analyze and flag suspicious activity during online exams."""

    def __init__(self):
        # Risk configuration - weight of each violation type
        self.RISK_WEIGHTS = {
            # Focus-related violations
            "focus_loss": 0.8,  # User's attention left the exam window
            "focus_return": -0.2,  # User returned to exam (slight positive)
            # Audio violations
            "sus_aud": 0.8,  # Suspicious audio detected (LOUD noise detected)
            # Video violations - exact messages from webcam.py
            "sus_vid": 1.0,  # Generic suspicious video activity
            "Ye Kaun Hai!!": 3.0,  # Multiple faces detected
            "Where you go????": 2.5,  # No face detected (user left)
            "Where you look?": 1.5,  # Looking away from screen
            # AI-detected keystroke anomalies
            "ai_check": 2.0,  # AI flagged unusual typing pattern
        }

        # Risk thresholds (percentage-based)
        self.THRESHOLDS = {
            "soft_warning": 25,  # 25% risk - mild warning
            "strong_warning": 45,  # 45% risk - strong warning
            "exam_review": 65,  # 65% risk - flag for manual review
            "exam_termination": 85,  # 85% risk - recommend termination
        }

        # Time windows for analysis (in seconds)
        self.ANALYSIS_WINDOWS = {
            "recent": 300,  # Last 5 minutes (high weight)
            "medium": 900,  # Last 15 minutes (medium weight)
            "full": 3600,  # Full hour (lower weight)
        }

        # Maximum risk score possible (used to scale percentage)
        self.MAX_RISK_SCORE = 30

        # Event storage with timestamps
        self.event_history = deque(maxlen=5000)

        # Track when events were last processed (for cooldown)
        self.last_event_time = {}

        # Cooldown periods for high-frequency events (seconds)
        # Aligned with the ALERT_COOLDOWN value from webcam.py (3 seconds)
        self.COOLDOWN_PERIODS = {
            "sus_aud": 3,  # Audio alerts can be frequent
            "sus_vid": 3,  # Match with webcam.py's ALERT_COOLDOWN
            "Ye Kaun Hai!!": 5,  # Multiple faces
            "Where you go????": 5,  # No face
            "Where you look?": 3,  # Suspicious gaze
            "focus_loss": 3,
        }

        # Track file reading position
        self.last_read_position = 0

        # Store violation counts for reporting
        self.violation_counts = {k: 0 for k in self.RISK_WEIGHTS.keys()}

        # Pattern detection for repeated behavior - using actual message strings
        self.pattern_tracker = {
            "focus_loss_pattern": deque(maxlen=10),
            "Where you look?": deque(maxlen=10),
            "Where you go????": deque(maxlen=5),
        }

        # Use the main log file for activity
        self.log_file = "activity.log"  # This is correct - monitoring activity.log

        # Ensure file exists
        if not os.path.exists(self.log_file):
            open(self.log_file, "a").close()

        # Log that we're monitoring this file
        logging.info(f"Monitoring activity log file: {self.log_file}")

    def log_event(self, event_type, timestamp, message=None, weight=None):
        """Records an event in the tracking system with throttling."""
        current_time = time.time()

        # Apply cooldown for high-frequency events
        if event_type in self.COOLDOWN_PERIODS:
            if event_type in self.last_event_time:
                time_since_last = current_time - self.last_event_time[event_type]
                if time_since_last < self.COOLDOWN_PERIODS[event_type]:
                    return False  # Skip this event, still in cooldown

            self.last_event_time[event_type] = current_time

        # Use specified weight or default from config
        if weight is None:
            weight = self.RISK_WEIGHTS.get(event_type, 0.5)

        # Store the event
        self.event_history.append(
            {
                "timestamp": timestamp,
                "type": event_type,
                "weight": weight,
                "message": message,
            }
        )

        # Update violation count
        self.violation_counts[event_type] = self.violation_counts.get(event_type, 0) + 1

        # Track patterns of suspicious behavior - using actual message strings from webcam.py
        if event_type == "focus_loss":
            self.pattern_tracker["focus_loss_pattern"].append(timestamp)
        elif event_type == "Where you look?":
            self.pattern_tracker["Where you look?"].append(timestamp)
        elif event_type == "Where you go????":
            self.pattern_tracker["Where you go????"].append(timestamp)

        return True  # Event was recorded

    def detect_patterns(self):
        """Detects suspicious patterns in the collected events."""
        current_time = time.time()
        patterns = {
            "frequent_focus_loss": False,
            "persistent_gaze_issues": False,
            "repeated_absence": False,
        }

        # Check for multiple focus losses in short timespan
        if len(self.pattern_tracker["focus_loss_pattern"]) >= 5:
            # If 5 focus losses happened within 3 minutes
            time_span = (
                self.pattern_tracker["focus_loss_pattern"][-1]
                - self.pattern_tracker["focus_loss_pattern"][0]
            )
            if time_span < 180:
                patterns["frequent_focus_loss"] = True

        # Check for persistent gaze issues - using "Where you look?" message
        if len(self.pattern_tracker["Where you look?"]) >= 4:
            # If 4 gaze issues happened within 2 minutes
            time_span = (
                self.pattern_tracker["Where you look?"][-1]
                - self.pattern_tracker["Where you look?"][0]
            )
            if time_span < 120:
                patterns["persistent_gaze_issues"] = True

        # Check for repeated absences - using "Where you go????" message
        if len(self.pattern_tracker["Where you go????"]) >= 3:
            # If student was absent 3 times within 5 minutes
            time_span = (
                self.pattern_tracker["Where you go????"][-1]
                - self.pattern_tracker["Where you go????"][0]
            )
            if time_span < 300:
                patterns["repeated_absence"] = True

        return patterns

    def calculate_risk(self):
        """Calculates the current risk score (0-100%) based on recorded events."""
        current_time = time.time()

        # Sort events into time windows
        recent_events = [
            e
            for e in self.event_history
            if e["timestamp"] > current_time - self.ANALYSIS_WINDOWS["recent"]
        ]
        medium_events = [
            e
            for e in self.event_history
            if current_time - self.ANALYSIS_WINDOWS["medium"]
            < e["timestamp"]
            <= current_time - self.ANALYSIS_WINDOWS["recent"]
        ]
        older_events = [
            e
            for e in self.event_history
            if current_time - self.ANALYSIS_WINDOWS["full"]
            < e["timestamp"]
            <= current_time - self.ANALYSIS_WINDOWS["medium"]
        ]

        # Apply time-based weighting
        total_risk = self._calculate_window_risk(recent_events, 1.0)  # Full weight
        total_risk += self._calculate_window_risk(medium_events, 0.6)  # 60% weight
        total_risk += self._calculate_window_risk(older_events, 0.3)  # 30% weight

        # Apply pattern multipliers
        patterns = self.detect_patterns()

        if patterns["frequent_focus_loss"]:
            total_risk *= 1.2  # 20% boost for suspicious pattern
        if patterns["persistent_gaze_issues"]:
            total_risk *= 1.25  # 25% boost for sustained gaze issues
        if patterns["repeated_absence"]:
            total_risk *= 1.3  # 30% boost for repeated absence

        # Cap at maximum risk score and convert to percentage
        risk_percentage = min(100, (total_risk / self.MAX_RISK_SCORE) * 100)
        return risk_percentage, patterns

    def _calculate_window_risk(self, events, time_factor):
        """Helper to calculate risk within a specific time window."""
        risk_score = 0

        # Group by event type for diminishing returns
        event_types = {}
        for event in events:
            event_type = event["type"]
            if event_type not in event_types:
                event_types[event_type] = []
            event_types[event_type].append(event)

        # Process each event type with diminishing returns
        for event_type, events_of_type in event_types.items():
            # Sort by weight (descending)
            events_of_type.sort(key=lambda x: x["weight"], reverse=True)

            # Apply diminishing returns formula
            for i, event in enumerate(events_of_type):
                diminishing_factor = 1.0 / (math.sqrt(i + 1))  # Square root diminishing
                risk_score += event["weight"] * diminishing_factor

        return risk_score * time_factor

    def get_risk_level(self, risk_percentage):
        """Maps a risk percentage to a risk level."""
        # Use ASCII-friendly symbols on Windows
        if EMOJI_SAFE:
            if risk_percentage >= self.THRESHOLDS["exam_termination"]:
                return "CRITICAL", "X EXAM TERMINATION RECOMMENDED"
            elif risk_percentage >= self.THRESHOLDS["exam_review"]:
                return "HIGH", "! MANUAL REVIEW REQUIRED"
            elif risk_percentage >= self.THRESHOLDS["strong_warning"]:
                return "MEDIUM", "! STRONG WARNING"
            elif risk_percentage >= self.THRESHOLDS["soft_warning"]:
                return "LOW", "* SOFT WARNING"
            else:
                return "SAFE", "OK NO ISSUES DETECTED"
        else:
            # Use Unicode emojis on other platforms
            if risk_percentage >= self.THRESHOLDS["exam_termination"]:
                return "CRITICAL", "❌ EXAM TERMINATION RECOMMENDED"
            elif risk_percentage >= self.THRESHOLDS["exam_review"]:
                return "HIGH", "⚠️ MANUAL REVIEW REQUIRED"
            elif risk_percentage >= self.THRESHOLDS["strong_warning"]:
                return "MEDIUM", "⚠️ STRONG WARNING"
            elif risk_percentage >= self.THRESHOLDS["soft_warning"]:
                return "LOW", "🔸 SOFT WARNING"
            else:
                return "SAFE", "✅ NO ISSUES DETECTED"

    def get_violation_summary(self):
        """Returns a summary of recorded violations."""
        return {
            # Focus violations
            "focus_violations": self.violation_counts.get("focus_loss", 0),
            # Audio violations
            "audio_violations": self.violation_counts.get("sus_aud", 0),
            # Video violations - using exact message strings
            "video_violations": sum(
                [
                    self.violation_counts.get("sus_vid", 0),
                    self.violation_counts.get("Ye Kaun Hai!!", 0),
                    self.violation_counts.get("Where you go????", 0),
                    self.violation_counts.get("Where you look?", 0),
                ]
            ),
            # AI violations
            "ai_violations": self.violation_counts.get("ai_check", 0),
        }

    def process_log_entry(self, line):
        """Process a single log line and update risk tracking."""
        try:
            # Parse the log entry
            parts = line.strip().split()
            if not parts or len(parts) < 2:
                return False

            # Handle different log formats based on actual implementation

            # Handle AI keystroke anomaly detection
            if parts[0] == "ai_check":
                try:
                    # Format: ai_check Score: X.XX
                    if "Score:" in line:
                        score_idx = parts.index("Score:") + 1
                        if score_idx < len(parts):
                            score = float(parts[score_idx])
                            weight = min(5, 0.5 + score * 0.9)
                            self.log_event(
                                "ai_check",
                                time.time(),
                                f"AI anomaly score: {score}",
                                weight,
                            )
                            return True
                except (ValueError, IndexError):
                    pass

            # Handle suspicious video events based on webcam.py
            elif parts[0] == "sus_vid":
                try:
                    # Format from send_alert in webcam.py:
                    # The event payload is {"Type": "sus_vid", "Value": [message, timestamp]}
                    # Extract timestamp (last element) and message (everything else)
                    timestamp = float(parts[-1])
                    message = " ".join(parts[1:-1])

                    # Use the actual message as the event type for specific tracking
                    if message in [
                        "Where you go????",
                        "Ye Kaun Hai!!",
                        "Where you look?",
                    ]:
                        self.log_event(message, timestamp, message)
                    else:
                        self.log_event("sus_vid", timestamp, message)
                    return True
                except (ValueError, IndexError):
                    pass

            # Handle suspicious audio events based on audio_analysis.py
            elif parts[0] == "sus_aud":
                try:
                    # Format from audio_analysis.py:
                    # The event payload has "Value": ["LOUD noise detected!", timestamp]
                    timestamp = float(parts[-1])
                    message = " ".join(parts[1:-1])
                    self.log_event("sus_aud", timestamp, message)
                    return True
                except (ValueError, IndexError):
                    pass

            # Handle focus events
            elif parts[0] == "focus":
                if len(parts) >= 2:
                    if parts[1] == "true":
                        # Focus regained
                        self.log_event(
                            "focus_return", time.time(), "Focus returned to exam"
                        )
                        return True
                    elif parts[1] == "false":
                        # Focus lost
                        self.log_event(
                            "focus_loss", time.time(), "Focus lost from exam"
                        )
                        return True
                    else:
                        # Focus duration report
                        try:
                            duration = float(parts[1])
                            if duration > 10:  # Only log significant focus loss
                                weight = min(3.0, duration / 20)  # Cap at 3.0
                                self.log_event(
                                    "focus_loss",
                                    time.time(),
                                    f"Focus lost for {duration}s",
                                    weight,
                                )
                                return True
                        except ValueError:
                            pass

            return False  # No recognized format

        except Exception as e:
            logging.error(f"Error processing log entry: {e}")
            return False

    def process_log_batch(self):
        """Processes new entries from the log file."""
        try:
            if not os.path.exists(self.log_file):
                logging.warning(f"Log file not found at {self.log_file}")
                return 0

            file_size = os.path.getsize(self.log_file)
            if file_size < self.last_read_position:
                # File was truncated, start from beginning
                self.last_read_position = 0

            with open(self.log_file, "r", encoding="utf-8") as f:
                # Move to last processed position
                f.seek(self.last_read_position)
                new_lines = f.readlines()
                self.last_read_position = f.tell()

                if not new_lines:
                    return 0

                processed_count = 0
                for line in new_lines:
                    if self.process_log_entry(line):
                        processed_count += 1

                if processed_count > 0:
                    logging.info(
                        f"Processed {processed_count} new events from {self.log_file}"
                    )

                return processed_count

        except FileNotFoundError:
            logging.error(f"Log file not found at {self.log_file}")
            return 0
        except Exception as e:
            logging.error(f"Error reading log file: {e}")
            return 0

    def generate_report(self, risk_percentage, patterns):
        """Generates a comprehensive risk report."""
        risk_level, risk_message = self.get_risk_level(risk_percentage)
        violation_summary = self.get_violation_summary()

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = {
            "timestamp": current_time,
            "risk_score": round(risk_percentage, 2),
            "risk_level": risk_level,
            "risk_message": risk_message,
            "violations": violation_summary,
            "suspicious_patterns": patterns,
            "recommendations": [],
        }

        # Add recommendations based on patterns and exact message strings
        if patterns["frequent_focus_loss"]:
            report["recommendations"].append(
                "Monitor for tab switching/window changing"
            )

        if patterns["persistent_gaze_issues"]:
            report["recommendations"].append(
                "Student may be looking at unauthorized resources"
            )

        if patterns["repeated_absence"]:
            report["recommendations"].append("Student repeatedly leaving camera view")

        if self.violation_counts.get("Ye Kaun Hai!!", 0) > 0:
            report["recommendations"].append("Multiple people detected during exam")

        if risk_percentage >= self.THRESHOLDS["exam_review"]:
            report["recommendations"].append("Immediate manual review required")

        # Change the path to use checklogs consistently
        try:
            with open("checklogs/risk_reports.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(report) + "\n")
        except Exception as e:
            logging.error(f"Failed to write risk report: {e}")

        return report

    def monitor_logs(self, interval=3):
        """Continuously monitors log file and updates risk score."""
        logging.info(
            f"Starting monitoring of {self.log_file} with interval {interval}s"
        )

        while True:
            try:
                processed_count = self.process_log_batch()

                if processed_count > 0:
                    risk_percentage, patterns = self.calculate_risk()
                    report = self.generate_report(risk_percentage, patterns)

                    # Print summary to console
                    risk_level, risk_message = self.get_risk_level(risk_percentage)
                    logging.info(f"Risk Score: {risk_percentage:.2f}% - {risk_message}")

                    # If critical risk, generate special alert
                    if risk_percentage >= self.THRESHOLDS["exam_termination"]:
                        logging.warning(
                            "CRITICAL RISK ALERT - POSSIBLE CHEATING DETECTED"
                        )

            except KeyboardInterrupt:
                logging.info("Monitoring stopped by user")
                break
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")

            time.sleep(interval)


# Entry point for running the script directly
if __name__ == "__main__":
    # Create and start the fraud detection system
    logging.info("Starting online proctoring fraud detection system...")
    detector = FraudDetectionSystem()
    detector.monitor_logs()
