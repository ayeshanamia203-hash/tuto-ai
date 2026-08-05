# AI Brain
# ai_brain.py - AI Engine with PDF & Context Support
import os
from groq import Groq
from config import GROQ_API_KEY, SYSTEM_PROMPT
from pypdf import PdfReader

# Groq Client Initialization
client = Groq(api_key=GROQ_API_KEY)

def extract_text_from_pdf(pdf_file):
    """Extracts text content from an uploaded PDF file."""
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def ask_ai_tutor(user_question, chat_history=None, grade="General", subject="General", context_text=""):
    """
    Routes tutoring requests to Groq (Llama 3.3 70B).
    Accepts grade, subject, and optional document context.
    """
    try:
        # System prompt combined with student context
        dynamic_system_prompt = f"{SYSTEM_PROMPT}\n\n[STUDENT CONTEXT]\nGrade/Level: {grade}\nSubject: {subject}"
        
        messages = [{"role": "system", "content": dynamic_system_prompt}]

        # Append prior conversation context
        if chat_history:
            for msg in chat_history:
                if msg["role"] in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})

        # Build user message with attached document context if available
        final_user_content = user_question
        if context_text:
            final_user_content = f"--- ATTACHED DOCUMENT/NOTES CONTEXT ---\n{context_text}\n---------------------------------------\n\nStudent Question: {user_question}"

        messages.append({"role": "user", "content": final_user_content})

        response = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error getting AI response: {str(e)}"
