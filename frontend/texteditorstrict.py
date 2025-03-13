import tkinter as tk
from tkinter import scrolledtext, filedialog
from tkinter import ttk
import tkinter.font as tkFont
import datetime
import csv
import os
# import time  # For time functions
from focus import FocusMonitor  # Import our focus monitor module
from tkinter import messagebox


class TextEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Exam Text Editor")

        # Make window fullscreen and add security measures
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)  # Keep window always on top
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button
        self.root.resizable(False, False)  # Disable resizing

        # Remove escape key binding to prevent exiting fullscreen
        # self.root.bind('<Escape>', lambda e: root.attributes('-fullscreen', False))

        # Add controlled exit method
        self.exam_finished = False

        # Set exam duration (3 hours = 10800 seconds)
        self.exam_duration = 10800
        self.time_remaining = self.exam_duration
        self.exam_started = False

        style = ttk.Style()
        style.theme_use("clam")

        # Initialize the log buffer for keystrokes and events
        self.log_entries = []
        self.csv_filename = "keystrokes.csv"

        # --- Header Frame ---
        header_frame = ttk.Frame(root, padding="10")
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        title_label = ttk.Label(
            header_frame, text="Online Exam Text Editor", font=("Helvetica", 18, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w")

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

        custom_font = tkFont.Font(family="Helvetica", size=12)

        # Define the questions list
        self.questions = [
            "Question 1: What is your name?",
            "Question 2: What is your age?",
        ]

        self.question_frames = []
        self.answer_widgets = []

        self.page_container = ttk.Frame(main_frame)
        self.page_container.pack(fill="both", expand=True)

        # Create a separate frame for each question (each page)
        for question in self.questions:
            frame = ttk.Frame(self.page_container, padding="10")
            question_label = ttk.Label(
                frame, text=question, font=("Helvetica", 14, "bold")
            )
            question_label.pack(anchor="w", pady=(0, 5))
            answer_widget = scrolledtext.ScrolledText(
                frame,
                wrap=tk.WORD,
                font=custom_font,
                bg="#ffffff",
                fg="#333",
                height=5,  # Adjust height as needed
            )
            answer_widget.pack(fill="both", expand=True)
            # Bind Key Down and Key Up events
            answer_widget.bind("<KeyPress>", self.on_key_down)
            answer_widget.bind("<KeyRelease>", self.on_key_up)
            self.answer_widgets.append(answer_widget)
            self.question_frames.append(frame)

        self.current_question = 0
        self.show_question_page(self.current_question)

        # --- Navigation Frame ---
        nav_frame = ttk.Frame(main_frame, padding="10")
        nav_frame.pack(fill="x")
        self.prev_button = ttk.Button(
            nav_frame, text="Previous", command=self.show_previous
        )
        self.prev_button.pack(side="left")
        self.next_button = ttk.Button(nav_frame, text="Next", command=self.show_next)
        self.next_button.pack(side="right")
        self.update_nav_buttons()

        # --- Status Bar ---
        self.status = tk.StringVar()
        self.status.set("Ready")
        status_bar = ttk.Label(
            root, textvariable=self.status, relief=tk.SUNKEN, anchor="w", padding=5
        )
        status_bar.grid(row=2, column=0, sticky="ew")

        # Schedule the log flush every 5 seconds
        self.root.after(5000, self.flush_log)

        # Register internal widgets with focus monitor
        self.focus_monitor = FocusMonitor(root, self.append_log_entry)
        self.focus_monitor.register_internal_widget(self.prev_button)
        self.focus_monitor.register_internal_widget(self.next_button)
        for widget in self.answer_widgets:
            self.focus_monitor.register_internal_widget(widget)

    def append_log_entry(self, entry):
        """Callback for external events (like focus events) to add a log entry."""
        self.log_entries.append(entry)

    def show_question_page(self, index):
        for frame in self.question_frames:
            frame.pack_forget()
        self.question_frames[index].pack(fill="both", expand=True)

    def update_nav_buttons(self):
        if self.current_question == 0:
            self.prev_button.config(state="disabled")
        else:
            self.prev_button.config(state="normal")
        if self.current_question == len(self.questions) - 1:
            self.next_button.config(text="Finish")
        else:
            self.next_button.config(text="Next")

    def log_question_change(self, question_label):
        timestamp = datetime.datetime.now().timestamp()
        log_entry = {
            "timestamp": f"{timestamp:.3f}",
            "key_value": question_label,
            "key_event": "question_change",
        }
        print(f"Question changed to: {question_label} at {timestamp:.3f}")
        self.log_entries.append(log_entry)

    def show_previous(self):
        if self.current_question > 0:
            self.current_question -= 1
            self.show_question_page(self.current_question)
            self.update_nav_buttons()
            self.log_question_change(self.questions[self.current_question])

    def show_next(self):
        if self.current_question < len(self.questions) - 1:
            self.current_question += 1
            self.show_question_page(self.current_question)
            self.update_nav_buttons()
            self.log_question_change(self.questions[self.current_question])
        else:
            for widget in self.answer_widgets:
                widget.config(state="disabled")
            self.prev_button.config(state="disabled")
            self.next_button.config(state="disabled")
            self.status.set("Exam Finished")
            self.exam_finished = True

            # Save final log entries
            self.flush_log()

            # Schedule window closure after 2 seconds
            self.root.after(2000, self.root.destroy)

            # Show completion message
            messagebox.showinfo(
                "Exam Complete",
                "Your exam has been submitted successfully.\nThe window will close automatically.",
            )

    def update_clock(self):
        if not self.exam_started:
            self.exam_started = True
        if self.time_remaining > 0:
            hours = self.time_remaining // 3600
            minutes = (self.time_remaining % 3600) // 60
            seconds = self.time_remaining % 60
            time_str = (
                f"Time Remaining: {hours:02d}:{minutes:02d}:{seconds:02d} / 03:00:00"
            )
            self.timer_label.config(text=time_str)
            self.time_remaining -= 1
            self.root.after(1000, self.update_clock)
        else:
            self.timer_label.config(text="Time's Up!")
            for widget in self.answer_widgets:
                widget.config(state="disabled")

    def on_key_down(self, event):
        timestamp = datetime.datetime.now().timestamp()
        key_value = event.char if event.char else event.keysym
        log_entry = {
            "timestamp": f"{timestamp:.3f}",
            "key_value": key_value,
            "key_event": "KD",
        }
        print(f"KD: {key_value} at {timestamp:.3f}")
        self.status.set(f"KD: {key_value}")
        self.log_entries.append(log_entry)

    def on_key_up(self, event):
        timestamp = datetime.datetime.now().timestamp()
        key_value = event.char if event.char else event.keysym
        log_entry = {
            "timestamp": f"{timestamp:.3f}",
            "key_value": key_value,
            "key_event": "KU",
        }
        print(f"KU: {key_value} at {timestamp:.3f}")
        self.status.set(f"KU: {key_value}")
        self.log_entries.append(log_entry)

    def flush_log(self):
        if self.log_entries:
            file_exists = os.path.exists(self.csv_filename)
            with open(
                self.csv_filename, mode="a", newline="", encoding="utf-8"
            ) as csvfile:
                fieldnames = ["timestamp", "key_value", "key_event"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                for entry in self.log_entries:
                    writer.writerow(entry)
            self.log_entries = []
        self.root.after(5000, self.flush_log)

    def new_file(self):
        for widget in self.answer_widgets:
            widget.delete("1.0", tk.END)
        self.status.set("New file created")

    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.status.set("Open file not supported in multi-question editor")

    def save_file(self):
        combined_text = ""
        for i, widget in enumerate(self.answer_widgets):
            answer_text = widget.get("1.0", tk.END)
            combined_text += f"{self.questions[i]}\n{answer_text}\n\n"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(combined_text)
            self.status.set(f"Saved: {file_path}")


def main():
    root = tk.Tk()
    app = TextEditorApp(root)
    # FocusMonitor is now initialized in TextEditorApp
    root.mainloop()


if __name__ == "__main__":
    main()
