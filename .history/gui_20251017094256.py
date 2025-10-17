import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLabel, QTextEdit, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QProcess

class MeetingSummarizer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Meeting Summarizer")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # --- Button Layout ---
        self.button_layout = QHBoxLayout()
        self.start_button = QPushButton("1. Start Recording")
        self.start_button.clicked.connect(self.start_recording)
        self.button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("2. Stop Recording")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False) # Disabled initially
        self.button_layout.addWidget(self.stop_button)
        layout.addLayout(self.button_layout)

        self.summarize_button = QPushButton("3. Summarize from Audio File")
        self.summarize_button.clicked.connect(self.summarize_from_file)
        layout.addWidget(self.summarize_button)

        self.transcript_label = QLabel("Transcript:")
        layout.addWidget(self.transcript_label)
        self.transcript_edit = QTextEdit()
        self.transcript_edit.setReadOnly(True)
        layout.addWidget(self.transcript_edit)

        self.summary_label = QLabel("Summary & Action Items:")
        layout.addWidget(self.summary_label)
        self.summary_edit = QTextEdit()
        self.summary_edit.setReadOnly(True)
        layout.addWidget(self.summary_edit)

        self.status_label = QLabel("Status: Idle")
        layout.addWidget(self.status_label)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        
        self.output_buffer = ""

    def update_ui_state(self, is_running):
        """Enable/disable buttons based on process state."""
        self.start_button.setEnabled(not is_running)
        self.summarize_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running and self.is_recording)

    def start_recording(self):
        output_filename, _ = QFileDialog.getSaveFileName(self, "Save Meeting Recording", filter="MP3 Files (*.mp3)")
        if not output_filename:
            return
        if not output_filename.endswith(".mp3"):
            output_filename += ".mp3"
        
        self.is_recording = True
        self.clear_output()
        self.status_label.setText("Status: Recording...")
        self.update_ui_state(True)
        self.process.start("python", ["cli.py", "record", output_filename])

    def stop_recording(self):
        if self.process.state() == QProcess.Running:
            self.process.terminate()
            self.status_label.setText("Status: Stopping recording...")

    def summarize_from_file(self):
        audio_filename, _ = QFileDialog.getOpenFileName(self, "Select Audio File", filter="Audio Files (*.mp3 *.wav *.m4a)")
        if not audio_filename:
            return
            
        self.is_recording = False
        self.clear_output()
        self.status_label.setText("Status: Summarizing audio file... This may take a moment.")
        self.update_ui_state(True)
        self.process.start("python", ["cli.py", "summarize", audio_filename])

    def clear_output(self):
        """Clears the output text boxes for a new session."""
        self.transcript_edit.clear()
        self.summary_edit.clear()
        self.output_buffer = ""

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.output_buffer += data
        
        if "SUMMARY_JSON_START" in self.output_buffer and "SUMMARY_JSON_END" in self.output_buffer:
            try:
                transcript_start = self.output_buffer.find("TRANSCRIPT:") + len("TRANSCRIPT:")
                transcript_end = self.output_buffer.find("SUMMARY_JSON_START")
                transcript = self.output_buffer[transcript_start:transcript_end].strip()
                self.transcript_edit.setPlainText(transcript)

                json_start = self.output_buffer.find("SUMMARY_JSON_START") + len("SUMMARY_JSON_START")
                json_end = self.output_buffer.find("SUMMARY_JSON_END")
                json_str = self.output_buffer[json_start:json_end].strip()
                
                summary_data = json.loads(json_str)
                self.display_summary(summary_data)

            except (json.JSONDecodeError, IndexError) as e:
                self.summary_edit.setPlainText(f"Error parsing summary output: {e}\n\nRaw output:\n{self.output_buffer}")
            except Exception as e:
                self.summary_edit.setPlainText(f"An unexpected error occurred: {e}")
        else:
             print(f"STDOUT: {data.strip()}") 

    def display_summary(self, data):
        """Formats the JSON data for display."""
        display_text = "### Meeting Summary ###\n"
        display_text += data.get("summary", "No summary provided.")
        display_text += "\n\n### Key Decisions ###\n"
        decisions = data.get("key_decisions", [])
        if decisions:
            for i, decision in enumerate(decisions, 1):
                display_text += f"{i}. {decision}\n"
        else:
            display_text += "No key decisions were identified.\n"

        display_text += "\n### Action Items ###\n"
        actions = data.get("action_items", [])
        if actions:
            for i, item in enumerate(actions, 1):
                owner = item.get('owner', 'TBD')
                task = item.get('task', 'No task specified')
                deadline = item.get('deadline', 'Not specified')
                display_text += f"{i}. Task: {task} (Owner: {owner}, Deadline: {deadline})\n"
        else:
            display_text += "No action items were identified.\n"

        self.summary_edit.setPlainText(display_text)


    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        if data:
            self.status_label.setText("Status: An error occurred.")
            QMessageBox.critical(self, "Error", f"An error occurred in the backend process:\n\n{data.strip()}")
        print(f"STDERR: {data.strip()}")

    def process_finished(self):
        self.status_label.setText("Status: Idle")
        self.update_ui_state(False)
        self.is_recording = False
        print("Process finished.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MeetingSummarizer()
    window.show()
    sys.exit(app.exec_())


