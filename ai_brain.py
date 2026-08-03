# AI Brain
import os
from groq import Groq
from config import GROQ_API_KEY, SYSTEM_PROMPT

# Groq Client Initialization
client = Groq(api_key=GROQ_API_KEY)

def ask_ai_tutor(user_question, chat_history=None):
    """
    Routes tutoring requests to Groq (Llama 3.3 70B).
    Accepts optional chat_history list of {"role": ..., "content": ...} dicts
    for multi-turn conversation context.
    """
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Append prior conversation turns for context
        if chat_history:
            for msg in chat_history:
                if msg["role"] in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})

        # Append the current user question
        messages.append({"role": "user", "content": user_question})

        response = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error getting AI response: {str(e)}"
