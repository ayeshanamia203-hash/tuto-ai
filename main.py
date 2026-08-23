# ============================================================
# TUTO AI - MAIN.PY
# Groq Text + Groq Vision + Groq Whisper
# NO GEMINI
# ============================================================

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
# APP
# ============================================================

app = FastAPI(
    title="Tuto AI",
    description="Tuto AI - Groq powered AI assistant",
    version="4.0.0"
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
# MODELS
# ============================================================

TEXT_MODEL = "openai/gpt-oss-20b"

VISION_MODEL = "qwen/qwen3.6-27b"

WHISPER_MODEL = "whisper-large-v3"


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

            try:

                text = page.extract_text()

                if text:
                    pages.append(text)

            except Exception:
                continue

        return "\n\n".join(pages).strip()

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

    # Keep latest 40 messages
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
                        Expected file:
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
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {

        "status": "ok",

        "service": "Tuto AI",

        "text_model": TEXT_MODEL,

        "vision_model": VISION_MODEL,

        "voice_model": WHISPER_MODEL,

        "gemini": False

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
                    "Empty audio file."

            }

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        ) as temp_audio:

            temp_audio.write(
                audio_content
            )

            temp_audio_path = temp_audio.name

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

                        model=WHISPER_MODEL,

                        response_format="json"

                    )
                )

            return {

                "status": "success",

                "text":
                    transcription.text or ""

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

Create a very short title for this conversation.

User message:

{prompt}

Rules:

- 2 to 5 words maximum.
- Output ONLY the title.
- No quotation marks.
- No explanation.
- No punctuation at the end.
- Match the user's language when possible.

"""

        completion = (
            groq_client
            .chat
            .completions
            .create(

                model=TEXT_MODEL,

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

        title = title.replace(
            "\n",
            " "
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


    # --------------------------------------------------------
    # GROQ CURRENT MAX FILE SIZE
    # --------------------------------------------------------

    if len(image_bytes) > 20 * 1024 * 1024:

        return (

            None,

            "Image is too large. "
            "Please upload an image smaller than 20 MB."

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
        # USER QUESTION
        # ----------------------------------------------------

        user_question = (
            question.strip()
        )


        if not user_question:

            user_question = (
                "Briefly describe what is visible "
                "in this image."
            )


        # ----------------------------------------------------
        # IMAGE PROMPT
        # ----------------------------------------------------

        prompt = f"""

You are Tuto AI.

Look at the uploaded image and answer the user's
question directly.

USER QUESTION:
{user_question}

IMPORTANT:

1. Answer the exact question first.
2. Keep simple questions SIMPLE.
3. Do NOT automatically write a long image analysis.
4. Do NOT describe the entire image unless the user asks.
5. If the user asks for a short answer, give a short answer.
6. Normally keep the answer to 1-4 short sentences.
7. If the user asks for detailed analysis, then provide details.
8. Do not invent information that cannot reasonably be seen.
9. If something cannot be determined reliably from the image,
   say that clearly.
10. Do not infer a person's gender identity, sexuality, religion,
    race, medical condition, or other sensitive personal
    attributes from appearance.
11. If the user asks whether a person is a boy or girl based
    only on appearance, say that the person's gender cannot
    be reliably determined from the image.
12. Match the user's language.
13. If the user writes Bangla, answer in Bangla.
14. Do not repeat the user's question.

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

                max_completion_tokens=300,

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

                "Groq Vision returned an empty response."

            )


        return (

            clean_ai_response(answer),

            None

        )


    except Exception as e:

        return (

            None,

            f"Groq Vision error: {str(e)}"

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
        # FILE UPLOAD
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
                            "PDF থেকে কোনো readable text পাওয়া যায়নি।"

                    }


                user_question = (
                    question
                    or
                    "Please analyze this document and "
                    "summarize the most important information."
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

                    "Briefly describe what is visible "
                    "in this image."

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
