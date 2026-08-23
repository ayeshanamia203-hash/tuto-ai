# main.py
# Tuto AI - Groq Text + Gemini Vision + Groq Whisper

import io
import os
import re
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse
from groq import Groq
import google.generativeai as genai
import uvicorn

from ai_brain import ask_ai
from config import GROQ_API_KEY, GEMINI_API_KEY


# ============================================================
# APP CONFIGURATION
# ============================================================

app = FastAPI(
    title="Tuto AI",
    description="Tuto AI - General Purpose AI",
    version="4.0.0"
)


# ============================================================
# API CLIENTS
# ============================================================

groq_client = None

if GROQ_API_KEY:
    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

if GEMINI_API_KEY:
    genai.configure(
        api_key=GEMINI_API_KEY
    )


# Gemini vision models
GEMINI_VISION_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]


# ============================================================
# CHAT MEMORY
# ============================================================

chat_sessions = {}


# ============================================================
# CLEAN AI RESPONSE
# ============================================================

def clean_ai_response(text: str) -> str:

    if not text:
        return ""

    # Remove hidden thinking tags if any model returns them
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    return text.strip()


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(contents: bytes) -> str:

    try:

        import pypdf

        reader = pypdf.PdfReader(
            io.BytesIO(contents)
        )

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n\n".join(
            pages
        ).strip()

    except Exception as e:

        return (
            f"Unable to extract PDF text: {str(e)}"
        )


# ============================================================
# SESSION FUNCTIONS
# ============================================================

def get_session_history(session_id: str):

    if session_id not in chat_sessions:

        chat_sessions[session_id] = []

    return chat_sessions[session_id]


def save_message(
    session_id: str,
    role: str,
    content: str
):

    if session_id not in chat_sessions:

        chat_sessions[session_id] = []

    chat_sessions[session_id].append({

        "role": role,

        "content": content

    })

    # Keep last 40 messages
    chat_sessions[session_id] = (
        chat_sessions[session_id][-40:]
    )


# ============================================================
# FRONTEND
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
async def home():

    try:

        base_dir = (
            Path(__file__).resolve().parent
        )

        index_file = (
            base_dir / "index.html"
        )

        # Fallback to current directory
        if not index_file.exists():

            current_file = (
                Path.cwd() / "index.html"
            )

            if current_file.exists():

                index_file = current_file

            else:

                return HTMLResponse(

                    f"""
                    <html>

                    <body style="
                        background:#131314;
                        color:white;
                        font-family:Arial;
                        padding:40px;
                    ">

                        <h2>
                            Tuto AI frontend not found.
                        </h2>

                        <p>
                            Expected:
                        </p>

                        <code>
                            {index_file}
                        </code>

                    </body>

                    </html>
                    """,

                    status_code=500
                )

        html = index_file.read_text(
            encoding="utf-8"
        )

        return HTMLResponse(
            content=html,
            status_code=200
        )

    except Exception as e:

        return HTMLResponse(

            f"""
            <html>

            <body style="
                background:#131314;
                color:white;
                font-family:Arial;
                padding:40px;
            ">

                <h2>
                    Tuto AI Frontend Error
                </h2>

                <p>
                    {str(e)}
                </p>

            </body>

            </html>
            """,

            status_code=500
        )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():

    return {

        "status": "ok",

        "service": "Tuto AI",

        "text_ai": "Groq / ai_brain",

        "vision": "Google Gemini",

        "voice": "Groq Whisper"

    }


# ============================================================
# VOICE TRANSCRIPTION
# ============================================================

@app.post("/api/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...)
):

    try:

        if not GROQ_API_KEY or not groq_client:

            return {

                "status": "error",

                "message":
                    "GROQ_API_KEY missing."

            }

        audio_content = await audio.read()

        if not audio_content:

            return {

                "status": "error",

                "message":
                    "Audio file is empty."

            }

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        ) as temp_audio:

            temp_audio.write(
                audio_content
            )

            temp_audio_path = (
                temp_audio.name
            )

        try:

            with open(
                temp_audio_path,
                "rb"
            ) as audio_file:

                transcription = (
                    groq_client
                    .audio
                    .transcriptions
                    .create(

                        file=(

                            os.path.basename(
                                temp_audio_path
                            ),

                            audio_file.read()

                        ),

                        model="whisper-large-v3",

                        response_format="json"

                    )
                )

            return {

                "status": "success",

                "text":
                    transcription.text

            }

        finally:

            if os.path.exists(
                temp_audio_path
            ):

                os.remove(
                    temp_audio_path
                )

    except Exception as e:

        return {

            "status": "error",

            "message": str(e)

        }


# ============================================================
# SMART CHAT TITLE
# ============================================================

@app.post("/api/generate-title")
async def generate_title(
    request: Request
):

    try:

        # Accept JSON from frontend
        # and also support form data.

        prompt = ""

        content_type = (
            request.headers
            .get("content-type", "")
            .lower()
        )

        if "application/json" in content_type:

            body = await request.json()

            prompt = str(
                body.get("prompt", "")
            )

        else:

            form = await request.form()

            prompt = str(
                form.get("prompt", "")
            )

        prompt = prompt.strip()

        if not prompt:

            return {

                "status": "success",

                "title": "New Chat"

            }

        if not GROQ_API_KEY or not groq_client:

            return {

                "status": "success",

                "title": "New Chat"

            }

        title_prompt = f"""
Create a short 2-5 word title for this conversation.

User message:
{prompt}

Rules:
- Output ONLY the title.
- 2-5 words.
- No quotation marks.
- No explanation.
- No punctuation at the end.
"""

        completion = (
            groq_client
            .chat
            .completions
            .create(

                model="openai/gpt-oss-20b",

                messages=[

                    {
                        "role": "user",

                        "content":
                            title_prompt

                    }

                ],

                max_completion_tokens=20,

                temperature=0.3

            )
        )

        title = (
            completion
            .choices[0]
            .message
            .content
            or "New Chat"
        ).strip()

        title = title.replace(
            '"',
            ""
        )

        title = title.replace(
            "'",
            ""
        )

        title = title.replace(
            "\n",
            " "
        )

        return {

            "status": "success",

            "title":
                title[:80]

        }

    except Exception:

        return {

            "status": "success",

            "title": "New Chat"

        }


# ============================================================
# GEMINI IMAGE AI
# ============================================================

async def analyze_image(
    question: str,
    image_bytes: bytes,
    mime_type: str
):

    if not GEMINI_API_KEY:

        return (

            None,

            "GEMINI_API_KEY missing."

        )

    if not image_bytes:

        return (

            None,

            "Image file is empty."

        )

    # 10 MB safety limit
    if len(image_bytes) > 10 * 1024 * 1024:

        return (

            None,

            "Image is too large. "
            "Please upload a smaller image."

        )

    try:

        user_question = (
            question.strip()
        )

        if not user_question:

            user_question = (
                "Briefly describe what "
                "is visible in this image."
            )


        # ====================================================
        # GEMINI IMAGE PROMPT
        # ====================================================

        prompt = f"""
You are Tuto AI, a helpful general-purpose AI assistant.

Look at the provided image and answer the user's request.

USER REQUEST:
{user_question}

IMPORTANT RESPONSE RULES:

1. Answer the user's actual question directly.

2. Keep the answer concise and natural.

3. If the user asks a simple question, give a simple
   answer. Do NOT automatically perform a long image analysis.

4. For a simple question, normally answer in 1-3 short
   sentences.

5. Only give a detailed visual analysis when the user
   specifically asks for detailed analysis.

6. Do not create unnecessary sections such as:
   "Analyze the visual cues", "Subject", "Background",
   "Clothing", etc. unless the user asks for that.

7. Do not repeat the user's question.

8. Only mention things that can reasonably be observed
   in the image.

9. Never invent details.

10. If something cannot be determined reliably from the
    image, say that it cannot be determined with certainty.

11. Do not identify a real person's name or identity from
    the image.

12. For sensitive or uncertain characteristics, do not state
    guesses as facts.

13. If the user asks whether the person appears to be a
    boy or girl, do not claim certainty from appearance alone.
    If useful, say that the person's gender cannot be reliably
    determined from the image.

14. Match the user's language.
    If the user asks in Bangla, answer in Bangla.
    If the user asks in English, answer in English.

15. Do not reveal hidden reasoning or chain-of-thought.

16. Do not use long essays unless specifically requested.

USER'S QUESTION:
{user_question}
"""


        image_part = {

            "mime_type":
                mime_type,

            "data":
                image_bytes

        }


        last_error = ""


        # ====================================================
        # TRY GEMINI MODELS
        # ====================================================

        for model_name in GEMINI_VISION_MODELS:

            try:

                model = (
                    genai
                    .GenerativeModel(
                        model_name
                    )
                )

                response = (
                    model
                    .generate_content(
                        [
                            prompt,
                            image_part
                        ]
                    )
                )


                if (
                    response
                    and
                    getattr(
                        response,
                        "text",
                        None
                    )
                ):

                    answer = (
                        response
                        .text
                        .strip()
                    )

                    return (

                        clean_ai_response(
                            answer
                        ),

                        None

                    )

            except Exception as e:

                last_error = str(e)


        return (

            None,

            (
                "Gemini vision error: "
                f"{last_error}"
            )

        )

    except Exception as e:

        return (

            None,

            str(e)

        )


# ============================================================
# MAIN CHAT API
# ============================================================

@app.post("/api/chat")
async def chat_endpoint(

    question: str = Form(""),

    session_id: str = Form("default"),

    grade: str = Form(""),

    subject: str = Form(""),

    file: UploadFile = File(None)

):

    try:

        question = question.strip()

        history = get_session_history(
            session_id
        )


        # ====================================================
        # FILE HANDLING
        # ====================================================

        if file and file.filename:

            filename = (
                file.filename.lower()
            )

            file_contents = (
                await file.read()
            )


            # =================================================
            # PDF
            # =================================================

            if (

                filename.endswith(".pdf")

                or

                file.content_type
                == "application/pdf"

            ):

                extracted_text = (
                    extract_pdf_text(
                        file_contents
                    )
                )

                if not extracted_text:

                    return {

                        "status": "error",

                        "message":
                            "PDF থেকে কোনো "
                            "readable text "
                            "পাওয়া যায়নি।"

                    }


                user_question = (

                    question

                    or

                    "Please analyze this document "
                    "and summarize the most important "
                    "information."

                )


                document_context = (

                    f"User uploaded a PDF named: "
                    f"{file.filename}\n\n"

                    f"Document content:\n"
                    f"{extracted_text[:12000]}"

                )


                if grade:

                    document_context += (

                        f"\n\nUser level/context: "
                        f"{grade}"

                    )


                if subject:

                    document_context += (

                        f"\nSubject/context: "
                        f"{subject}"

                    )


                response = ask_ai(

                    user_question=
                        user_question,

                    chat_history=
                        history,

                    context_text=
                        document_context

                )


                response = clean_ai_response(
                    response
                )


                save_message(

                    session_id,

                    "user",

                    (
                        f"[PDF: {file.filename}] "
                        f"{user_question}"
                    )

                )


                save_message(

                    session_id,

                    "assistant",

                    response

                )


                return {

                    "status": "success",

                    "question":
                        user_question,

                    "response":
                        response

                }


            # =================================================
            # IMAGE
            # =================================================

            if (

                file.content_type

                and

                file.content_type.startswith(
                    "image/"
                )

            ):

                user_question = (

                    question

                    or

                    "Briefly describe what "
                    "is visible in this image."

                )


                image_response, error = (
                    await analyze_image(

                        user_question,

                        file_contents,

                        file.content_type

                    )
                )


                if error:

                    return {

                        "status": "error",

                        "message":
                            error

                    }


                save_message(

                    session_id,

                    "user",

                    (
                        f"[Image: {file.filename}] "
                        f"{user_question}"
                    )

                )


                save_message(

                    session_id,

                    "assistant",

                    image_response

                )


                return {

                    "status": "success",

                    "question":
                        user_question,

                    "response":
                        image_response

                }


            # =================================================
            # UNSUPPORTED FILE
            # =================================================

            return {

                "status": "error",

                "message":
                    "Unsupported file type."

            }


        # ====================================================
        # NORMAL TEXT CHAT
        # ====================================================

        if not question:

            return {

                "status": "error",

                "message":
                    "Please enter a message."

            }


        contextual_question = (
            question
        )


        if grade:

            contextual_question += (

                f"\n\n"
                f"[Optional user context: "
                f"{grade}]"

            )


        if subject:

            contextual_question += (

                f"\n"
                f"[Optional subject context: "
                f"{subject}]"

            )


        response = ask_ai(

            user_question=
                contextual_question,

            chat_history=
                history

        )


        response = clean_ai_response(
            response
        )


        save_message(

            session_id,

            "user",

            question

        )


        save_message(

            session_id,

            "assistant",

            response

        )


        return {

            "status": "success",

            "question":
                question,

            "response":
                response

        }


    except Exception as e:

        return {

            "status": "error",

            "message":
                str(e)

        }


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":

    port = int(

        os.environ.get(
            "PORT",
            8000
        )

    )

    uvicorn.run(

        app,

        host="0.0.0.0",

        port=port

    )
