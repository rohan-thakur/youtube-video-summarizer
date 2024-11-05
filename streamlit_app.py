import streamlit as st
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi as y
# from llama_index.core.llms import ChatMessage
# from llama_index.llms.ollama import Ollama
# from langchain.text_splitter import RecursiveCharacterTextSplitter
import ollama

# Function to extract video ID from YouTube URL
def get_video_id(youtube_url):
    url_components = urlparse(youtube_url)
    if url_components.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(url_components.query).get("v", [None])[0]
    elif url_components.hostname == "youtu.be":
        return url_components.path[1:]
    return None

# Function to get transcript as a single string
def get_transcript_text(video_id, translate_language):
    print(translate_language)
    # try:
    if translate_language:
        transcript_list = y.list_transcripts(video_id)
        for t in transcript_list:
            print(f'language code is {t.language_code}, is translatable {t.is_translatable}')
            if t.language_code=='en':
                transcript=t.translate(translate_language).fetch()
                print("I did the translation")
                print(transcript)
            else:
                continue

        # transcript = y.get_transcript(video_id)
        # print(type(transcript))
        # transcript = [t.translate(translate_language).fetch() for t in transcript]
        # print(transcript)
    else:
        transcript = y.get_transcript(video_id)
        print("I did no translation")
    return " ".join([snippet['text'] for snippet in transcript])
    # except Exception as e:
    #     st.error("Could not retrieve transcript. The video may not have subtitles.")
    #     return None

def get_transcript_languages(video_id):
    transcript_list = y.list_transcripts(video_id)
    # return [t['language'] for t in transcript_list._translation_languages]
    return transcript_list._translation_languages

# Function to summarize text using Ollama's LLaMA model
def summarize_text(text, prompt):
    print(f'llama has been given this text {text}')
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

    selected_language = st.selectbox("What language would you like the summary in?", get_transcript_languages(video_id))['language_code']
    print(selected_language)
    if video_id:
        print("Getting Transcript")
        transcript = get_transcript_text(video_id, selected_language)
        if transcript:
            with st.spinner("Generating summary..."):
                print(transcript)
                summary = summarize_text(transcript, prompt)
                #summary = summarize_large_string(transcript)
                st.write(summary)
    else:
        st.error("Invalid YouTube URL. Please check and try again.")
