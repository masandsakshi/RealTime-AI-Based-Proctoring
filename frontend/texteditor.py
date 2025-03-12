import tkinter as tk
from tkinter import scrolledtext, filedialog
from tkinter import ttk
import tkinter.font as tkFont
import datetime
import csv
import os

class TextEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Exam Text Editor")
        self.root.geometry("800x600")

        # Set exam duration (3 hours = 10800 seconds)
        self.exam_duration = 10800
        self.time_remaining = self.exam_duration
        self.exam_started = False

        # Use a themed style for a better design
        style = ttk.Style()
        style.theme_use("clam")

        # Initialize the log buffer for keystrokes
        self.log_entries = []
        # CSV file name for logging
        self.csv_filename = "keystrokes.csv"

        # --- Header Frame ---
        header_frame = ttk.Frame(root, padding="10")
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        # Title label
        title_label = ttk.Label(
            header_frame, text="Online Exam Text Editor", font=("Helvetica", 18, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Clock label for a live timer
        self.timer_label = ttk.Label(header_frame, font=("Helvetica", 12))
        self.timer_label.grid(row=0, column=1, sticky="e")
        self.update_clock()

        # --- Menu Bar ---
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.new_file)
        filemenu.add_command(label="Open", command=self.open_file)
        filemenu.add_command(label="Save", command=self.save_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        root.config(menu=menubar)

        # --- Main Frame for Questions ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=1, column=0, sticky="nsew")
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Set a custom font for the text widgets
        custom_font = tkFont.Font(family="Helvetica", size=12)

        # Define the questions list
        self.questions = [
            "Question 1: What is Sex?",
            "Question 2: What is Gender?"
        ]

        # List to hold answer text widgets for each question
        self.answer_widgets = []

        # Create a separate LabelFrame for each question with reduced size
        for question in self.questions:
            q_frame = ttk.LabelFrame(main_frame, text=question, padding="5")
            # Fill horizontally only, not vertically, to reduce size
            q_frame.pack(fill="x", padx=5, pady=5)

            answer_widget = scrolledtext.ScrolledText(
                q_frame,
                wrap=tk.WORD,
                font=custom_font,
                bg="#ffffff",
                fg="#333",
                height=5  # Reduced height (number of text lines visible)
            )
            answer_widget.pack(fill="x", padx=5, pady=5)
            answer_widget.bind("<Key>", self.on_key_press)
            self.answer_widgets.append(answer_widget)

        # --- Status Bar ---
        self.status = tk.StringVar()
        self.status.set("Ready")
        status_bar = ttk.Label(
            root, textvariable=self.status, relief=tk.SUNKEN, anchor="w", padding=5
        )
        status_bar.grid(row=2, column=0, sticky="ew")

        # Schedule the log flush every 10 seconds
        self.root.after(10000, self.flush_log)

    def update_clock(self):
        if not self.exam_started:
            self.exam_started = True

        if self.time_remaining > 0:
            hours = self.time_remaining // 3600
            minutes = (self.time_remaining % 3600) // 60
            seconds = self.time_remaining % 60
            time_str = f"Time Remaining: {hours:02d}:{minutes:02d}:{seconds:02d} / 03:00:00"
            self.timer_label.config(text=time_str)
            self.time_remaining -= 1
            self.root.after(1000, self.update_clock)
        else:
            self.timer_label.config(text="Time's Up!")
            # Disable all answer widgets when time's up
            for widget in self.answer_widgets:
                widget.config(state="disabled")

    def on_key_press(self, event):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "key_value": event.char,   # The character pressed (empty for non-character keys)
            "key_event": event.keysym  # The key symbol (e.g., "Shift_L", "Return", etc.)
        }
        key_info = f"Key pressed: '{event.char}' (keysym: {event.keysym}) at {timestamp}"
        print(key_info)
        self.status.set(key_info)
        self.log_entries.append(log_entry)

    def flush_log(self):
        if self.log_entries:
            file_exists = os.path.exists(self.csv_filename)
            with open(self.csv_filename, mode="a", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["key_value", "key_event", "timestamp"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                for entry in self.log_entries:
                    writer.writerow(entry)
            self.log_entries = []
        self.root.after(10000, self.flush_log)

    def new_file(self):
        # Clear all answer text widgets
        for widget in self.answer_widgets:
            widget.delete("1.0", tk.END)
        self.status.set("New file created")

    def open_file(self):
        # For a multi-question editor, open_file functionality isn't straightforward.
        # Here, we'll display a status message indicating it's not supported.
        file_path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.status.set("Open file not supported in multi-question editor")

    def save_file(self):
        # Combine answers from all question frames into one text block
        combined_text = ""
        for i, widget in enumerate(self.answer_widgets):
            answer_text = widget.get("1.0", tk.END)
            combined_text += f"{self.questions[i]}\n{answer_text}\n\n"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(combined_text)
            self.status.set(f"Saved: {file_path}")

def main():
    root = tk.Tk()
    app = TextEditorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
