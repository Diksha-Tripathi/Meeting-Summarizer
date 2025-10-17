import os
import sys
import time
import json
import threading
import signal
import openai
import tiktoken
import ffmpeg
from dotenv import load_dotenv

TRANSCRIPTION_MODEL = "whisper-1"
SUMMARIZATION_MODEL = "gpt-4o-mini"
TOKENIZER_ENCODING = "cl100k_base"
MAX_TOKENS_PER_CHUNK = 8000

stop_ticker_flag = False

def display_ticker():
    """Displays a recording timer in the console for user feedback."""
    start_time = time.time()
    while not stop_ticker_flag:
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        sys.stdout.write(f'\rRecording: {minutes:02d}:{seconds:02d}')
        sys.stdout.flush()
        time.sleep(1)

def record_audio(output_filename):
    """
    Records audio from the default system microphone using ffmpeg.
    This process runs until it is terminated by the user (via the GUI or Ctrl+C).
    """
    global stop_ticker_flag
    stop_ticker_flag = False
    ticker_thread = threading.Thread(target=display_ticker)
    ticker_thread.start()

    print(f"Starting recording... Press 'Stop Recording' in the GUI to finish.")
    
    process = None
    try:
        if sys.platform == 'darwin': 
            input_format = 'avfoundation'
            input_device = ':0'
        elif sys.platform == 'win32': # Windows
            input_format = 'dshow'
            input_device = 'audio=default' # A common default, may need adjustment
        else: # Linux
            input_format = 'pulse'
            input_device = 'default'

        stream = ffmpeg.input(
            input_device, f=input_format
        ).output(
            output_filename, acodec="libmp3lame", audio_bitrate="192k", format="mp3"
        ).overwrite_output()
        
        # Run ffmpeg synchronously and wait for it to be terminated.
        process = ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)

    except ffmpeg.Error as e:
        # Write ffmpeg errors to stderr for the GUI to catch.
        error_message = e.stderr.decode('utf8')
        sys.stderr.write(f"An ffmpeg error occurred during recording:\n{error_message}\n")
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred during recording: {e}\n")
    finally:
        # Cleanly stop the ticker thread.
        stop_ticker_flag = True
        ticker_thread.join()
        print("\nRecording process finished.")


def transcribe_audio_with_api(filename, client):
    """
    Transcribes the given audio file using the OpenAI Whisper API.
    """
    print("Uploading audio for transcription via API... This may take a moment.")
    try:
        with open(filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=TRANSCRIPTION_MODEL,
                file=audio_file,
                response_format="text"
            )
        print("Transcription successful.")
        return transcript
    except openai.APIError as e:
        sys.stderr.write(f"OpenAI API Error during transcription: {e}\n")
        return None
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred during transcription: {e}\n")
        return None


def summarize_transcript(transcript, client):
    """
    Summarizes a long transcript using a Map-Reduce strategy to fit context windows.
    """
    print("Starting summarization process...")
    tokenizer = tiktoken.get_encoding(TOKENIZER_ENCODING)
    tokens = tokenizer.encode(transcript)

    # 1. MAP step: Summarize each chunk of the transcript individually.
    print(f"Splitting transcript into chunks...")
    chunks = []
    while tokens:
        chunk_tokens = tokens[:MAX_TOKENS_PER_CHUNK]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        tokens = tokens[MAX_TOKENS_PER_CHUNK:]
    
    chunk_summaries = []
    print(f"Summarizing {len(chunks)} chunk(s) of text...")
    for i, chunk in enumerate(chunks):
        print(f"  - Processing chunk {i+1}/{len(chunks)}...")
        map_prompt = f"""
        You are part of a summarization pipeline. Your task is to extract and summarize the key information from the following segment of a meeting transcript.
        Focus on concrete facts, decisions made, and any tasks assigned to individuals. Be concise and clear.

        Transcript Segment:
        ---
        {chunk}
        ---
        """
        summary = get_llm_response(map_prompt, client)
        if summary:
            chunk_summaries.append(summary)

    # 2. REDUCE step: Combine the individual summaries into one final, structured report.
    if not chunk_summaries:
        sys.stderr.write("Could not generate summaries for any transcript chunks.\n")
        return "{}"

    print("Generating final consolidated summary...")
    combined_summaries = "\n\n---\n\n".join(chunk_summaries)
    reduce_prompt = f"""
    You are an expert executive assistant. Your goal is to create a clear and actionable summary from a collection of meeting notes.
    Analyze the provided notes and generate a final report in a valid JSON object format.

    The JSON object must have exactly these three keys:
    1. "summary": A brief, one-paragraph overview of the meeting's main topics and outcomes.
    2. "key_decisions": A list of strings, where each string is a significant decision that was finalized.
    3. "action_items": A list of objects, where each object has three string keys: "task", "owner" (use "TBD" if unassigned), and "deadline" (use "Not specified" if none).

    Meeting Notes to Synthesize:
    ---
    {combined_summaries}
    ---
    Now, generate the final JSON report.
    """
    
    final_summary_json = get_llm_response(reduce_prompt, client, is_json=True)
    print("Summarization complete.")
    return final_summary_json


def get_llm_response(prompt, client, is_json=False):
    """A robust helper function to call the OpenAI Chat Completions API."""
    try:
        messages = [{"role": "system", "content": "You are a helpful assistant that processes text."},
                    {"role": "user", "content": prompt}]
        
        response_format = {"type": "json_object"} if is_json else {"type": "text"}

        response = client.chat.completions.create(
            model=SUMMARIZATION_MODEL,
            messages=messages,
            temperature=0.3,
            response_format=response_format,
        )
        return response.choices[0].message.content.strip()
    except openai.APIError as e:
        sys.stderr.write(f"OpenAI API Error during summarization: {e}\n")
        return "{}" if is_json else ""
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred during summarization: {e}\n")
        return "{}" if is_json else ""


def main():
    """Main entry point for the command-line interface."""
    if len(sys.argv) != 3:
        sys.stderr.write(f"Usage: python {sys.argv[0]} [record|summarize] <filename.mp3>\n")
        sys.exit(1)

    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        sys.stderr.write("Error: OPENAI_API_KEY environment variable not found in .env file.\n")
        sys.exit(1)
    
    client = openai.OpenAI(api_key=api_key)
    action, filename = sys.argv[1], sys.argv[2]

    if action == "record":
        record_audio(filename)
    elif action == "summarize":
        transcript = transcribe_audio_with_api(filename, client)
        if transcript:
            summary_json = summarize_transcript(transcript, client)
            # Use clear markers for the GUI to find and parse the output.
            print(f"TRANSCRIPT:{transcript}\n")
            print(f"SUMMARY_JSON_START:\n{summary_json}\nSUMMARY_JSON_END\n")
    else:
        sys.stderr.write(f"Invalid action '{action}'. Use 'record' or 'summarize'.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

