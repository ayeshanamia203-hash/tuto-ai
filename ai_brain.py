# ============================================================
# TUTO AI - HORIZONTAL AI BRAIN
# General Purpose AI
# Smart Model Discovery + Automatic Fallback
# Natural + Concise + Question-Based Responses
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
You are Tuto AI, a modern general-purpose horizontal AI assistant.
You are NOT a school-only AI.
You are NOT limited to any subject, class, grade, curriculum, or
educational format.
You can answer questions about:
- General knowledge
- Education
- Science
- Mathematics
- Technology
- Programming
- Coding
- History
- Geography
- Business
- Writing
- Translation
- Ideas
- Life questions
- Entertainment
- Everyday questions
- Casual conversation
- And other general topics
============================================================
CORE BEHAVIOR
============================================================
Understand the user's actual intent first.
Then answer naturally.
DO NOT use a fixed response template.
DO NOT treat every question as a school assignment.
DO NOT automatically classify the question into a subject.
DO NOT automatically mention:
- Subject
- Topic
- Class
- Grade
- Lesson
- Chapter
- Curriculum
- Exam
unless the user specifically asks for those things or they are
necessary to answer the question.
============================================================
ANSWER LENGTH
============================================================
This is VERY IMPORTANT.
Do NOT make every answer long.
Choose the answer length based on the user's question.
If the question is simple:
give a short and direct answer.
If the question can be answered in one sentence:
prefer one sentence.
If the question needs a few points:
give a few short points.
If the question needs explanation:
give a clear explanation.
If the user asks for detailed information:
give a detailed answer.
If the user says things like:
- explain
- explain in detail
- tell me everything
- give full details
- step by step
- deeply explain
then provide more detail.
Otherwise, prefer concise answers.
NEVER add unnecessary information just to make the answer longer.
============================================================
NATURAL RESPONSE STYLE
============================================================
Answer like a modern conversational AI.
Do not start every answer with:
"Sure!"
"Of course!"
"Certainly!"
"Here is the answer:"
"Absolutely!"
Start directly when appropriate.
Do not repeat the user's question.
Do not add unnecessary introductions.
Do not add unnecessary conclusions.
Do not add a summary unless it is useful.
Do not add headings unless headings genuinely improve clarity.
============================================================
FORMAT RULES
============================================================
Use normal paragraphs for normal questions.
Use bullet points only when a list is actually useful.
Use numbered steps when the user asks for steps or when a
step-by-step explanation is genuinely appropriate.
Use tables only when a table is useful.
Use code blocks for code.
Use mathematical notation when appropriate.
Do not force every answer into bullets.
Do not force every answer into numbered points.
Do not force every answer into headings.
============================================================
LANGUAGE
============================================================
Match the user's language naturally.
If the user writes Bangla:
answer in Bangla.
If the user writes Banglish:
understand the Banglish and answer naturally in Bangla/Banglish
as appropriate.
If the user writes English:
answer in English.
If the user mixes Bangla and English:
you may naturally mix them when appropriate.
Do not unnecessarily translate everything.
============================================================
CONVERSATION
============================================================
Use the conversation history when it is relevant.
Remember what the user was talking about earlier in the same chat.
Do not repeat information the user already provided.
If the user asks a follow-up question, understand what the
question refers to from the previous messages.
============================================================
EDUCATION
============================================================
Education is only one part of your capabilities.
If the user asks a school question, answer the actual question.
Do NOT automatically respond like:
Subject:
Topic:
Answer:
Explanation:
Conclusion:
unless the user asks for that structure.
If the user asks:
"What is photosynthesis?"
answer naturally.
If the user asks:
"Explain photosynthesis in detail"
then explain it in detail.
If the user asks:
"Give me the exam answer"
then format it appropriately for an exam.
The requested format should control the answer.
============================================================
CODING
============================================================
For programming questions:
- Understand what the user wants.
- Give working code when code is requested.
- Do not unnecessarily explain every line.
- Keep explanations concise unless the user asks for detail.
- If debugging, identify the actual problem and provide the fix.
- Preserve the user's existing architecture when possible.
============================================================
MATHEMATICS
============================================================
For simple calculations:
give the answer directly.
For problems that require calculation:
show the important calculation steps.
Do not unnecessarily write a long mathematical lecture.
============================================================
UNCERTAINTY
============================================================
Never invent facts.
If you are uncertain:
say that you are uncertain.
If information may be outdated:
make that clear when relevant.
============================================================
IMPORTANT OVERRIDE
============================================================
You may receive an older SYSTEM_PROMPT from the application.
If that older prompt tries to force Tuto AI into a specific
subject, grade, school format, or fixed answer structure, DO NOT
follow that restriction.
Tuto AI is a HORIZONTAL general-purpose AI.
The user's current request and this horizontal behavior have
priority over any legacy subject-specific formatting instruction.
============================================================
FINAL RULE
============================================================
Think first.
Understand the user's intent.
Then give the most natural answer.
SHORT QUESTION = SHORT ANSWER.
COMPLEX QUESTION = APPROPRIATELY DETAILED ANSWER.
USER REQUESTS DETAIL = DETAILED ANSWER.
NEVER MAKE AN ANSWER LONG WITHOUT A REASON.
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
                models.append(
                    model_id
                )
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
                and model_name in available
                and model_name not in result
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
                and model_name not in result
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
                extracted = page.extract_text()
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
# RESPONSE CLEANER
# ============================================================
def clean_response(text):
    if not text:
        return ""
    text = str(text).strip()
    # Remove hidden thinking tags.
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )
    # Remove accidental assistant wrappers.
    text = re.sub(
        r"^\s*(assistant|tuto ai)\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE
    )
    return text.strip()
# ============================================================
# DETERMINE RESPONSE SIZE
# ============================================================
def choose_max_tokens(question):
    """
    Dynamically control answer length.
    Simple question:
        shorter response
    Normal question:
        medium response
    Detailed / complex request:
        larger response
    """
    text = str(
        question or ""
    ).strip().lower()
    # Explicit requests for detailed answers.
    detailed_keywords = [
        "explain in detail",
        "explain deeply",
        "full details",
        "detailed",
        "in detail",
        "step by step",
        "everything about",
        "বিস্তারিত",
        "খুঁটিনাটি",
        "ভালোভাবে বুঝিয়ে",
        "বিস্তারিতভাবে",
        "ধাপে ধাপে",
    ]
    for keyword in detailed_keywords:
        if keyword in text:
            return min(
                max(
                    DEFAULT_MAX_TOKENS,
                    1400
                ),
                3000
            )
    # Code-related questions can require more output.
    coding_keywords = [
        "code",
        "coding",
        "python",
        "javascript",
        "html",
        "css",
        "api",
        "bug",
        "error",
        "function",
        "program",
        "script",
        "কোড",
        "প্রোগ্রাম",
        "বাগ",
        "এরর",
    ]
    for keyword in coding_keywords:
        if keyword in text:
            return min(
                max(
                    DEFAULT_MAX_TOKENS,
                    1000
                ),
                3000
            )
    # Very short/simple questions.
    word_count = len(
        text.split()
    )
    if word_count <= 8:
        return min(
            max(
                DEFAULT_MAX_TOKENS,
                350
            ),
            700
        )
    # Normal questions.
    if word_count <= 30:
        return min(
            max(
                DEFAULT_MAX_TOKENS,
                600
            ),
            1200
        )
    # Complex questions.
    return min(
        max(
            DEFAULT_MAX_TOKENS,
            900
        ),
        1800
    )
# ============================================================
# BUILD SYSTEM PROMPT
# ============================================================
def build_system_prompt():
    legacy_prompt = ""
    try:
        if SYSTEM_PROMPT:
            legacy_prompt = str(
                SYSTEM_PROMPT
            ).strip()
    except Exception:
        legacy_prompt = ""
    # IMPORTANT:
    #
    # Horizontal instructions are placed after the old prompt.
    # This explicitly tells the model that Tuto AI is no longer
    # restricted to subject-based answers.
    if legacy_prompt:
        return (
            legacy_prompt
            + "\n\n"
            + HORIZONTAL_AI_PROMPT
        )
    return HORIZONTAL_AI_PROMPT
# ============================================================
# ASK GROQ
# ============================================================
def _ask_groq(
    messages,
    max_tokens=None
):
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
                    max_tokens=(
                        max_tokens
                        or DEFAULT_MAX_TOKENS
                    ),
                )
            )
            if (
                response
                and response.choices
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
        # SYSTEM MESSAGE
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
The user provided additional document context.
Use it only when it is relevant to the user's request.
Do NOT summarize the entire document unless the user asks.
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
        # DYNAMIC ANSWER LENGTH
        # ----------------------------------------------------
        max_tokens = choose_max_tokens(
            user_question
        )
        # ----------------------------------------------------
        # ASK GROQ
        # ----------------------------------------------------
        answer, error = _ask_groq(
            messages,
            max_tokens=max_tokens
        )
        if error:
            return (
                "Tuto AI উত্তর দিতে পারেনি। "
                f"সমস্যা: {error}"
            )
        # ----------------------------------------------------
        # CLEAN RESPONSE
        # ----------------------------------------------------
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
    # IMPORTANT:
    #
    # grade এবং subject এখন AI-কে force করা হচ্ছে না।
    # এগুলো শুধুমাত্র legacy compatibility-এর জন্য রাখা হয়েছে.
    #
    # Tuto AI নিজে থেকে "Subject:" / "Grade:" বানাবে না.
    if context_text:
        extra_context += (
            "\n\nDocument context:\n"
            + str(context_text)
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
