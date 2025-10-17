Meeting Summarizer

A desktop application that records meeting audio, transcribes it using OpenAI's Whisper API, and generates a structured, actionable summary using the GPT-4o-mini model.

Overview

This tool is designed to boost productivity by automating the process of note-taking and summarizing meetings. It provides a simple graphical user interface (GUI) to either record live audio or process an existing audio file. The output includes a full transcript, a concise summary, a list of key decisions, and clearly defined action items.

Features

Live Audio Recording: Record meetings directly from your system's microphone and save them as MP3 files.

File-Based Summarization: Upload existing audio files (e.g., MP3, WAV, M4A) for transcription and summarization.

High-Accuracy Transcription: Leverages OpenAI's whisper-1 model for robust and precise speech-to-text conversion.

Structured, AI-Powered Summaries: Uses gpt-4o-mini to generate summaries in a clean JSON format, including:

A concise summary paragraph.

A bulleted list of key decisions.

A list of action items with assigned owners and deadlines.

Simple User Interface: An intuitive GUI built with PyQt5 that is easy to operate.

Tech Stack

Language: Python

GUI: PyQt5

Audio Processing: FFmpeg (via ffmpeg-python)

AI Services: OpenAI API

Transcription: Whisper (whisper-1)

Summarization: GPT (gpt-4o-mini)

Tokenization: tiktoken

Environment Variables: python-dotenv

Setup and Installation

Follow these steps to set up and run the project on your local machine.

1. Prerequisites

Python 3.8+ installed on your system.

FFmpeg: This is a required dependency for audio recording. You must install it separately.

macOS (using Homebrew): brew install ffmpeg

Windows (using Chocolatey): choco install ffmpeg

Linux (using apt): sudo apt update && sudo apt install ffmpeg

2. Clone the Repository

git clone [https://github.com/your-username/meeting-summarizer.git](https://github.com/your-username/meeting-summarizer.git)
cd meeting-summarizer


3. Install Dependencies

It is highly recommended to use a virtual environment.

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install the required Python packages
pip install -r requirements.txt


4. Set Up OpenAI API Key

You need an API key from OpenAI to use the transcription and summarization features.

Create a file named .env in the root directory of the project.

Add your API key to this file as follows:

OPENAI_API_KEY="sk-YourSecretApiKeyGoesHere"


How to Run the Application

Once the setup is complete, you can launch the GUI by running the gui.py script:

python gui.py


How to Use the Application

To Record a New Meeting

Click the "1. Start Recording" button.

A file dialog will open. Choose a location and name for your MP3 recording file and click "Save".

The application will start recording. A timer will be visible in the console where you launched the script.

Click the "2. Stop Recording" button to finish. The recording will be saved to the location you selected.

To get a summary, click "3. Summarize from Audio File" and select the file you just saved.

To Summarize an Existing Audio File

Click the "3. Summarize from Audio File" button.

Select a supported audio file (e.g., .mp3, .wav, .m4a) from your computer.

The application will begin the transcription and summarization process. This may take a few moments depending on the length of the audio.

The full transcript and the formatted summary will appear in the respective text boxes once the process is complete.
