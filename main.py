from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import uvicorn
import base64
import re
import tempfile
from groq import Groq
from pypdf import PdfReader
from PIL import Image

app = FastAPI(title="Tuto AI Professional Edition")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# In-memory storage for chat histories
chat_sessions = {}

class TitleRequest(BaseModel):
    prompt: str

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tuto AI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- KaTeX Math Rendering -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
    
    <!-- Marked.js for Markdown -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

    <!-- Highlight.js for Syntax Highlighting -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>

    <style>
        :root {
            --bg-color: #131314;
            --sidebar-bg: #1e1e20;
            --text-color: #ffffff;
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
            transition: all 0.2s;
        }
        .new-chat-btn:hover {
            background-color: #3b3a43;
            color: #fff;
        }
        .history-list {
            flex: 1;
            overflow-y: auto;
            margin-top: 15px;
        }
        .history-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 12px;
            border-radius: 10px;
            color: #ccc;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 5px;
            transition: background 0.2s;
        }
        .history-item:hover, .history-item.active {
            background-color: #2b2a33;
            color: #fff;
        }
        .history-title {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 170px;
        }
        .delete-chat-btn {
            color: #888;
            border: none;
            background: none;
            font-size: 12px;
            cursor: pointer;
            opacity: 0.7;
        }
        .delete-chat-btn:hover {
            color: #ff4d4d;
            opacity: 1;
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
            align-items: center;
            justify-content: space-between;
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
            width: 100%;
        }
        
        /* Code Box Style */
        .code-box {
            background: #282c34;
            border-radius: 8px;
            margin: 12px 0;
            overflow: hidden;
            border: 1px solid #3e4451;
        }
        .code-header {
            background: #21252b;
            padding: 6px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: #abb2bf;
        }
        .copy-btn {
            background: #31353f;
            border: none;
            color: #abb2bf;
            padding: 3px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
        }
        .copy-btn:hover { background: #4b5263; color: #fff; }
        pre { margin: 0; padding: 12px; }

        .input-wrapper {
            max-width: 850px;
            margin: 0 auto 25px auto;
            width: 90%;
            background-color: #1e1e20;
            border: 1px solid #3c4043;
            border-radius: 20px;
            padding: 8px 15px;
        }
        .input-row { display: flex; align-items: center; gap: 10px; }
        .plus-btn, .mic-btn, .send-btn {
            background: none; border: none; color: var(--accent-color); font-size: 18px; cursor: pointer;
        }
        .mic-btn.recording { color: #ef4444; animation: pulse 1s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
        .chat-textarea {
            background: none; border: none; color: #ffffff; width: 100%; outline: none; font-size: 15px; resize: none;
        }
        .file-preview {
            display: flex;
            align-items: center;
            gap: 10px;
            background: #2b2a33;
            padding: 5px 12px;
            border-radius: 12px;
            margin-bottom: 8px;
            font-size: 13px;
        }
        @media (max-width: 768px) { .sidebar { display: none; } }
    </style>
</head>
<body>
    <div class="sidebar">
        <button class="new-chat-btn w-100 mb-2" onclick="startNewChat()">
            <i class="fa-solid fa-plus me-2"></i> New Chat
        </button>
        <div class="text-secondary small fw-bold mt-2 mb-1">RECENT CHATS</div>
        <div class="history-list" id="historyList"></div>
    </div>

    <div class="main-chat">
        <div class="chat-header">
            <h5 class="m-0 fw-bold text-light"><i class="fa-solid fa-graduation-cap me-2 text-warning"></i>Tuto AI</h5>
        </div>

        <div class="chat-container" id="chatBox"></div>

        <div class="container max-width-850">
            <div class="input-wrapper">
                <div id="filePreviewArea"></div>
                <div class="input-row">
                    <button type="button" class="plus-btn" onclick="document.getElementById('fileInput').click()">
                        <i class="fa-solid fa-paperclip"></i>
                    </button>
                    <input type="file" id="fileInput" style="display:none;" onchange="handleFileSelect(event)">

                    <form id="chatForm" class="d-flex w-100 align-items-center gap-2">
                        <textarea id="question" class="chat-textarea" rows="1" placeholder="Message Tuto AI or attach photo/PDF..."></textarea>
                        <button type="button" class="mic-btn" id="micBtn" onclick="toggleVoiceRecording()">
                            <i class="fa-solid fa-microphone"></i>
                        </button>
                        <button type="submit" class="send-btn" id="sendBtn">
                            <i class="fa-solid fa-paper-plane"></i>
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
    const questionInput = document.getElementById('question');
    const chatBox = document.getElementById('chatBox');
    const historyList = document.getElementById('historyList');
    const micBtn = document.getElementById('micBtn');
    const fileInput = document.getElementById('fileInput');
    const filePreviewArea = document.getElementById('filePreviewArea');

    let allSessions = JSON.parse(localStorage.getItem('tuto_all_sessions')) || {};
    let currentSessionId = localStorage.getItem('tuto_current_session_id') || null;
    let selectedFile = null;
    let mediaRecorder = null;
    let audioChunks = [];

    const DEFAULT_WELCOME = `
        <div class="message">
            <div class="avatar ai-avatar">AI</div>
            <div class="bubble"><strong>Hello!</strong><br>I am Tuto AI. How can I help you today? You can ask questions, send code, or attach images/PDFs!</div>
        </div>
    `;

    window.addEventListener('DOMContentLoaded', () => {
        if (!currentSessionId || !allSessions[currentSessionId]) {
            startNewChat(false);
        } else {
            renderSidebarHistory();
            loadSession(currentSessionId);
        }
    });

    function saveSessionsToStorage() {
        localStorage.setItem('tuto_all_sessions', JSON.stringify(allSessions));
        localStorage.setItem('tuto_current_session_id', currentSessionId);
    }

    function startNewChat(shouldRender = true) {
        currentSessionId = 'session_' + Date.now();
        allSessions[currentSessionId] = { title: 'New Chat', html: DEFAULT_WELCOME };
        saveSessionsToStorage();
        if (shouldRender) { renderSidebarHistory(); loadSession(currentSessionId); }
    }

    function loadSession(sessionId) {
        currentSessionId = sessionId;
        saveSessionsToStorage();
        chatBox.innerHTML = allSessions[sessionId].html || DEFAULT_WELCOME;
        chatBox.scrollTop = chatBox.scrollHeight;
        renderSidebarHistory();
        renderMathAndCode();
    }

    function deleteSession(e, sessionId) {
        e.stopPropagation();
        delete allSessions[sessionId];
        const keys = Object.keys(allSessions);
        if (keys.length > 0) { currentSessionId = keys[keys.length - 1]; } else { startNewChat(false); }
        saveSessionsToStorage();
        renderSidebarHistory();
        loadSession(currentSessionId);
    }

    function renderSidebarHistory() {
        historyList.innerHTML = '';
        Object.keys(allSessions).reverse().forEach(id => {
            const isActive = id === currentSessionId ? 'active' : '';
            historyList.innerHTML += `
                <div class="history-item ${isActive}" onclick="loadSession('${id}')">
                    <div class="history-title"><i class="fa-regular fa-message me-2"></i>${allSessions[id].title}</div>
                    <button class="delete-chat-btn" onclick="deleteSession(event, '${id}')"><i class="fa-solid fa-trash-can"></i></button>
                </div>
            `;
        });
    }

    function handleFileSelect(e) {
        selectedFile = e.target.files[0];
        if (selectedFile) {
            filePreviewArea.innerHTML = `
                <div class="file-preview">
                    <i class="fa-solid fa-file"></i> <span>${selectedFile.name}</span>
                    <i class="fa-solid fa-xmark text-danger ms-auto" style="cursor:pointer;" onclick="clearFile()"></i>
                </div>
            `;
        }
    }

    function clearFile() {
        selectedFile = null;
        fileInput.value = '';
        filePreviewArea.innerHTML = '';
    }

    function formatTextToHTML(text) {
        try {
            return marked.parse(text);
        } catch(e) {
            return text.replace(/\\n/g, '<br>');
        }
    }

    function renderMathAndCode() {
        renderMathInElement(chatBox, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '$', right: '$', display: false}
            ],
            throwOnError: false
        });
        
        chatBox.querySelectorAll('pre code').forEach((block) => {
            if (!block.classList.contains('hljs-done')) {
                hljs.highlightElement(block);
                block.classList.add('hljs-done');
                const wrapper = document.createElement('div');
                wrapper.className = 'code-box';
                wrapper.innerHTML = `<div class="code-header"><span>Code</span><button class="copy-btn" onclick="copyCode(this)">Copy</button></div>`;
                block.parentNode.parentNode.insertBefore(wrapper, block.parentNode);
                wrapper.appendChild(block.parentNode);
            }
        });
    }

    function copyCode(btn) {
        const code = btn.parentElement.nextElementSibling.innerText;
        navigator.clipboard.writeText(code);
        btn.innerText = 'Copied!';
        setTimeout(() => btn.innerText = 'Copy', 2000);
    }

    async function toggleVoiceRecording() {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            micBtn.classList.remove('recording');
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const formData = new FormData();
                formData.append('file', audioBlob, 'voice.wav');

                micBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;
                try {
                    const res = await fetch('/api/transcribe', { method: 'POST', body: formData });
                    const data = await res.json();
                    if (data.text) {
                        questionInput.value = data.text;
                    }
                } catch(e) { console.error(e); }
                micBtn.innerHTML = `<i class="fa-solid fa-microphone"></i>`;
            };

            mediaRecorder.start();
            micBtn.classList.add('recording');
        } catch (err) {
            alert('Microphone access denied or not supported.');
        }
    }

    async function generateTitle(prompt) {
        try {
            const res = await fetch('/api/generate-title', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt })
            });
            const data = await res.json();
            if (data.title) {
                allSessions[currentSessionId].title = data.title;
                saveSessionsToStorage();
                renderSidebarHistory();
            }
        } catch(e) {}
    }

    document.getElementById('chatForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = questionInput.value.trim();
        if (!question && !selectedFile) return;

        if (allSessions[currentSessionId].title === 'New Chat') {
            generateTitle(question || "File Upload");
        }

        let userContent = question;
        if (selectedFile) {
            userContent += `<br><small class="text-info"><i class="fa-solid fa-paperclip me-1"></i>[Attached: ${selectedFile.name}]</small>`;
        }

        chatBox.innerHTML += `
            <div class="message">
                <div class="avatar user-avatar">You</div>
                <div class="bubble"><strong>You</strong><br>${userContent}</div>
            </div>
        `;
        
        questionInput.value = '';
        const loadingId = 'loading-' + Date.now();
        chatBox.innerHTML += `
            <div class="message" id="${loadingId}">
                <div class="avatar ai-avatar">AI</div>
                <div class="bubble text-secondary"><i class="fa-solid fa-circle-notch fa-spin me-2"></i>Thinking...</div>
            </div>
        `;
        chatBox.scrollTop = chatBox.scrollHeight;

        const formData = new FormData();
        formData.append('question', question);
        formData.append('session_id', currentSessionId);
        if (selectedFile) {
            formData.append('file', selectedFile);
        }

        clearFile();

        try {
            const response = await fetch('/api/chat', { method: 'POST', body: formData });
            const data = await response.json();
            const loadingElem = document.getElementById(loadingId);

            if (data.status === 'success') {
                const parsedHTML = formatTextToHTML(data.response);
                loadingElem.querySelector('.bubble').innerHTML = `<strong>Tuto AI</strong><br>${parsedHTML}`;
                renderMathAndCode();

                allSessions[currentSessionId].html = chatBox.innerHTML;
                saveSessionsToStorage();
            } else {
                loadingElem.querySelector('.bubble').innerHTML = `<span class="text-danger">Error: ${data.message}</span>`;
            }
        } catch (err) {
            document.getElementById(loadingId).querySelector('.bubble').innerHTML = `<span class="text-danger">Connection error. Please try again.</span>`;
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    });
</script>
</body>
</html>
"""

def clean_ai_response(text: str) -> str:
    if not text: return ""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return text.strip()

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_LAYOUT

@app.post("/api/generate-title")
async def generate_title_endpoint(req: TitleRequest):
    try:
        if not GROQ_API_KEY:
            return {"title": req.prompt[:20]}
        client = Groq(api_key=GROQ_API_KEY)
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Generate a concise 3 to 5 word topic title for this chat. Respond with ONLY the title."},
                {"role": "user", "content": req.prompt}
            ]
        )
        title = res.choices[0].message.content.strip().replace('"', '')
        return {"title": title}
    except Exception:
        return {"title": req.prompt[:20]}

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(tmp_path, audio_file.read()),
                model="whisper-large-v3",
                response_format="json",
            )
        os.remove(tmp_path)
        return {"text": transcription.text}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/chat")
async def chat_endpoint(
    question: str = Form(""),
    session_id: str = Form("default"),
    file: UploadFile = File(None)
):
    global chat_sessions
    try:
        if not GROQ_API_KEY:
            return {"status": "error", "message": "GROQ_API_KEY is not configured on server."}

        client = Groq(api_key=GROQ_API_KEY)
        
        file_context = ""
        image_base64 = None

        if file:
            content_type = file.content_type or ""
            file_bytes = await file.read()

            if "pdf" in content_type:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name

                reader = PdfReader(tmp_path)
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text() or ""
                os.remove(tmp_path)
                file_context = f"\n\n[Attached PDF Content]:\n{pdf_text[:3000]}"

            elif "image" in content_type:
                image_base64 = base64.b64encode(file_bytes).decode('utf-8')

        full_prompt = (question + file_context).strip()
        if not full_prompt and not image_base64:
            full_prompt = "Hello"

        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        system_prompt = "You are Tuto AI, created solely by Imran Hossen. Help users with clear explanations and clean markdown code blocks."

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_sessions[session_id][-6:])

        if image_base64:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": full_prompt or "Describe this image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            })
            model_to_use = "llama-3.2-11b-vision-preview"
        else:
            messages.append({"role": "user", "content": full_prompt})
            model_to_use = "llama-3.3-70b-versatile"

        completion = client.chat.completions.create(
            model=model_to_use,
            messages=messages
        )

        reply = clean_ai_response(completion.choices[0].message.content)

        chat_sessions[session_id].append({"role": "user", "content": full_prompt})
        chat_sessions[session_id].append({"role": "assistant", "content": reply})

        return {"status": "success", "response": reply}

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
