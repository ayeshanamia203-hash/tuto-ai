# main.py - FastAPI Server Entry Point
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from ai_brain import ask_ai_tutor, extract_text_from_pdf

app = FastAPI(title="Tuto AI Tutor Backend")

# Allow Frontend (Next.js) to connect with Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "online", "message": "Tuto AI Tutor API is Running Streamlessly!"}

@app.post("/api/chat")
async def chat_endpoint(
    question: str = Form(...),
    grade: str = Form("General / Self-Learner"),
    subject: str = Form("General Studies"),
    file: Optional[UploadFile] = File(None)
):
    context_text = ""
    image_file = None

    if file:
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext == "pdf":
            context_text = extract_text_from_pdf(file.file)
        elif file_ext in ["png", "jpg", "jpeg"]:
            image_file = file.file

    response = ask_ai_tutor(
        user_question=question,
        chat_history=None,
        grade=grade,
        subject=subject,
        context_text=context_text,
        image_file=image_file
    )

    return {"response": response}
