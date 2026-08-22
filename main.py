# main.py
# Tuto AI - Horizontal AI Backend

import io
import os
import tempfile
import re
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
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
    description="Tuto AI - General Purpose Horizontal AI",
    version="2.0.0"
)


# ============================================================
# API CLIENTS
# ============================================================

groq_client = None

if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# ============================================================
# CHAT MEMORY
# ============================================================

chat_sessions = {}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clean_ai_response(text: str) -> str:
    if not text:
        return ""

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    return text.strip()


def extract_pdf_text(contents: bytes) -> str:
    try:
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(contents))
        pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n\n".join(pages).strip()

    except Exception as e:
        return f"Unable to extract PDF text: {str(e)}"


def get_session_history(session_id: str):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    return chat_sessions[session_id]


def save_message(session_id: str, role: str, content: str):

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    chat_sessions[session_id].append({
        "role": role,
        "content": content
    })

    # Maximum 40 messages = approximately 20 turns
    chat_sessions[session_id] = chat_sessions[session_id][-40:]


# ============================================================
# FRONTEND
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def home():

    """
    Serve index.html from the same directory as main.py.
    """

    try:

        # Get the exact directory where main.py is located
        base_dir = Path(__file__).resolve().parent

        # Expected frontend location
        index_file = base_dir / "index.html"

        # Debug-friendly fallback
        if not index_file.exists():

            # Also check current working directory
            current_file = Path.cwd() / "index.html"

            if current_file.exists():
                index_file = current_file

            else:

                return HTMLResponse(
                    content=f"""
                    <html>
                    <body style="
                        background:#131314;
                        color:white;
                        font-family:Arial;
                        padding:40px;
                    ">
                        <h2>Tuto AI frontend (index.html) not found.</h2>
                        <p>Expected location:</p>
                        <code>{index_file}</code>
                        </body>
                    </html>
                    """,
                    status_code=500
                )

        # Read frontend
        html = index_file.read_text(
            encoding="utf-8"
        )

        return HTMLResponse(
            content=html,
            status_code=200
        )

    except Exception as e:

        return HTMLResponse(
            content=f"""
            <html>
            <body style="
                background:#131314;
                color:white;
                font-family:Arial;
                padding:40px;
            ">
                <h2>Tuto AI Frontend Error</h2>
                <p>{str(e)}</p>
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
        "type": "horizontal_ai"
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
                "message": "GROQ_API_KEY missing."
            }

        audio_content = await audio.read()

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        ) as temp_audio:

            temp_audio.write(audio_content)
            temp_audio_path = temp_audio.name

        try:

            with open(
                temp_audio_path,
                "rb"
            ) as audio_file:

                transcription = groq_client.audio.transcriptions.create(
                    file=(
                        os.path.basename(temp_audio_path),
                        audio_file.read()
                    ),
                    model="whisper-large-v3",
                    response_format="json"
                )

            return {
                "status": "success",
                "text": transcription.text
            }

        finally:

            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

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
    prompt: str = Form(...)
):

    try:

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
- No quotation marks.
- No explanation.
- No punctuation at the end.
"""

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": title_prompt
                }
            ],
            max_tokens=20,
            temperature=0.3
        )

        title = completion.choices[0].message.content.strip()

        title = title.replace('"', "")
        title = title.replace("'", "")

        return {
            "status": "success",
            "title": title
        }

    except Exception:

        return {
            "status": "success",
            "title": "New Chat"
        }


# ============================================================
# IMAGE AI
# ============================================================

async def analyze_image(
    question: str,
    image_bytes: bytes,
    mime_type: str
):

    if not GEMINI_API_KEY:
        return None, "GEMINI_API_KEY missing."

    try:

        prompt = f"""
You are Tuto AI, a general-purpose AI assistant.

Analyze the image carefully and answer the user's request.

User request:
{question if question else "Describe and analyze this image helpfully."}

Rules:
- Answer directly.
- Do not reveal hidden reasoning.
- Do not invent information that cannot be seen.
- Match the user's language.
"""

        image_part = {
            "mime_type": mime_type,
            "data": image_bytes
        }

        preferred_models = [
            "gemini-2.0-flash",
            "gemini-1.5-flash"
        ]

        last_error = ""

        for model_name in preferred_models:

            try:

                model = genai.GenerativeModel(
                    model_name
                )

                response = model.generate_content([
                    prompt,
                    image_part
                ])

                if response and response.text:

                    return (
                        clean_ai_response(response.text),
                        None
                    )

            except Exception as e:

                last_error = str(e)

        return (
            None,
            f"Gemini vision error: {last_error}"
        )

    except Exception as e:

        return None, str(e)


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

        # ----------------------------------------------------
        # SESSION
        # ----------------------------------------------------

        history = get_session_history(session_id)

        # ----------------------------------------------------
        # FILE HANDLING
        # ----------------------------------------------------

        if file and file.filename:

            filename = file.filename.lower()
            file_contents = await file.read()

            # =================================================
            # PDF
            # =================================================

            if (
                filename.endswith(".pdf")
                or file.content_type == "application/pdf"
            ):

                extracted_text = extract_pdf_text(
                    file_contents
                )

                if not extracted_text:

                    return {
                        "status": "error",
                        "message": "PDF থেকে কোনো readable text পাওয়া যায়নি।"
                    }

                user_question = question

                if not user_question:
                    user_question = (
                        "Please analyze this document and summarize "
                        "the most important information."
                    )

                document_context = (
                    f"User uploaded a PDF named: {file.filename}\n\n"
                    f"Document content:\n"
                    f"{extracted_text[:12000]}"
                )

                if grade:
                    document_context += (
                        f"\n\nUser level/context: {grade}"
                    )

                if subject:
                    document_context += (
                        f"\nSubject/context: {subject}"
                    )

                response = ask_ai(
                    user_question=user_question,
                    chat_history=history,
                    context_text=document_context
                )

                response = clean_ai_response(response)

                save_message(
                    session_id,
                    "user",
                    f"[PDF: {file.filename}] {user_question}"
                )

                save_message(
                    session_id,
                    "assistant",
                    response
                )

                return {
                    "status": "success",
                    "question": user_question,
                    "response": response
                }

            # =================================================
            # IMAGE
            # =================================================

            if (
                file.content_type
                and file.content_type.startswith("image/")
            ):

                user_question = question

                if not user_question:
                    user_question = (
                        "Analyze this image and tell me what is important."
                    )

                image_response, error = await analyze_image(
                    user_question,
                    file_contents,
                    file.content_type
                )

                if error:

                    return {
                        "status": "error",
                        "message": error
                    }

                save_message(
                    session_id,
                    "user",
                    f"[Image: {file.filename}] {user_question}"
                )

                save_message(
                    session_id,
                    "assistant",
                    image_response
                )

                return {
                    "status": "success",
                    "question": user_question,
                    "response": image_response
                }

            return {
                "status": "error",
                "message": "Unsupported file type."
            }

        # ====================================================
        # NORMAL TEXT CHAT
        # ====================================================

        if not question:

            return {
                "status": "error",
                "message": "Please enter a message."
            }

        contextual_question = question

        if grade:
            contextual_question += (
                f"\n\n[Optional user context: {grade}]"
            )

        if subject:
            contextual_question += (
                f"\n[Optional subject context: {subject}]"
            )

        response = ask_ai(
            user_question=contextual_question,
            chat_history=history
        )

        response = clean_ai_response(response)

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
            "question": question,
            "response": response
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 8000)
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
