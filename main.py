from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import os
import uvicorn

app = FastAPI(title="Tuto AI Backend")

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tuto AI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f6f9; font-family: sans-serif; }
        .chat-card { max-width: 700px; margin: 30px auto; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .chat-header { background: #4f46e5; color: white; border-radius: 15px 15px 0 0 !important; padding: 15px; }
        .chat-box { height: 380px; overflow-y: auto; padding: 20px; background: #fff; }
        .bubble { padding: 10px 15px; border-radius: 15px; background: #f1f5f9; display: inline-block; }
    </style>
</head>
<body>
<div class="container">
    <div class="card chat-card">
        <div class="card-header chat-header text-center">
            <h4 class="m-0">🎓 Tuto AI Tutor</h4>
        </div>
        <div class="chat-box" id="chatBox">
            <div class="bubble">হ্যালো ইমরান ভাই! আমি Tuto AI। তোমার কী সাহায্য লাগবে?</div>
        </div>
        <div class="p-3 bg-light">
            <form id="chatForm">
                <div class="input-group">
                    <input type="text" id="question" class="form-control" placeholder="প্রশ্ন লেখো..." required>
                    <button class="btn btn-primary" type="submit">পাঠাও 🚀</button>
                </div>
            </form>
        </div>
    </div>
</div>
<script>
    document.getElementById('chatForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const input = document.getElementById('question');
        const chatBox = document.getElementById('chatBox');
        chatBox.innerHTML += `<div class="text-end my-2"><span class="bubble bg-primary text-white">${input.value}</span></div>`;
        input.value = '';
    });
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_LAYOUT

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
