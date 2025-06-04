

# Core Imports
import streamlit as st
# from phi.agent import Agent
# from phi.model.google import Gemini
# from phi.tools.duckduckgo import DuckDuckGo
import google.generativeai as genai

from google.generativeai import upload_file, get_file
import google.generativeai as genai
from deep_translator import GoogleTranslator
import time
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import os

import requests
from bs4 import BeautifulSoup




# Load API Key
# load_dotenv()
# API_KEY = os.getenv("GOOGLE_API_KEY")
# if API_KEY:
#     genai.configure(api_key=API_KEY)

API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# Set Page Config
st.set_page_config(
    page_title="🎥 AI Video Summarizer",
    page_icon="🤖",
    layout="wide",
)

st.markdown("""     
            
    <style>
    body {
        background-color:#f0f0f0;
    }
    .main {
        background-color:#999999;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    .stTextArea textarea {
        height: 180px !important;
    }
   
    </style>
""", unsafe_allow_html=True)


# Title and Header
st.markdown("<h1 style='text-align: center;'>🎬 Long Videos!!!   No Worries - Get It Summarized</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>Analyze. Summarize. Translate. — Powered by Gemini 2.0 Flash Exp</h4>", unsafe_allow_html=True)
st.markdown("---")

# Session State
if 'original_summary' not in st.session_state:
    st.session_state.original_summary = None

# Initialize AI Agent
@st.cache_resource
# def initialize_agent():
#     return Agent(
#         name="Video AI Summarizer",
#         model=Gemini(id="gemini-2.0-flash-exp"),
#         tools=[DuckDuckGo()],
#         markdown=True,
#     )
# agent = initialize_agent()



def duckduckgo_search(query):
    url = f"https://html.duckduckgo.com/html/?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    results = soup.find_all("a", class_="result__a")
    return [r.get_text() for r in results[:5]]

# Upload Video
st.subheader("📁 Upload a Video")
video_file = st.file_uploader("Choose a video file", type=['mp4', 'mov', 'avi'])

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name
    st.video(video_path, format="video/mp4")

    st.subheader("❓ What do you want to know about this video?")
    user_query = st.text_area(
        "Ask any specific question or insight about the video...",
        placeholder="e.g. What is the main theme of this video?",
    )

    if st.button("🚀 Analyze Video"):
        if not user_query:
            st.warning("Please enter a question before analyzing the video.")
        else:
            try:
                with st.spinner("🔍 Processing video, please wait..."):
                    processed_video = upload_file(video_path)
                    while processed_video.state.name == "PROCESSING":
                        time.sleep(1)
                        processed_video = get_file(processed_video.name)

                    prompt = f"""
                    Analyze the uploaded video for content and context.
                    Respond to the following query using video insights and web knowledge:
                    {user_query}
                    Give a clear, concise, and user-friendly answer.
                    """

                    # response = agent.run(prompt, videos=[processed_video])
                    model = genai.GenerativeModel("gemini-1.5-flash")  # or "gemini-1.5-pro"
                    response = model.generate_content(
                        [prompt, processed_video],
                        generation_config={"temperature": 0.7},
                    )
                    st.session_state.original_summary = response.text

                    st.session_state.original_summary = response.text

                st.success("✅ Analysis Complete!")
                st.subheader("📄 Summary")
                st.markdown(response.text)

            except Exception as error:
                st.error(f"An error occurred: {error}")
            finally:
                Path(video_path).unlink(missing_ok=True)

    if st.session_state.original_summary:
        st.markdown("---")
        st.subheader("🌐 Translate Summary")
        languages = GoogleTranslator().get_supported_languages()
        lang_dict = {lang.capitalize(): lang for lang in languages}
        selected_lang = st.selectbox("Choose language", list(lang_dict.keys()), index=0)

        if st.button("🌍 Translate Summary"):
            try:
                translated = translate_text(st.session_state.original_summary, lang_dict[selected_lang])
                st.success("✅ Translation Successful!")
                st.subheader(f"🗣️ Translated Summary ({selected_lang})")
                st.markdown(translated)
            except Exception as error:
                st.error(f"Translation error: {str(error)}")

else:
    st.info("🎥 Please upload a video file to begin.")

# Translation helper function
def translate_text(text, dest_language):
    try:
        translator = GoogleTranslator(source='auto', target=dest_language)
        return translator.translate(text)
    except Exception as e:
        return f"Error in translation: {e}"
