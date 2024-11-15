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

# Function to get available transcripts and filter supported languages
def get_transcripts(video_id):
    try:
        transcript_list = y.list_transcripts(video_id)
        
        # Check if transcripts are available
        if not transcript_list:
            st.warning("No transcripts found for this video.")
            return {}, []

        transcripts = {transcript.language_code: transcript for transcript in transcript_list}

        # Define supported languages for LLaMA 3.2
        supported_languages = {
            "en": "English", "fr": "French", "de": "German", "hi": "Hindi",
            "it": "Italian", "pt": "Portuguese", "es": "Spanish", "th": "Thai"
        }

        # Check which supported languages have available transcripts or translations
        available_languages = {
            code: name for code, name in supported_languages.items()
            if code in transcripts or code in transcript_list._translation_languages
        }
        return transcripts, available_languages
    except Exception as e:
        st.error("Error retrieving transcript or languages.")
        print(f"Error: {e}")
        return {}, {}

# Function to get transcript text, with optional translation
def get_transcript_text(transcripts, language_code):
    try:
        transcript = transcripts.get(language_code, transcripts.get("en"))  # Default to English if available
        if transcript:
            transcript = transcript.fetch()
            return " ".join([snippet['text'] for snippet in transcript])
        else:
            st.warning("Transcript not available in the selected language.")
    except Exception as e:
        st.error("Could not retrieve transcript text.")
        print(f"Error: {e}")
    return None

# Function to summarize text using LLaMA 3.2
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

# Form to group all steps
with st.form("summary_form"):
    st.subheader("Complete the steps below and hit 'Submit' when ready")

    # Step 1: Enter URL
    youtube_url = st.text_input("Enter YouTube Video URL")

    # Step 2: Ask Questions
    prompt = st.text_input("What would you like to know about the video? (Ask questions or describe desired insights)")

    # Step 3: Select Language
    supported_languages = {
        "en": "English", "fr": "French", "de": "German", "hi": "Hindi",
        "it": "Italian", "pt": "Portuguese", "es": "Spanish", "th": "Thai"
    }
    selected_language = st.selectbox("Choose language for summary", options=supported_languages.keys(),
                                     format_func=lambda code: supported_languages[code])
    
    # Submit button
    submitted = st.form_submit_button("Submit")

# Once the form is submitted, process the input
if submitted:
    if youtube_url and prompt:
        video_id = get_video_id(youtube_url)
        if video_id:
            transcripts, available_languages = get_transcripts(video_id)
            if selected_language in available_languages:
                transcript = get_transcript_text(transcripts, selected_language)
                if transcript:
                    with st.spinner("Generating summary..."):
                        summary = summarize_text(transcript, prompt)
                        if summary:
                            st.success("Summary generated successfully!")
                            # Embed YouTube video above the summary
                            st.video(f"https://www.youtube.com/watch?v={video_id}")
                            st.write(summary)
                        else:
                            st.error("Failed to generate summary.")
                else:
                    st.warning("Unable to retrieve transcript. Try another video or check subtitle availability.")
            else:
                st.warning("Selected language not available for this video.")
        else:
            st.error("Invalid YouTube URL. Please check and try again.")
    else:
        st.error("Please complete all steps before submitting.")
