from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import uvicorn
import base64
import re
import tempfile
from groq import Groq

app = FastAPI(title="Tuto AI Professional Edition")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# In-memory chat store for sessions
chat_sessions = {}

class TitleRequest(BaseModel):
    prompt: str

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tuto AI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- KaTeX Math Rendering CSS & JS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
    
    <!-- Marked.js for Markdown Rendering -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

    <!-- Highlight.js for Syntax Highlighting -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>

    <style>
        :root {
            --bg-color: #131314;
            --sidebar-bg: #1e1e20;
            --chat-bg: #131314;
            --text-color: #ffffff;
            --accent-color: #a8c7fa;
        }
        * {
            box-sizing: border-box;
        }
        html, body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        body {
            display: flex;
        }
        .sidebar {
            width: 260px;
            background-color: var(--sidebar-bg);
            padding: 20px;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #2d2d30;
            flex-shrink: 0;
            height: 100%;
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
            background-color: #3b3a45;
        }
        .history-list {
            flex: 1;
            overflow-y: auto;
            margin-top: 15px;
            margin-bottom: 15px;
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
            padding: 2px 5px;
        }
        .delete-chat-btn:hover {
            color: #e11d48;
        }
        .main-chat {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100vh;
            height: 100dvh; /* Dynamic Viewport Height for Mobile/iPad Safari */
            overflow: hidden;
            position: relative;
        }
        .chat-header {
            padding: 15px 25px;
            border-bottom: 1px solid #2d2d30;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px 30px;
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
        .bubble p { margin-bottom: 8px; }
        .bubble strong { color: #a8c7fa !important; }
        .bubble table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            color: #fff;
        }
        .bubble table, .bubble th, .bubble td {
            border: 1px solid #444;
            padding: 8px;
        }
        .bubble th { background-color: #2b2a33; }
        .uploaded-img-preview {
            max-width: 200px;
            border-radius: 10px;
            margin-bottom: 10px;
            border: 1px solid #444;
        }
        
        /* Code Container Styling */
        .code-container {
            position: relative;
            margin: 12px 0;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #3e4451;
            background: #282c34;
        }
        .code-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #21252b;
            padding: 6px 12px;
            font-size: 12px;
            color: #abb2bf;
            font-family: monospace;
            border-bottom: 1px solid #3e4451;
        }
        pre {
            margin: 0 !important;
            padding: 12px !important;
            background: transparent !important;
            overflow-x: auto;
        }
        pre code {
            font-family: 'Consolas', 'Fira Code', 'Courier New', monospace;
            font-size: 14px;
        }
        .copy-code-btn {
            background: #3e4451;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 12px;
            cursor: pointer;
            transition: 0.2s;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .copy-code-btn:hover {
            background: #4b5263;
        }

        .input-container-box {
            padding: 10px 20px 20px 20px;
            background: var(--bg-color);
            flex-shrink: 0;
        }

        .input-wrapper {
            max-width: 850px;
            margin: 0 auto;
            width: 100%;
            background-color: #1e1e20;
            border: 1px solid #3c4043;
            border-radius: 20px;
            padding: 8px 15px;
            display: flex;
            flex-direction: column;
        }

        #imagePreviewArea {
            display: none;
            position: relative;
            width: fit-content;
            margin-bottom: 8px;
        }

        #previewImgThumb {
            width: 70px;
            height: 70px;
            object-fit: cover;
            border-radius: 12px;
            border: 1px solid #555;
        }

        .close-img-btn {
            position: absolute;
            top: -6px;
            right: -6px;
            background: #e11d48;
            color: #fff;
            border: none;
            border-radius: 50%;
            width: 22px;
            height: 22px;
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }

        .input-row {
            display: flex;
            align-items: flex-end;
            gap: 10px;
        }

        .plus-btn, .mic-btn {
            background: none;
            border: none;
            color: var(--accent-color);
            font-size: 18px;
            cursor: pointer;
            padding: 5px;
            margin-bottom: 3px;
            transition: 0.2s;
        }
        .plus-btn:hover, .mic-btn:hover { color: #fff; }
        .mic-btn.recording {
            color: #ef4444 !important;
            animation: pulse 1.2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.2); }
            100% { transform: scale(1); }
        }

        .chat-textarea {
            background: none;
            border: none;
            color: #ffffff;
            padding: 6px 0;
            width: 100%;
            outline: none;
            font-size: 15px;
            resize: none;
            max-height: 120px;
            min-height: 28px;
            line-height: 1.4;
            font-family: inherit;
        }

        .send-btn {
            background: none;
            border: none;
            color: var(--accent-color);
            font-size: 18px;
            cursor: pointer;
            padding: 5px;
            margin-bottom: 3px;
        }
        
        .modal-content {
            background-color: #1e1e20;
            color: #fff;
            border: 1px solid #444;
        }
        .modal-btn {
            background-color: #2b2a33;
            color: #fff;
            border: 1px solid #444;
            border-radius: 15px;
            padding: 15px;
            width: 100%;
            text-align: left;
            margin-bottom: 10px;
            transition: 0.2s;
        }
        .modal-btn:hover {
            background-color: #3b3a45;
            color: #a8c7fa;
        }

        @media (max-width: 768px) { .sidebar { display: none; } }
    </style>
</head>
<body>
    <div class="sidebar">
        <button class="new-chat-btn w-100 mb-2" onclick="startNewChat()">
            <i class="fa-solid fa-plus me-2"></i> New Chat
        </button>
        <div class="text-secondary small fw-bold mt-2">RECENT CHATS</div>
        <div class="history-list" id="historyList">
            <!-- Chat history -->
        </div>
    </div>

    <div class="main-chat">
        <div class="chat-header">
            <h5 class="m-0 fw-bold text-light"><i class="fa-solid fa-graduation-cap me-2 text-warning"></i>Tuto AI</h5>
        </div>

        <div class="chat-container" id="chatBox">
            <!-- Chat messages -->
        </div>

        <div class="input-container-box">
            <div class="input-wrapper">
                <div id="imagePreviewArea">
                    <img id="previewImgThumb" src="" alt="Thumbnail">
                    <button type="button" class="close-img-btn" onclick="clearImage()"><i class="fa-solid fa-xmark"></i></button>
                </div>

                <div class="input-row">
                    <button type="button" class="plus-btn" data-bs-toggle="modal" data-bs-target="#uploadModal">
                        <i class="fa-solid fa-circle-plus"></i>
                    </button>
                    <form id="chatForm" class="d-flex w-100 align-items-end gap-2">
                        <textarea id="question" class="chat-textarea" rows="1" placeholder="Message Tuto AI or attach photo..."></textarea>
                        <button type="button" class="mic-btn" id="micBtn" onclick="toggleVoiceRecording()" title="Voice Input (Groq Whisper)">
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

    <input type="file" id="galleryInput" accept="image/*" style="display: none;" onchange="handleFileSelect(this)">
    <input type="file" id="cameraInput" accept="image/*" capture="environment" style="display: none;" onchange="handleFileSelect(this)">

    <div class="modal fade" id="uploadModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header border-0">
                    <h5 class="modal-title fw-bold"><i class="fa-solid fa-paperclip me-2 text-primary"></i>Attach Photo</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <button class="modal-btn" onclick="triggerCamera()">
                        <i class="fa-solid fa-camera fa-lg me-3 text-warning"></i> <strong>Take Photo</strong> (Open Camera)
                    </button>
                    <button class="modal-btn" onclick="triggerGallery()">
                        <i class="fa-solid fa-images fa-lg me-3 text-info"></i> <strong>Upload Photo</strong> (From Gallery)
                    </button>
                </div>
            </div>
        </div>
    </div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
    let selectedFile = null;
    const questionInput = document.getElementById('question');
    const chatBox = document.getElementById('chatBox');
    const historyList = document.getElementById('historyList');
    const micBtn = document.getElementById('micBtn');

    let allSessions = JSON.parse(localStorage.getItem('tuto_all_sessions')) || {};
    let currentSessionId = localStorage.getItem('tuto_current_session_id') || null;

    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;

    async function toggleVoiceRecording() {
        if (isRecording) {
            stopRecordingAndTranscribe();
        } else {
            startRecording();
        }
    }

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                stream.getTracks().forEach(track => track.stop());
                await transcribeAudio(audioBlob);
            };

            mediaRecorder.start();
            isRecording = true;
            micBtn.classList.add('recording');
            questionInput.placeholder = "Recording... Click mic again to stop";
        } catch (err) {
            console.error("Mic access denied or not supported:", err);
            alert("Microphone permission denied or not supported by browser!");
        }
    }

    function stopRecordingAndTranscribe() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            micBtn.classList.remove('recording');
            questionInput.placeholder = "Processing voice with Groq AI...";
        }
    }

    async function transcribeAudio(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'audio.webm');

        try {
            const response = await fetch('/api/transcribe', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.status === 'success' && data.text) {
                questionInput.value = data.text;
                questionInput.style.height = 'auto';
                questionInput.style.height = (questionInput.scrollHeight) + 'px';
            } else {
                alert("Voice recognition error: " + (data.message || "Could not recognize audio"));
            }
        } catch (err) {
            console.error("Transcription fetch error:", err);
            alert("Error connecting to Groq Whisper API");
        } finally {
            questionInput.placeholder = "Message Tuto AI or attach photo...";
        }
    }

    const DEFAULT_WELCOME = `
        <div class="message">
            <div class="avatar ai-avatar">AI</div>
            <div class="bubble">
                <strong>Hello!</strong><br>
                I am Tuto AI. Send me your Math, Physics, or Chemistry problems, or share any image to chat about it!
            </div>
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

    questionInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    questionInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('chatForm').dispatchEvent(new Event('submit'));
        }
    });

    function renderMathInElem(element) {
        if (window.renderMathInElement) {
            try {
                window.renderMathInElement(element, {
                    delimiters: [
                        {left: '$$', right: '$$', display: true},
                        {left: '$', right: '$', display: false},
                        {left: '\\(', right: '\\)', display: false},
                        {left: '\\[', right: '\\]', display: true}
                    ],
                    throwOnError : false
                });
            } catch(e) {}
        }
    }

    function processCodeBlocks(element) {
        if (!element) return;
        
        element.querySelectorAll('pre').forEach((pre) => {
            if (pre.closest('.code-container')) return;

            const codeBlock = pre.querySelector('code');
            const codeText = codeBlock ? codeBlock.innerText : pre.innerText;
            
            let lang = 'code';
            if (codeBlock && codeBlock.className) {
                const match = codeBlock.className.match(/language-(\\w+)/);
                if (match) lang = match[1];
            }

            const container = document.createElement('div');
            container.className = 'code-container';

            const header = document.createElement('div');
            header.className = 'code-header';
            header.innerHTML = `<span>${lang}</span>`;

            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-code-btn';
            copyBtn.type = 'button';
            copyBtn.innerHTML = '<i class="fa-regular fa-copy me-1"></i>Copy';
            
            copyBtn.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(codeText.trim());
                    copyBtn.innerHTML = '<i class="fa-solid fa-check me-1"></i>Copied!';
                    setTimeout(() => {
                        copyBtn.innerHTML = '<i class="fa-regular fa-copy me-1"></i>Copy';
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy code: ', err);
                }
            });

            header.appendChild(copyBtn);
            
            pre.parentNode.insertBefore(container, pre);
            container.appendChild(header);
            container.appendChild(pre);

            if (window.hljs && codeBlock) {
                try { hljs.highlightElement(codeBlock); } catch(e) {}
            }
        });
    }

    function saveSessionsToStorage() {
        localStorage.setItem('tuto_all_sessions', JSON.stringify(allSessions));
        localStorage.setItem('tuto_current_session_id', currentSessionId);
    }

    function startNewChat(shouldRender = true) {
        currentSessionId = 'session_' + Date.now();
        allSessions[currentSessionId] = {
            title: 'New Chat',
            html: DEFAULT_WELCOME,
            messages: []
        };
        saveSessionsToStorage();
        if (shouldRender) {
            renderSidebarHistory();
            loadSession(currentSessionId);
        }
    }

    function loadSession(sessionId) {
        currentSessionId = sessionId;
        saveSessionsToStorage();
        chatBox.innerHTML = allSessions[sessionId].html || DEFAULT_WELCOME;
        document.querySelectorAll('.bubble').forEach(elem => {
            renderMathInElem(elem);
            processCodeBlocks(elem);
        });
        chatBox.scrollTop = chatBox.scrollHeight;
        renderSidebarHistory();
    }

    function deleteSession(e, sessionId) {
        e.stopPropagation();
        delete allSessions[sessionId];
        if (currentSessionId === sessionId) {
            const keys = Object.keys(allSessions);
            if (keys.length > 0) {
                currentSessionId = keys[keys.length - 1];
            } else {
                startNewChat(false);
            }
        }
        saveSessionsToStorage();
        renderSidebarHistory();
        loadSession(currentSessionId);
    }

    function renderSidebarHistory() {
        historyList.innerHTML = '';
        const keys = Object.keys(allSessions).reverse();
        keys.forEach(id => {
            const session = allSessions[id];
            const isActive = id === currentSessionId ? 'active' : '';
            historyList.innerHTML += `
                <div class="history-item ${isActive}" onclick="loadSession('${id}')">
                    <div class="history-title"><i class="fa-regular fa-message me-2"></i>${session.title}</div>
                    <button class="delete-chat-btn" onclick="deleteSession(event, '${id}')" title="Delete Chat">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            `;
        });
    }

    async function generateSmartTitle(promptText, sessionId) {
        try {
            const res = await fetch('/api/generate-title', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: promptText })
            });
            const data = await res.json();
            if (data.status === 'success' && data.title) {
                if (allSessions[sessionId]) {
                    allSessions[sessionId].title = data.title;
                    saveSessionsToStorage();
                    renderSidebarHistory();
                }
            }
        } catch (e) {
            console.error("Title generation failed:", e);
        }
    }

    function closeModal() {
        const modalElem = document.getElementById('uploadModal');
        const modalInstance = bootstrap.Modal.getInstance(modalElem);
        if (modalInstance) {
            modalInstance.hide();
        }
    }

    function triggerGallery() {
        closeModal();
        document.getElementById('galleryInput').click();
    }

    function triggerCamera() {
        closeModal();
        document.getElementById('cameraInput').click();
    }

    function handleFileSelect(input) {
        if (input.files && input.files[0]) {
            selectedFile = input.files[0];
            const imgURL = URL.createObjectURL(selectedFile);
            document.getElementById('previewImgThumb').src = imgURL;
            document.getElementById('imagePreviewArea').style.display = 'block';
        }
    }

    function clearImage() {
        selectedFile = null;
        document.getElementById('galleryInput').value = '';
        document.getElementById('cameraInput').value = '';
        document.getElementById('imagePreviewArea').style.display = 'none';
        document.getElementById('previewImgThumb').src = '';
    }

    document.getElementById('chatForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const sendBtn = document.getElementById('sendBtn');
        const question = questionInput.value.trim();
        if (!question && !selectedFile) return;

        if (allSessions[currentSessionId].title === 'New Chat') {
            const titlePrompt = question || (selectedFile ? "Image Analysis" : "New Conversation");
            generateSmartTitle(titlePrompt, currentSessionId);
        }

        let userContentHTML = `<strong>You</strong><br>${question.replace(/\\n/g, '<br>')}`;
        
        if (selectedFile) {
            const imgURL = URL.createObjectURL(selectedFile);
            userContentHTML = `<img src="${imgURL}" class="uploaded-img-preview"><br>` + userContentHTML;
        }

        chatBox.innerHTML += `
            <div class="message">
                <div class="avatar user-avatar">You</div>
                <div class="bubble">${userContentHTML}</div>
            </div>
        `;
        
        const formData = new FormData();
        formData.append('question', question || "Describe or analyze this image naturally.");
        formData.append('session_id', currentSessionId);
        if (selectedFile) {
            formData.append('file', selectedFile);
        }

        questionInput.value = '';
        questionInput.style.height = 'auto';
        clearImage();
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
            const response = await fetch('/api/chat', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            const loadingElem = document.getElementById(loadingId);
            
            if (data.status === 'success') {
                let htmlContent = "";
                try {
                    htmlContent = typeof marked !== 'undefined' ? marked.parse(data.response) : data.response;
                } catch(mErr) {
                    htmlContent = data.response.replace(/\\n/g, '<br>');
                }

                const bubbleElem = loadingElem.querySelector('.bubble');
                bubbleElem.innerHTML = `<strong>Tuto AI</strong><br>${htmlContent}`;
                
                processCodeBlocks(bubbleElem);
                renderMathInElem(bubbleElem);

                allSessions[currentSessionId].html = chatBox.innerHTML;
                saveSessionsToStorage();
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

def clean_ai_response(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    if "**Drafting the response:**" in text:
        text = text.split("**Drafting the response:**")[-1]
    elif "Drafting the response:" in text:
        text = text.split("Drafting the response:")[-1]
    return text.strip()

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_LAYOUT

@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    try:
        if not GROQ_API_KEY:
            return {"status": "error", "message": "GROQ_API_KEY missing."}
        
        client = Groq(api_key=GROQ_API_KEY)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            content = await audio.read()
            temp_audio.write(content)
            temp_audio_path = temp_audio.name

        with open(temp_audio_path, "rb") as file_to_transcribe:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(temp_audio_path), file_to_transcribe.read()),
                model="whisper-large-v3",
                response_format="json"
            )

        os.remove(temp_audio_path)

        return {"status": "success", "text": transcription.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-title")
async def generate_title(data: TitleRequest):
    try:
        if not GROQ_API_KEY:
            return {"status": "error", "title": "New Chat"}
        client = Groq(api_key=GROQ_API_KEY)
        
        prompt = (
            f"Generate a short, concise 2 to 4 word title representing this user prompt: '{data.prompt}'. "
            "Output ONLY the title in plain text, with no quotes, no periods, and no conversation."
        )
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=15
        )
        title = completion.choices[0].message.content.strip().replace('"', '').replace("'", "")
        return {"status": "success", "title": title}
    except Exception:
        return {"status": "error", "title": "New Chat"}

@app.post("/api/chat")
async def chat_endpoint(
    question: str = Form(...), 
    session_id: str = Form("default"),
    file: UploadFile = File(None)
):
    global chat_sessions
    try:
        if not GROQ_API_KEY:
            return {"status": "error", "message": "GROQ_API_KEY missing in Render environment."}
        
        client = Groq(api_key=GROQ_API_KEY)
        
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        SMART_SYSTEM_PROMPT = (
            "You are Tuto AI, an advanced AI tutor created and developed solely by Imran Hossen. "
            "CRITICAL IDENTITY INSTRUCTIONS:\n"
            "- If anyone asks who created, built, developed, or programmed you, ALWAYS answer that you were created by Imran Hossen.\n"
            "- Maintain this identity naturally regardless of language (English, Bangla, etc.).\n"
            "GENERAL INSTRUCTIONS:\n"
            "1. ALWAYS default to English. Switch to Bangla ONLY if the user asks in Bangla.\n"
            "2. REMEMBER past conversation context provided in the chat history.\n"
            "3. IF writing code (Python, HTML, JS, C++, etc.), ALWAYS wrap code snippets in markdown code blocks with language tags, e.g. ```python ... ```.\n"
            "4. IF solving Math/Science: Break into clear steps and use LaTeX formulas ($...$).\n"
            "5. Never output internal monologue, reasoning, or '<think>' tags."
        )

        messages_payload = [{"role": "system", "content": SMART_SYSTEM_PROMPT}]
        messages_payload.extend(chat_sessions[session_id][-10:])

        if file and file.filename:
            contents = await file.read()
            base64_image = base64.b64encode(contents).decode('utf-8')
            mime_type = file.content_type or "image/jpeg"
            image_url = f"data:{mime_type};base64,{base64_image}"

            current_user_msg = {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
            messages_payload.append(current_user_msg)

            completion = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=messages_payload
            )
            raw_response = completion.choices[0].message.content
            final_response = clean_ai_response(raw_response)
            
            chat_sessions[session_id].append({"role": "user", "content": f"[User sent image] {question}"})
            chat_sessions[session_id].append({"role": "assistant", "content": final_response})

        else:
            current_user_msg = {"role": "user", "content": question}
            messages_payload.append(current_user_msg)

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages_payload
            )
            final_response = clean_ai_response(completion.choices[0].message.content)

            chat_sessions[session_id].append(current_user_msg)
            chat_sessions[session_id].append({"role": "assistant", "content": final_response})

        return {
            "status": "success",
            "question": question,
            "response": final_response
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
