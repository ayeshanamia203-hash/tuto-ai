# ============================================================
# TUTO AI - HORIZONTAL AI BRAIN
# Groq Text AI
# Smart model discovery + automatic fallback
# ============================================================

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
    client = Groq(
        api_key=GROQ_API_KEY
    )


# ============================================================
# MODEL CACHE
# ============================================================

_available_models = None


# ============================================================
# HORIZONTAL AI SYSTEM PROMPT
# ============================================================

HORIZONTAL_AI_PROMPT = """
You are Tuto AI, a general-purpose horizontal AI assistant.

Your job is to answer users naturally and directly, like a modern
general-purpose AI assistant.

IMPORTANT RESPONSE STYLE:

1. Answer the user's actual question directly.
2. Do NOT automatically organize every answer into:
   - Subject
   - Topic
   - Answer
   - Analysis
   - Explanation
   - Conclusion
   - Summary
   or similar headings.
3. Do NOT treat every question like a school assignment.
4. Do NOT automatically mention the user's subject or grade.
5. Prefer natural sentences and short paragraphs.
6. Keep simple questions simple.
7. Give detailed explanations only when the user asks for detail
   or when the question genuinely requires explanation.
8. If a list is genuinely useful, you may use bullet points.
9. If the user asks for steps, use numbered steps.
10. If the user asks for a table, comparison, code, formula, etc.,
    provide the format requested by the user.
11. Do not force everything into paragraphs if another format is
    clearly better.
12. Do not repeat the user's question unnecessarily.
13. Do not start every answer with phrases such as:
    "Sure", "Of course", "Here is the answer", or "Certainly".
14. Be conversational, clear and useful.
15. Match the user's language.
16. If the user writes Bangla/Banglish, answer naturally in Bangla
    unless the user clearly asks for English.
17. If the user asks in English, answer in English.
18. If the user mixes Bangla and English, understand the meaning
    and reply naturally in the same style when appropriate.
19. Never invent facts.
20. If you are uncertain, clearly say that you are uncertain.
21. For coding questions, give working code and explain only what
    is necessary.
22. For mathematical questions, show the calculation when useful.
23. For casual questions, respond naturally instead of using
    educational headings.
24. You are NOT limited to education. You are a general-purpose
    horizontal AI.

MOST IMPORTANT:

Think about the user's intent first.

Then choose the most natural answer format for that specific request.

Do not use a fixed answer template for every question.
"""


# ============================================================
# GET AVAILABLE GROQ MODELS
# ============================================================

def get_available_models():
    """
    Ask Groq which models are currently available.
    Result is cached during the server lifetime.
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

            model_id = getattr(
                model,
                "id",
                None
            )

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
    Create ordered list of models to try.

    Priority:
    1. Configured primary
    2. Configured fallback
    3. Strong known Groq models
    4. Other available models
    """

    available = get_available_models()

    preferred = [

        PRIMARY_GROQ_MODEL,

        FALLBACK_GROQ_MODEL,

        "openai/gpt-oss-120b",

        "openai/gpt-oss-20b",

        "llama-3.3-70b-versatile",

        "llama-3.1-8b-instant",

    ]

    result = []

    if available:

        for model_name in preferred:

            if (

                model_name

                and

                model_name in available

                and

                model_name not in result

            ):

                result.append(
                    model_name
                )

        for model_name in available:

            if model_name not in result:

                result.append(
                    model_name
                )

    else:

        for model_name in preferred:

            if (

                model_name

                and

                model_name not in result

            ):

                result.append(
                    model_name
                )

    return result


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_text_from_pdf(pdf_file):

    try:

        import pypdf

        reader = pypdf.PdfReader(
            pdf_file
        )

        text_parts = []

        for page in reader.pages:

            try:

                extracted = (
                    page.extract_text()
                )

                if extracted:

                    text_parts.append(
                        extracted
                    )

            except Exception:

                continue

        return "\n\n".join(
            text_parts
        ).strip()

    except Exception as e:

        return (
            f"PDF পড়তে সমস্যা হয়েছে: {str(e)}"
        )


# ============================================================
# AI RESPONSE CLEANER
# ============================================================

def clean_response(text):

    if not text:
        return ""

    text = str(text).strip()

    # Remove hidden thinking tags if any.
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    # Remove accidental assistant/system wrappers.
    text = re.sub(
        r"^\s*(assistant|tuto ai)\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    return text.strip()


# ============================================================
# BUILD SYSTEM PROMPT
# ============================================================

def build_system_prompt():

    base_prompt = ""

    try:

        if SYSTEM_PROMPT:

            base_prompt = str(
                SYSTEM_PROMPT
            ).strip()

    except Exception:

        base_prompt = ""

    if base_prompt:

        return (
            base_prompt
            + "\n\n"
            + HORIZONTAL_AI_PROMPT
        )

    return HORIZONTAL_AI_PROMPT


# ============================================================
# ASK GROQ
# ============================================================

def _ask_groq(messages):

    if not client:

        return (

            None,

            "GROQ_API_KEY সেট করা নেই। "
            "Render Environment Variables থেকে "
            "GROQ_API_KEY যোগ করুন।"

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

            response = (
                client
                .chat
                .completions
                .create(

                    model=model_name,

                    messages=messages,

                    temperature=DEFAULT_TEMPERATURE,

                    max_tokens=DEFAULT_MAX_TOKENS,

                )
            )

            if (

                response

                and

                response.choices

            ):

                answer = (
                    response
                    .choices[0]
                    .message
                    .content
                )

                if answer:

                    return (
                        answer,
                        None
                    )

        except Exception as e:

            errors.append(
                f"{model_name}: {str(e)}"
            )

            continue

    if errors:

        return (

            None,

            "সব available Groq model দিয়ে "
            "চেষ্টা করা হয়েছে, কিন্তু কোনো "
            "model উত্তর দিতে পারেনি.\n\n"
            + "\n".join(
                errors[-3:]
            )

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

    try:

        if not GROQ_API_KEY:

            return (
                "GROQ_API_KEY সেট করা নেই। "
                "Render Environment Variables থেকে "
                "GROQ_API_KEY যোগ করুন।"
            )

        # ----------------------------------------------------
        # SYSTEM
        # ----------------------------------------------------

        messages = [

            {
                "role": "system",
                "content": build_system_prompt()
            }

        ]

        # ----------------------------------------------------
        # CHAT HISTORY
        # ----------------------------------------------------

        if chat_history:

            recent_history = (
                chat_history[
                    -MAX_HISTORY_MESSAGES:
                ]
            )

            for message in recent_history:

                if not isinstance(
                    message,
                    dict
                ):

                    continue

                role = message.get(
                    "role"
                )

                content = message.get(
                    "content"
                )

                if role not in [
                    "user",
                    "assistant"
                ]:

                    continue

                if not content:

                    continue

                messages.append({

                    "role": role,

                    "content": str(
                        content
                    )

                })

        # ----------------------------------------------------
        # CURRENT USER MESSAGE
        # ----------------------------------------------------

        final_question = (

            str(
                user_question
            ).strip()

            if user_question

            else ""

        )

        if not final_question:

            return (
                "Please enter a message."
            )

        # ----------------------------------------------------
        # DOCUMENT CONTEXT
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

        # ----------------------------------------------------
        # ADD USER MESSAGE
        # ----------------------------------------------------

        messages.append({

            "role": "user",

            "content": final_question

        })

        # ----------------------------------------------------
        # ASK GROQ
        # ----------------------------------------------------

        answer, error = _ask_groq(
            messages
        )

        if error:

            return (
                "Tuto AI উত্তর দিতে পারেনি। "
                f"সমস্যা: {error}"
            )

        return clean_response(
            answer
        )

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
            f"\n\nDocument context:\n"
            f"{context_text}"
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

    global _available_models

    _available_models = None

    return get_available_models()
