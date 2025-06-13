# 🧠 Universal Intelligent Document Processing (IDP) Chatbot

A **multimodal AI-powered assistant** that can read, analyze, and interact with **PDFs, Word docs, images, and audio files** — powered by **Google Gemini Pro** and built with **Streamlit**.

## 🔍 Overview
This chatbot understands and interacts with unstructured content using advanced AI models and NLP pipelines. Upload any file type (text, image, audio, doc), ask questions, and get instant answers with voice output, multilingual support, and document memory.

## 🚀 Key Features

✅ Analyze PDFs, DOCX, images, and audio files  
✅ Real-time Q&A using Google Gemini Pro (via `google.generativeai`)  
✅ OCR (Tesseract) for scanned images  
✅ Speech-to-Text using Google Speech Recognition  
✅ Translate any language (Deep Translator)  
✅ Text-to-Speech (gTTS) for accessibility  
✅ Responsive chat interface using Streamlit + Custom CSS  
✅ Supports file sizes up to 10MB+ with session persistence

## 🧰 Tech Stack

- **LLM**: Google Gemini Pro (`google.generativeai`)
- **Frontend**: Streamlit with custom CSS styling
- **OCR**: Tesseract (PyTesseract)
- **Speech Recognition**: Google Speech Recognition API
- **TTS**: gTTS (Google Text-to-Speech)
- **Translation**: Deep Translator
- **Languages**: Python, HTML, CSS

## 💡 Use Cases

- Reading and querying scanned government forms or invoices  
- Converting audio meeting recordings into interactive summaries  
- Multilingual document analysis for global accessibility  
- GenAI for research or academic paper review


## 📦 Setup Instructions

```bash
git clone https://github.com/KEERTHANANAMULAMETU/universal-idp-chatbot.git
cd universal-idp-chatbot
pip install -r requirements.txt
streamlit run app.py
