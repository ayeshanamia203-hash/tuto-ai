# main.py
# Tuto AI - Groq Text + Groq Vision + Groq Whisper

import base64
import io
import os
import re
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse
from groq import Groq
import uvicorn

from ai_brain import ask_ai
from config import GROQ_API_KEY


# ============================================================
# APP CONFIGURATION
# ============================================================

app = FastAPI(
    title="Tuto AI",
    description="Tuto AI - General Purpose AI",
    version="3.0.0"
)


# ============================================================
# GROQ CLIENT
# ============================================================

groq_client = None

if GROQ_API_KEY:
    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


# ============================================================
# GROQ VISION MODEL
# ============================================================

# Current Groq vision-capable model
VISION_MODEL = "qwen/qwen3.6-27b"


# ============================================================
# CHAT MEMORY
# ============================================================

chat_sessions = {}


# ============================================================
# CLEAN RESPONSE
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
# SESSION
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

        index_file = (
            Path(__file__).resolve().parent
            / "index.html"
        )

        if not index_file.exists():

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

        "vision": VISION_MODEL

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

                "text": transcription.text

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

        completion = (
            groq_client
            .chat
            .completions
            .create(

                model="openai/gpt-oss-20b",

                messages=[

                    {
                        "role": "user",
                        "content": title_prompt
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

        return {

            "status": "success",

            "title": title[:80]

        }

    except Exception:

        return {

            "status": "success",

            "title": "New Chat"

        }


# ============================================================
# GROQ VISION
# ============================================================

async def analyze_image(
    question: str,
    image_bytes: bytes,
    mime_type: str
):

    if not GROQ_API_KEY or not groq_client:

        return (
            None,
            "GROQ_API_KEY missing."
        )

    # Groq base64 image request limit is 4 MB.
    if len(image_bytes) > 4 * 1024 * 1024:

        return (

            None,

            "Image is too large. "
            "Please upload a smaller image."

        )

    try:

        # ----------------------------------------------------
        # BASE64
        # ----------------------------------------------------

        image_base64 = (
            base64
            .b64encode(image_bytes)
            .decode("utf-8")
        )

        image_url = (
            f"data:{mime_type};"
            f"base64,{image_base64}"
        )


        # ----------------------------------------------------
        # QUESTION
        # ----------------------------------------------------

        user_question = (
            question.strip()
        )

        if not user_question:

            user_question = (
                "Briefly describe the "
                "important things visible "
                "in this image."
            )


        # ----------------------------------------------------
        # IMAGE PROMPT
        # ----------------------------------------------------

        prompt = f"""

You are Tuto AI, a helpful general-purpose
AI assistant.

Analyze the image and answer the user's request.

User request:

{user_question}

IMPORTANT RESPONSE STYLE:

- Be concise and natural.
- Usually use 3-6 short bullet points.
- Aim for around 60-150 words.
- Do NOT write a long essay.
- Do NOT repeat the user's question.
- Only describe things that can reasonably be seen.
- Do not invent information.
- If something is uncertain, say so.
- Match the user's language.
- If the user writes Bangla, answer in Bangla.
- If the user asks a simple question,
  give a simple answer.
- Only give a detailed answer if the user
  specifically asks for details.

"""

        # ----------------------------------------------------
        # GROQ VISION REQUEST
        # ----------------------------------------------------

        response = (
            groq_client
            .chat
            .completions
            .create(

                model=VISION_MODEL,

                messages=[

                    {

                        "role": "user",

                        "content": [

                            {

                                "type": "text",

                                "text": prompt

                            },

                            {

                                "type": "image_url",

                                "image_url": {

                                    "url": image_url

                                }

                            }

                        ]

                    }

                ],

                temperature=0.3,

                max_completion_tokens=350,

                stream=False

            )
        )


        answer = (
            response
            .choices[0]
            .message
            .content
            or ""
        ).strip()


        if not answer:

            return (

                None,

                "Groq vision returned "
                "an empty response."

            )


        return (

            clean_ai_response(
                answer
            ),

            None

        )

    except Exception as e:

        return (

            None,

            f"Groq vision error: {str(e)}"

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
        # FILE
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

                    user_question=user_question,

                    chat_history=history,

                    context_text=document_context

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

                    "question": user_question,

                    "response": response

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

                    "Briefly analyze this image."

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

                        "message": error

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

                    "question": user_question,

                    "response": image_response

                }


            # =================================================
            # UNSUPPORTED
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


        contextual_question = question


        if grade:

            contextual_question += (
                f"\n\n"
                f"[Optional user context: {grade}]"
            )


        if subject:

            contextual_question += (
                f"\n"
                f"[Optional subject context: {subject}]"
            )


        response = ask_ai(

            user_question=contextual_question,

            chat_history=history

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
