# ai_brain.py
# Tuto AI - General Purpose AI Brain

from groq import Groq
from config import (
    GROQ_API_KEY,
    SYSTEM_PROMPT,
    PRIMARY_GROQ_MODEL,
    FALLBACK_GROQ_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    MAX_HISTORY_MESSAGES,
)


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(api_key=GROQ_API_KEY)


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_text_from_pdf(pdf_file):
    """
    Extract readable text from a PDF file.
    """

    try:
        import pypdf

        reader = pypdf.PdfReader(pdf_file)

        text_parts = []

        for page in reader.pages:
            extracted = page.extract_text()

            if extracted:
                text_parts.append(extracted)

        return "\n\n".join(text_parts).strip()

    except Exception as e:
        return f"PDF পড়তে সমস্যা হয়েছে: {str(e)}"


# ============================================================
# AI RESPONSE CLEANER
# ============================================================

def clean_response(text):
    """
    Clean unnecessary AI output.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove accidental internal-thought style tags
    import re

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    return text.strip()


# ============================================================
# MAIN TUTO AI ENGINE
# ============================================================

def ask_ai(
    user_question,
    chat_history=None,
    context_text=None,
):
    """
    Main general-purpose Tuto AI function.

    Parameters:
        user_question:
            Current user message.

        chat_history:
            Previous conversation messages.

        context_text:
            Optional document/PDF context.
    """

    try:

        if not GROQ_API_KEY:
            return "GROQ_API_KEY সেট করা নেই। Render Environment Variables থেকে API key যোগ করুন।"

        # ----------------------------------------------------
        # Prepare messages
        # ----------------------------------------------------

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        # ----------------------------------------------------
        # Add conversation history
        # ----------------------------------------------------

        if chat_history:

            # Keep only recent messages
            recent_history = chat_history[-MAX_HISTORY_MESSAGES:]

            for message in recent_history:

                if not isinstance(message, dict):
                    continue

                role = message.get("role")
                content = message.get("content")

                if role not in ["user", "assistant"]:
                    continue

                if not content:
                    continue

                messages.append(
                    {
                        "role": role,
                        "content": str(content)
                    }
                )

        # ----------------------------------------------------
        # Build current user message
        # ----------------------------------------------------

        final_question = user_question.strip()

        if context_text:

            final_question = f"""
The user provided the following document context:

--- DOCUMENT CONTEXT ---
{context_text[:12000]}
--- END DOCUMENT CONTEXT ---

User's request:

{user_question}
"""

        messages.append(
            {
                "role": "user",
                "content": final_question
            }
        )

        # ----------------------------------------------------
        # Try primary model
        # ----------------------------------------------------

        response = None
        last_error = ""

        models_to_try = [
            PRIMARY_GROQ_MODEL,
            FALLBACK_GROQ_MODEL
        ]

        for model_name in models_to_try:

            try:

                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=DEFAULT_TEMPERATURE,
                    max_tokens=DEFAULT_MAX_TOKENS,
                )

                if response and response.choices:
                    break

            except Exception as e:
                last_error = str(e)
                response = None

        # ----------------------------------------------------
        # Check response
        # ----------------------------------------------------

        if not response or not response.choices:

            return f"Tuto AI উত্তর দিতে পারেনি। সমস্যা: {last_error}"

        answer = response.choices[0].message.content

        return clean_response(answer)

    except Exception as e:

        return f"Tuto AI-তে একটি সমস্যা হয়েছে: {str(e)}"


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def ask_ai_tutor(
    user_question,
    chat_history=None,
    grade=None,
    subject=None,
    context_text=None,
    image_file=None,
):
    """
    Compatibility wrapper.

    পুরোনো app.py যদি ask_ai_tutor() ব্যবহার করে,
    তাহলেও application পুরোপুরি ভেঙে যাবে না।

    Grade/Subject এখন optional context হিসেবে ব্যবহার করা হচ্ছে।
    """

    extra_context = ""

    if grade:
        extra_context += f"\nUser level/context: {grade}"

    if subject:
        extra_context += f"\nSubject/context: {subject}"

    if context_text:
        extra_context += f"\n\nDocument context:\n{context_text}"

    return ask_ai(
        user_question=user_question,
        chat_history=chat_history,
        context_text=extra_context.strip() if extra_context else None,
    )
