import os
import re
import ssl
import tempfile

import streamlit as st
import fitz  # PyMuPDF
import docx2txt
import pytesseract
from PIL import Image
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from io import BytesIO
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
import google.generativeai as genai

# ------------- CONFIG & SETUP -------------

st.set_page_config(page_title="Universal IDP Bot", layout="wide")

if "uploader_version" not in st.session_state:
    st.session_state["uploader_version"] = 0

# Sidebar: Chat Options
chat_mode = st.sidebar.radio("🧭 Choose Option", ["Continue Chat", "🆕 Start New Chat"])

if chat_mode == "🆕 Start New Chat":
    for key in ["chat", "text", "chat_history", "new_chat_triggered"]:
        st.session_state[key] = None if key != "chat_history" else []
    st.session_state["uploader_version"] += 1
    st.success("✅ New chat session started. Upload a document to begin.")
    


# Bypass SSL verification issues if any
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ''
os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = ""

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-pro-preview-03-25")

# Set Tesseract OCR path (adjust for your machine)
pytesseract.pytesseract.tesseract_cmd = r"C:\\Users\\nake5001\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"

# ------------- CUSTOM CSS FOR CHAT UI -------------

CUSTOM_CSS = """
<style>

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
    background: url('https://www.transparenttextures.com/patterns/connected.png'), linear-gradient(145deg, #fef9f8, #f5f7fa);
    background-blend-mode: overlay;
    background-attachment: fixed;
    color: #212529;
}


/* --- USER MESSAGES --- */
.user-msg {
    background-color: #e7f5ff; /* Light blue */
    color: #084298; /* Deep blue text */
    padding: 12px 16px;
    border-radius: 15px;
    margin: 10px 0;
    max-width: 70%;
    margin-left: auto;
    text-align: right;
    font-size: 16px;
    box-shadow: 0 2px 6px rgba(0, 123, 255, 0.2);
}

/* --- BOT MESSAGES --- */
.bot-msg {
    background-color: #f1f3f5; /* Soft gray */
    color: #343a40;
    padding: 12px 16px;
    border-radius: 15px;
    margin: 10px 0;
    max-width: 70%;
    margin-right: auto;
    text-align: left;
    font-size: 16px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

/* --- TEXT INPUT --- */
.stTextInput > div > div > input {
    width: 100% !important;
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #ced4da;
    border-radius: 10px;
    padding: 10px;
    font-size: 16px;
    transition: 0.3s;
}
.stTextInput > div > div > input:focus {
    border-color: #74c0fc;
    box-shadow: 0 0 5px #a5d8ff;
}

/* --- FILE UPLOADER + BUTTONS --- */
button, .stButton>button {
    background-color: #228be6;
    color: #fff;
    border: none;
    padding: 10px 16px;
    border-radius: 10px;
    font-size: 16px;
    transition: all 0.3s ease;
}
button:hover, .stButton>button:hover {
    background-color: #1c7ed6;
}

/* --- DOWNLOAD & RESET BUTTON --- */
.stDownloadButton > button {
    background-color: #51cf66;
}
.stDownloadButton > button:hover {
    background-color: #40c057;
}
.stButton:has(button:contains("Reset")) > button {
    background-color: #ffa94d;
}
.stButton:has(button:contains("Reset")) > button:hover {
    background-color: #ff922b;
}

/* --- SPINNER --- */
.css-1y4p8pa {
    color: #495057;
}

/* --- AUDIO PLAYER BG FIX (optional) --- */
audio {
    background-color: #f8f9fa;
    border-radius: 10px;
}
</style>

"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ------------- FILE EXTRACTION FUNCTIONS -------------

def extract_pdf(file):
    if file.size > 10 * 1024 * 1024:  # 10 MB limit
        return "File too large. Please upload under 10MB."
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return " ".join(page.get_text() for page in doc)

def extract_docx(file):
    return docx2txt.process(file)

def extract_image(file):
    image = Image.open(file)
    return pytesseract.image_to_string(image)

def extract_audio(file):
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        try:
            if file.name.endswith(".mp3"):
                audio = AudioSegment.from_file(file, format="mp3")
                audio.export(tmp.name, format="wav")
            else:
                tmp.write(file.read())
            with sr.AudioFile(tmp.name) as source:
                audio_data = recognizer.record(source)
                return recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return "Could not understand the audio."
        except sr.RequestError:
            return "Speech recognition service unavailable."
        finally:
            os.remove(tmp.name)

def extract_text(file, file_type):
    extractors = {
        "pdf": extract_pdf,
        "docx": extract_docx,
        "txt": lambda f: f.read().decode("utf-8"),
        "png": extract_image,
        "jpg": extract_image,
        "jpeg": extract_image,
        "wav": extract_audio,
        "mp3": extract_audio,
        "m4a": extract_audio,
    }
    extractor = extractors.get(file_type, lambda f: "Unsupported file type.")
    return extractor(file)

# ------------- TRANSLATION DETECTION -------------

def detect_translation_language(prompt):
    lang_map = {
        "telugu": "te",
        "hindi": "hi",
        "tamil": "ta",
        "french": "fr",
        "spanish": "es"
    }
    prompt_lower = prompt.lower()
    for lang, code in lang_map.items():
        pattern = rf"(translate.*{lang}|in {lang}|give.*in {lang})"
        if re.search(pattern, prompt_lower):
            return code
    return None

# ------------- SESSION STATE INITIALIZATION -------------

for key in ["chat", "text", "chat_history"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "chat_history" else []

# ------------- UI HEADER -------------

st.markdown("""
<div class='bot-msg'>
👋 <strong>Hi User, how can I help you today?</strong><br>
<small>📄 If you'd like me to analyze a document, feel free to upload it below.</small>
</div>
""", unsafe_allow_html=True)

# ------------- FILE UPLOADER -------------

# ------------- FILE UPLOADER -------------
file_key = f"uploader_{st.session_state['uploader_version']}"
uploaded_file = st.file_uploader(
    label="",
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "wav", "mp3", "m4a"],
    key=file_key
)

# Process newly uploaded file (always)
if uploaded_file:
    file_ext = uploaded_file.name.split(".")[-1].lower()
    with st.spinner("⏳ Extracting content..."):
        extracted_text = extract_text(uploaded_file, file_ext)

    if isinstance(extracted_text, str) and not extracted_text.startswith("File too large"):
        st.session_state.text = extracted_text
        st.session_state.chat = model.start_chat(history=[
            {"role": "user", "parts": [f"You're an expert assistant. Here's the document:\n\n{extracted_text[:12000]}"]}
        ])
        st.session_state.chat_history = []
        st.success("✅ Document loaded. Ask me anything!")
    else:
        st.error(extracted_text)



# ------------- CHAT INTERFACE -------------

if st.session_state.text and not st.session_state.text.startswith("File too large"):
        # Show previous messages
    if st.session_state.chat_history:
        for q, a in st.session_state.chat_history:
            st.markdown(f"<div class='user-msg'>{q}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='bot-msg'>{a}</div>", unsafe_allow_html=True)

    user_query = st.chat_input("Type your question here...")

    if user_query:
        # Display user message
        st.markdown(f"<div class='user-msg'>{user_query}</div>", unsafe_allow_html=True)

        with st.spinner("🧠 Gemini is thinking..."):
            try:
                response = st.session_state.chat.send_message(user_query)
                reply_text = response.text
            except Exception as e:
                st.error(f"❌ Gemini Error: {e}")
                reply_text = "Something went wrong while processing your request."

            # Check if translation requested
            target_lang = detect_translation_language(user_query)
            if target_lang:
                reply_text = GoogleTranslator(source="auto", target=target_lang).translate(reply_text)

            # Display bot message
            st.markdown(f"<div class='bot-msg'>{reply_text}</div>", unsafe_allow_html=True)

            # If user asks for voice output, generate and play audio
            if re.search(r"(read it aloud|speak|audio|voice|say this|speak this|read this)", user_query.lower()):
                try:
                    tts = gTTS(text=reply_text, lang="en")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                        tts.save(tmp_audio.name)
                        st.audio(tmp_audio.name, format="audio/mp3")
                except Exception:
                    st.warning("⚠️ Could not generate voice output.")

            # Save chat history
            st.session_state.chat_history.append((user_query, reply_text))

# ------------- DOWNLOAD CHAT HISTORY -------------

if st.session_state.chat_history:
    chat_export = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in st.session_state.chat_history])
    st.download_button("📥 Download Chat History", data=chat_export, file_name="chat_history.txt")

# ------------- RESET BUTTON -------------

# if st.button("🔄 Reset Chat"):
#    for key in ["chat", "text", "chat_history"]:
 #       st.session_state[key] = None if key != "chat_history" else []
 #   st.success("Chat reset.")
