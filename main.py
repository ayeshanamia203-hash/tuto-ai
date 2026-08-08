from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import os
import uvicorn
from groq import Groq

app = FastAPI(title="Tuto AI Professional")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tuto AI - Created by Imran Hossen</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-color: #131314;
            --sidebar-bg: #1e1e20;
            --chat-bg: #131314;
            --text-color: #ffffff;
            --accent-color: #a8c7fa;
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Segoe UI', system-ui, sans-serif;
            height: 100vh;
            margin: 0;
            display: flex;
        }
        .sidebar {
            width: 260px;
            background-color: var(--sidebar-bg);
            padding: 20px;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #2d2d30;
        }
        .new-chat-btn {
            background-color: #2b2a33;
            color: var(--text-color);
            border: 1px solid #444;
            border-radius: 30px;
            padding: 10px 15px;
            font-weight: 500;
        }
        .main-chat {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 100vh;
        }
        .chat-header {
            padding: 15px 25px;
            border-bottom: 1px solid #2d2d30;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 30px;
            max-width: 850px;
            margin: 0 auto;
            width: 100%;
        }
        .message {
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
        }
        .avatar {
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: bold;
            flex-shrink: 0;
        }
        .user-avatar { background-color: #5436da; color: #ffffff; }
        .ai-avatar { background: linear-gradient(135deg, #f59e0b, #d97706); color: #ffffff; }
        .bubble {
            max-width: 85%;
            font-size: 16px;
            line-height: 1.6;
            color: #ffffff !important;
            white-space: pre-wrap;
        }
        .bubble strong {
            color: #a8c7fa !important;
        }
        .input-wrapper {
            max-width: 850px;
            margin: 0 auto 25px auto;
            width: 90%;
            position: relative;
        }
        .chat-input {
            background-color: #1e1e20;
            border: 1px solid #3c4043;
            color: #ffffff;
            border-radius: 25px;
            padding: 15px 50px 15px 20px;
            width: 100%;
            outline: none;
            font-size: 15px;
        }
        .send-btn {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: var(--accent-color);
            font-size: 18px;
            cursor: pointer;
        }
        @media (max-width: 768px) { .sidebar { display: none; } }
    </style>
</head>
<body>
    <div class="sidebar">
        <button class="new-chat-btn w-100 mb-4" onclick="location.reload()">
            <i class="fa-solid fa-plus me-2"></i> New Chat
        </button>
        <div class="text-secondary small fw-bold mb-2">PROJECT</div>
        <div class="text-light small">✨ Tuto AI System</div>
        <div class="mt-auto text-secondary small border-top border-secondary pt-3">
            👨‍💻 Developer: <strong class="text-light">Imran Hossen</strong>
        </div>
    </div>

    <div class="main-chat">
        <div class="chat-header">
            <h5 class="m-0 fw-bold text-light"><i class="fa-solid fa-graduation-cap me-2 text-warning"></i>Tuto AI</h5>
            <span class="badge bg-primary text-light px-3 py-2" style="font-size: 13px;">Created by Imran Hossen</span>
        </div>

        <div class="chat-container" id="chatBox">
            <div class="message">
                <div class="avatar ai-avatar">AI</div>
                <div class="bubble">
                    <strong>Hello Imran!</strong><br>
                    I am Tuto AI, your academic assistant. How can I help you today?
                </div>
            </div>
        </div>

        <div class="input-wrapper">
            <form id="chatForm">
                <input type="text" id="question" class="chat-input" placeholder="Message Tuto AI..." autocomplete="off" required>
                <button type="submit" class="send-btn" id="sendBtn">
                    <i class="fa-solid fa-paper-plane"></i>
                </button>
            </form>
        </div>
    </div>

<script>
    document.getElementById('chatForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const input = document.getElementById('question');
        const chatBox = document.getElementById('chatBox');
        const sendBtn = document.getElementById('sendBtn');

        const question = input.value.trim();
        if (!question) return;

        chatBox.innerHTML += `
            <div class="message">
                <div class="avatar user-avatar">IH</div>
                <div class="bubble"><strong>You</strong><br>${question}</div>
            </div>
        `;
        
        input.value = '';
        sendBtn.disabled = true;
        chatBox.scrollTop = chatBox.scrollHeight;

        const loadingId = 'loading-' + Date.now();
        chatBox.innerHTML += `
            <div class="message" id="${loadingId}">
                <div class="avatar ai-avatar">AI</div>
                <div class="bubble text-secondary"><i class="fa-solid fa-circle-notch fa-spin me-2"></i>Thinking...</div>
            </div>
        `;
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const formData = new FormData();
            formData.append('question', question);

            const response = await fetch('/api/chat', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            const loadingElem = document.getElementById(loadingId);
            
            if (data.status === 'success') {
                loadingElem.querySelector('.bubble').innerHTML = `<strong>Tuto AI</strong><br>${data.response}`;
            } else {
                loadingElem.querySelector('.bubble').innerHTML = `<span class="text-danger">Error: ${data.message}</span>`;
            }
        } catch (error) {
            document.getElementById(loadingId).querySelector('.bubble').innerHTML = `<span class="text-danger">Server connection error.</span>`;
        } finally {
            sendBtn.disabled = false;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    });
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_LAYOUT

@app.post("/api/chat")
def chat_endpoint(question: str = Form(...)):
    try:
        if not GROQ_API_KEY:
            return {"status": "error", "message": "GROQ_API_KEY environment variable missing in Render."}
        
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are Tuto AI, a friendly and smart academic assistant created by Imran Hossen. Respond clearly in whatever language the user talks to you (Bangla, English, or Banglish)."},
                {"role": "user", "content": question}
            ]
        )
        
        response_text = completion.choices[0].message.content
        return {
            "status": "success",
            "question": question,
            "response": response_text
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
