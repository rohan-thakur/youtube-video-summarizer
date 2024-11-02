import streamlit as st
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi as y
from llama_index.core.llms import ChatMessage
from llama_index.llms.ollama import Ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
import ollama

def chunk_text(text, chunk_size=500, chunk_overlap=50):
    """Splits text into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_text(text)
    return chunks

def summarize_chunk(chunk, model="llama3"):
    """Summarizes a single chunk of text using Ollama."""
    response = ollama.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes text."
            },
            {
                "role": "user",
                "content": f"Please summarize this text:\n{chunk}"
            }
        ]
    )
    return response["message"]["content"]

def summarize_large_string(text, model="llama3"):
    """Summarizes a large string by chunking and summarizing each chunk."""
    chunks = chunk_text(text)
    summaries = [summarize_chunk(chunk, model) for chunk in chunks]
    final_summary = "\n".join(summaries)
    return final_summary



# Function to extract video ID from YouTube URL
def get_video_id(youtube_url):
    url_components = urlparse(youtube_url)
    if url_components.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(url_components.query).get("v", [None])[0]
    elif url_components.hostname == "youtu.be":
        return url_components.path[1:]
    return None

# Function to get transcript as a single string
def get_transcript_text(video_id):
    try:
        transcript = y.get_transcript(video_id)
        return " ".join([snippet['text'] for snippet in transcript])
    except Exception as e:
        st.error("Could not retrieve transcript. The video may not have subtitles.")
        return None

# Function to summarize text using Ollama's LLaMA model
def summarize_text(text, prompt):
    response = ollama.chat(
        model='llama3',
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes text."
            },
            {
                "role": "user",
                "content": f"{prompt}:\n{text}"
            }
        ]
    )
    return response["message"]["content"]


# Streamlit app setup
st.title("YouTube Transcript Summarizer with LLaMA 3")
youtube_url = st.text_input("Enter YouTube video URL:")
prompt = st.text_input("Provide a prompt regarding what you are looking for.")

if youtube_url:
    print("Getting video_id")
    video_id = get_video_id(youtube_url)
    if video_id:
        print("Getting Transcript")
        transcript = get_transcript_text(video_id)
        if transcript:
            with st.spinner("Generating summary..."):
                summary = summarize_text(transcript, prompt)
                #summary = summarize_large_string(transcript)
                st.write(summary)
    else:
        st.error("Invalid YouTube URL. Please check and try again.")
