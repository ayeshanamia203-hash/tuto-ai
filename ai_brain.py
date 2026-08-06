# AI Brain
# ai_brain.py - AI Engine with PDF, Image & Context Support
import os
import base64
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

def encode_image(image_file):
    """Encodes image file to base64 format."""
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def ask_ai_tutor(user_question, chat_history=None, grade="General", subject="General", context_text="", image_file=None):
    """
    Routes tutoring requests to Groq.
    Uses llama-3.2-11b-vision-preview for image inputs and llama-3.3-70b-versatile for text/PDF.
    """
    try:
        dynamic_system_prompt = f"{SYSTEM_PROMPT}\n\n[STUDENT CONTEXT]\nGrade/Level: {grade}\nSubject: {subject}"
        
        # If image is uploaded, use Vision Model
        if image_file:
            base64_image = encode_image(image_file)
            
            messages = [
                {"role": "system", "content": dynamic_system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_question if user_question else "Please analyze this study material image and explain it to me."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            response = client.chat.completions.create(
                messages=messages,
                model="llama-3.2-11b-vision-preview",
            )
            return response.choices[0].message.content

        # Standard Text / PDF Processing with Llama-3.3-70b
        messages = [{"role": "system", "content": dynamic_system_prompt}]

        if chat_history:
            for msg in chat_history:
                if msg["role"] in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})

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

