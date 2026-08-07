# main.py - FastAPI Server Entry Point
from fastapi import FastAPI, Form, UploadFile, File
from typing import Optional
from ai_brain import ask_ai_tutor, extract_text_from_pdf

app = FastAPI(title="Tuto AI Backend")

@app.get("/")
def home():
    return {"message": "Tuto AI Backend is Running Successfully!"}

@app.post("/api/chat")
async def chat_endpoint(
    question: str = Form(...),
    grade: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    try:
        pdf_text = ""
        if file and file.filename.endswith(".pdf"):
            pdf_text = extract_text_from_pdf(file.file)

        user_content = f"Grade: {grade}\nSubject: {subject}\nQuestion: {question}"
        if pdf_text:
            user_content += f"\n\nPDF Context:\n{pdf_text}"

        messages = [{"role": "user", "content": user_content}]
        response = ask_ai_tutor(messages)

        return {"status": "success", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}

