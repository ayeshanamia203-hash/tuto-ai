# ai_brain.py
# Tuto AI - General Purpose AI Brain
# Smart Groq model discovery + automatic fallback

import re
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

client = None

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)


# ============================================================
# MODEL CACHE
# ============================================================

_available_models = None


# ============================================================
# GET AVAILABLE GROQ MODELS
# ============================================================

def get_available_models():
    """
    Ask Groq which models are currently available.

    The result is cached so we don't request the model list
    on every single user message.
    """

    global _available_models

    if _available_models is not None:
        return _available_models

    if not client:
        return []

    try:
        model_list = client.models.list()

        models = []

        for model in model_list.data:

            model_id = getattr(model, "id", None)

            if model_id:
                models.append(model_id)

        _available_models = models

        return models

    except Exception:
        return []


# ============================================================
# CHOOSE BEST AVAILABLE MODEL
# ============================================================

def choose_models():
    """
    Create an ordered list of models to try.

    Priority:
        1. Configured primary model
        2. Configured fallback model
        3. Other currently available Groq models
    """

    available = get_available_models()

    preferred = [
        PRIMARY_GROQ_MODEL,
        FALLBACK_GROQ_MODEL,

        # Known strong/general-purpose models.
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.1-8b-instant",
    ]

    result = []

    # First add configured/preferred models
    # only if Groq says they currently exist.
    if available:

        for model_name in preferred:

            if (
                model_name
                and model_name in available
                and model_name not in result
            ):
                result.append(model_name)

        # Then add any other available models.
        for model_name in available:

            if model_name not in result:
                result.append(model_name)

    else:
        # If model listing itself fails,
        # still try configured models.
        for model_name in preferred:

            if model_name and model_name not in result:
                result.append(model_name)

    return result


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

    text = str(text).strip()

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    return text.strip()


# ============================================================
# ASK GROQ
# ============================================================

def _ask_groq(messages):
    """
    Send the request to Groq using automatically selected models.

    If one model fails, another available model is tried.
    """

    if not client:

        return (
            None,
            "GROQ_API_KEY সেট করা নেই। "
            "Render Environment Variables থেকে GROQ_API_KEY যোগ করুন।"
        )

    models_to_try = choose_models()

    if not models_to_try:

        return (
            None,
            "Groq-এর কোনো available model পাওয়া যায়নি।"
        )

    errors = []

    for model_name in models_to_try:

        try:

            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=DEFAULT_MAX_TOKENS,
            )

            if response and response.choices:

                answer = response.choices[0].message.content

                if answer:

                    return answer, None

        except Exception as e:

            error_text = str(e)

            errors.append(
                f"{model_name}: {error_text}"
            )

            # If this model is invalid/deleted,
            # simply continue to the next model.
            continue

    # --------------------------------------------------------
    # All models failed
    # --------------------------------------------------------

    if errors:

        return (
            None,
            "সব available Groq model দিয়ে চেষ্টা করা হয়েছে, "
            "কিন্তু কোনো model উত্তর দিতে পারেনি.\n\n"
            + "\n".join(errors[-3:])
        )

    return (
        None,
        "Groq কোনো response দিতে পারেনি।"
    )


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
    """

    try:

        if not GROQ_API_KEY:

            return (
                "GROQ_API_KEY সেট করা নেই। "
                "Render Environment Variables থেকে "
                "GROQ_API_KEY যোগ করুন।"
            )

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
        # Conversation history
        # ----------------------------------------------------

        if chat_history:

            recent_history = (
                chat_history[-MAX_HISTORY_MESSAGES:]
            )

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
        # Current user message
        # ----------------------------------------------------

        final_question = (
            str(user_question).strip()
            if user_question
            else ""
        )

        if not final_question:

            return "Please enter a message."

        # ----------------------------------------------------
        # Document/PDF context
        # ----------------------------------------------------

        if context_text:

            final_question = f"""
The user provided the following document context.

--- DOCUMENT CONTEXT ---
{str(context_text)[:12000]}
--- END DOCUMENT CONTEXT ---

User's request:

{final_question}
"""

        messages.append(
            {
                "role": "user",
                "content": final_question
            }
        )

        # ----------------------------------------------------
        # Ask Groq
        # ----------------------------------------------------

        answer, error = _ask_groq(messages)

        if error:

            return (
                "Tuto AI উত্তর দিতে পারেনি। "
                f"সমস্যা: {error}"
            )

        return clean_response(answer)

    except Exception as e:

        return (
            f"Tuto AI-তে একটি সমস্যা হয়েছে: {str(e)}"
        )


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

    পুরোনো application যদি ask_ai_tutor() ব্যবহার করে,
    তাহলেও কাজ করবে।
    """

    extra_context = ""

    if grade:

        extra_context += (
            f"\nUser level/context: {grade}"
        )

    if subject:

        extra_context += (
            f"\nSubject/context: {subject}"
        )

    if context_text:

        extra_context += (
            f"\n\nDocument context:\n{context_text}"
        )

    return ask_ai(
        user_question=user_question,
        chat_history=chat_history,
        context_text=(
            extra_context.strip()
            if extra_context
            else None
        ),
    )


# ============================================================
# REFRESH MODEL CACHE
# ============================================================

def refresh_models():
    """
    Force Tuto AI to check Groq models again.

    Useful if Groq adds/removes models while the server
    is running.
    """

    global _available_models

    _available_models = None

    return get_available_models()
