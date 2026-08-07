import os
import pypdf
from groq import Groq
from config import GROQ_API_KEY, SYSTEM_PROMPT

client = Groq(api_key=GROQ_API_KEY)

def extract_text_from_pdf(pdf_file):
    try:
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        return f"PDF পড়তে সমস্যা হয়েছে: {str(e)}"

def ask_ai_tutor(messages_history):
    try:
        formatted_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        formatted_messages.extend(messages_history)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=formatted_messages,
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI উত্তর দিতে পারেনি: {str(e)}"
