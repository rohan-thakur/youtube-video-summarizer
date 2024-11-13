import streamlit as st
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi as y
import os
from groq import Groq

# Set up the Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Function to extract video ID from YouTube URL
def get_video_id(youtube_url):
    url_components = urlparse(youtube_url)
    if url_components.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(url_components.query).get("v", [None])[0]
    elif url_components.hostname == "youtu.be":
        return url_components.path[1:]
    return None

# Function to get available transcripts and specific languages for translation
def get_transcripts_and_languages(video_id):
    try:
        # Fetch the list of transcripts for the video
        transcript_list = y.list_transcripts(video_id)
        
        # Check if transcripts are available
        if not transcript_list:
            st.warning("No transcripts found for this video.")
            return {}, []

        transcripts = {transcript.language_code: transcript for transcript in transcript_list}

        # Define the list of supported languages for Llama 3.1
        supported_languages = [
            {"name": "English", "code": "en"},
            {"name": "French", "code": "fr"},
            {"name": "German", "code": "de"},
            {"name": "Hindi", "code": "hi"},
            {"name": "Italian", "code": "it"},
            {"name": "Portuguese", "code": "pt"},
            {"name": "Spanish", "code": "es"},
            {"name": "Thai", "code": "th"}
        ]

        # Get the list of available translation languages
        translation_languages = {lang['language_code'] for lang in transcript_list._translation_languages}

        # Filter supported languages based on available transcripts or translatable languages
        available_languages = [
            lang for lang in supported_languages
            if lang["code"] in transcripts or lang["code"] in translation_languages
        ]

        if not available_languages:
            st.warning("No translatable languages found for this video.")

        return transcripts, available_languages

    except Exception as e:
        st.error("Error retrieving transcript or languages.")
        print(f"Error: {e}")
        return {}, []

# Function to get transcript text, with optional translation
def get_transcript_text(transcripts, translate_language=None):
    try:
        transcript = transcripts.get('en')  # Default to English if available
        if transcript:
            if translate_language:
                transcript = transcript.translate(translate_language).fetch()
            else:
                transcript = transcript.fetch()
            return " ".join([snippet['text'] for snippet in transcript])
        else:
            st.warning("No English transcript available.")
    except Exception as e:
        st.error("Could not retrieve transcript text.")
        print(f"Error: {e}")
    return None

# Function to summarize text using Meta Llama 3.1 8B
def summarize_text(text, prompt):
    try:
        chat_history = [
            {"role": "system", "content": "You are a helpful assistant that summarizes text based on a user query."},
            {"role": "user", "content": f"{prompt}:\n{text}"}
        ]
        response = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=chat_history,
            max_tokens=8192,
            temperature=1.2
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error("Error in generating summary.")
        print(f"Error: {e}")
        return None

# Streamlit app setup
st.title("YouTube Video Summarizer")

# Step 1: Enter URL
with st.container():
    st.subheader("Step 1: Enter YouTube Video URL")
    youtube_url = st.text_input("Enter the video URL here")

# Proceed if URL is provided
if youtube_url:
    video_id = get_video_id(youtube_url)
    if video_id:
        # Step 2: Provide Prompt
        with st.container():
            st.subheader("Step 2: Enter Query Prompt")
            prompt = st.text_input("Describe what you’re looking for in the summary (e.g., main points, key takeaways)")

        # Proceed if prompt is provided
        if prompt:
            # Step 3: Select Language
            with st.container():
                st.subheader("Step 3: Select Language for Summary")
                transcripts, available_languages = get_transcripts_and_languages(video_id)
                if available_languages:
                    selected_language = st.selectbox(
                        "Choose language",
                        options=available_languages,
                        format_func=lambda lang: lang['name']
                    )
                    language_code = selected_language['code']

                    # Step 4: Generate Summary
                    transcript = get_transcript_text(transcripts, language_code)
                    if transcript:
                        with st.spinner("Generating summary..."):
                            summary = summarize_text(transcript, prompt)
                            if summary:
                                st.success("Summary generated successfully!")
                                st.write(summary)
                            else:
                                st.error("Failed to generate summary.")
                    else:
                        st.warning("Unable to retrieve transcript. Try another video or check subtitle availability.")
                else:
                    st.warning("No translatable languages found.")
    else:
        st.error("Invalid YouTube URL. Please check and try again.")
