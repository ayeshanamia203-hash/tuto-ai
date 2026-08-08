from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import os
import uvicorn
from ai_brain import ask_tuto_ai

app = FastAPI(title="Tuto AI Professional")

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tuto AI - Pro Tutor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-color: #131314;
            --sidebar-bg: #1e1e20;
            --chat-bg: #131314;
            --user-bubble: #2b2a33;
            --ai-bubble: #1e1e20;
            --text-color: #e3e3e3;
            --accent-color: #a8c7fa;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            height: 100vh;
            margin: 0;
            display: flex;
        }

        /* Sidebar UI */
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
            transition: 0.2s;
        }

        .new-chat-btn:hover {
            background-color: #373544;
            color: #fff;
        }

        /* Main Chat Area */
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
        }

        .user-avatar { background-color: #5436da; color: white; }
        .ai-avatar { background: linear-gradient(135deg, #10a37f, #0d8a6a); color: white; }

        .bubble {
            max-width: 85%;
            font-size: 15px;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        /* Input Box (Gemini / ChatGPT Style) */
        .input-wrapper {
            max-width: 850px;
            margin: 0 auto 25px auto;
            width: 90%;
            position: relative;
        }

        .chat-input {
            background-color: #1e1e20;
            border: 1px solid #3c4043;
            color: var(--text-color);
            border-radius: 25px;
            padding: 15px 50px 15px 20px;
            width: 100%;
            outline: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .chat-input:focus {
            border-color: var(--accent-color);
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

        @media (max-width: 768px) {
            .sidebar { display: none; }
        }
    </style>
</head>
<body>

    <!-- Sidebar -->
    <div class="sidebar">
        <button class="new-chat-btn w-100 mb-4" onclick="location.reload()">
            <i class="fa-solid fa-plus me-2"></i> New Chat
        </button>
        <div class="text-secondary small fw-bold mb-2">RECENT CHATS</div>
        <div class="text-muted small">✨ Tuto AI Assistant</div>
        <div class="mt-auto text-muted small border-top border-secondary pt-3">
            👨‍💻 Developer: <strong>Imran Hossen</strong>
        </div>
    </div>

    <!-- Main Chat Screen -->
    <div class="main-chat">
        <div class="chat-header">
            <h5 class="m-0 fw-bold"><i class="fa-solid fa-graduation-cap me-2 text-primary"></i>Tuto AI</h5>
            <span class="badge bg-dark border border-secondary text-light">v2.0 Pro</span>
        </div>

        <div class="chat-container" id="chatBox">
            <div class="message">
                <div class="avatar ai-avatar">AI</div>
                <div class="bubble">
                    <strong>Hello Imran!</strong><br>
                    I am Tuto AI, your personal academic assistant. How can I help you today?
                </div>
            </div>
        </div>

        <!-- Input Area -->
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

        // User Message Append
        chatBox.innerHTML += `
            <div class="message">
                <div class="avatar user-avatar">IH</div>
                <div class="bubble"><strong>You</strong><br>${question}</div>
            </div>
        `;
        
        input.value = '';
        sendBtn.disabled = true;
        chatBox.scrollTop = chatBox.scrollHeight;

        // AI Thinking Placeholder
        const loadingId = 'loading-' + Date.now();
        chatBox.innerHTML += `
            <div class="message" id="${loadingId}">
                <div class="avatar ai-avatar">AI</div>
                <div class="bubble text-muted"><i class="fa-solid fa-circle-notch fa-spin me-2"></i>Thinking...</div>
            </div>
        `;
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const formData = new FormData();
            formData.append('question', question);
            formData.append('grade', 'General');
            formData.append('subject', 'General');

            const response = await fetch('/api/chat', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            const loadingElem = document.getElementById(loadingId);
            
            if (data.status === 'success') {
                loadingElem.querySelector('.bubble').innerHTML = `<strong>Tuto AI</strong><br>${data.response}`;
            } else {
                loadingElem.querySelector('.bubble').innerHTML = `<span class="text-danger">Sorry, something went wrong.</span>`;
            }
        } catch (error) {
            document.getElementById(loadingId).querySelector('.bubble').innerHTML = `<span class="text-danger">Unable to connect to server.</span>`;
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
def chat_endpoint(
    question: str = Form(...),
    grade: str = Form("General"),
    subject: str = Form("General Studies")
):
    try:
        response_text = ask_tuto_ai(question=question, grade=grade, subject=subject)
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
