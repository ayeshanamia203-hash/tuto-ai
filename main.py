from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import HTMLResponse
import os
import uvicorn
import base64
from groq import Groq

app = FastAPI(title="Tuto AI Professional")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tuto AI - Day 7 Vision Edition</title>
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
        .bubble strong { color: #a8c7fa !important; }
        .uploaded-img-preview {
            max-width: 200px;
            border-radius: 10px;
            margin-bottom: 10px;
            border: 1px solid #444;
        }
        
        .input-wrapper {
            max-width: 850px;
            margin: 0 auto 25px auto;
            width: 90%;
            position: relative;
            display: flex;
            align-items: center;
            background-color: #1e1e20;
            border: 1px solid #3c4043;
            border-radius: 25px;
            padding: 5px 15px;
        }
        .plus-btn {
            background: none;
            border: none;
            color: var(--accent-color);
            font-size: 20px;
            cursor: pointer;
            padding: 5px 10px;
            transition: 0.2s;
        }
        .plus-btn:hover { color: #fff; }
        .chat-input {
            background: none;
            border: none;
            color: #ffffff;
            padding: 10px;
            width: 100%;
            outline: none;
            font-size: 15px;
        }
        .send-btn {
            background: none;
            border: none;
            color: var(--accent-color);
            font-size: 18px;
            cursor: pointer;
            padding: 5px 10px;
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
        
        #imagePreviewArea {
            display: none;
            padding: 5px 15px;
            background: #2b2a33;
            border-radius: 10px;
            margin-bottom: 8px;
            align-items: center;
            justify-content: space-between;
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
                    I am Tuto AI. You can now send me text or upload photos of your study materials and math problems!
                </div>
            </div>
        </div>

        <div class="container max-width-850">
            <div id="imagePreviewArea">
                <span class="text-light small" id="fileNameText"><i class="fa-solid fa-image me-2"></i>Image attached</span>
                <button type="button" class="btn-close btn-close-white btn-sm" onclick="clearImage()"></button>
            </div>

            <div class="input-wrapper">
                <button type="button" class="plus-btn" data-bs-toggle="modal" data-bs-target="#uploadModal">
                    <i class="fa-solid fa-circle-plus"></i>
                </button>
                <form id="chatForm" class="d-flex w-100 align-items-center">
                    <input type="text" id="question" class="chat-input" placeholder="Message Tuto AI or attach photo..." autocomplete="off">
                    <button type="submit" class="send-btn" id="sendBtn">
                        <i class="fa-solid fa-paper-plane"></i>
                    </button>
                </form>
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

    function triggerGallery() {
        bootstrap.Modal.getInstance(document.getElementById('uploadModal')).hide();
        document.getElementById('galleryInput').click();
    }

    function triggerCamera() {
        bootstrap.Modal.getInstance(document.getElementById('uploadModal')).hide();
        document.getElementById('cameraInput').click();
    }

    function handleFileSelect(input) {
        if (input.files && input.files[0]) {
            selectedFile = input.files[0];
            document.getElementById('fileNameText').innerText = "📷 " + selectedFile.name;
            document.getElementById('imagePreviewArea').style.display = 'flex';
        }
    }

    function clearImage() {
        selectedFile = null;
        document.getElementById('galleryInput').value = '';
        document.getElementById('cameraInput').value = '';
        document.getElementById('imagePreviewArea').style.display = 'none';
    }

    document.getElementById('chatForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const input = document.getElementById('question');
        const chatBox = document.getElementById('chatBox');
        const sendBtn = document.getElementById('sendBtn');

        const question = input.value.trim();
        if (!question && !selectedFile) return;

        let userContentHTML = `<strong>You</strong><br>${question}`;
        
        if (selectedFile) {
            const imgURL = URL.createObjectURL(selectedFile);
            userContentHTML = `<img src="${imgURL}" class="uploaded-img-preview"><br>` + userContentHTML;
        }

        chatBox.innerHTML += `
            <div class="message">
                <div class="avatar user-avatar">IH</div>
                <div class="bubble">${userContentHTML}</div>
            </div>
        `;
        
        const formData = new FormData();
        formData.append('question', question || "Please analyze this image.");
        if (selectedFile) {
            formData.append('file', selectedFile);
        }

        input.value = '';
        clearImage();
        sendBtn.disabled = true;
        chatBox.scrollTop = chatBox.scrollHeight;

        const loadingId = 'loading-' + Date.now();
        chatBox.innerHTML += `
            <div class="message" id="${loadingId}">
                <div class="avatar ai-avatar">AI</div>
                <div class="bubble text-secondary"><i class="fa-solid fa-circle-notch fa-spin me-2"></i>Analyzing & thinking...</div>
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
async def chat_endpoint(question: str = Form(...), file: UploadFile = File(None)):
    try:
        if not GROQ_API_KEY:
            return {"status": "error", "message": "GROQ_API_KEY missing in Render environment."}
        
        client = Groq(api_key=GROQ_API_KEY)
        
        # If image is attached -> Use Groq Llama 3.2 Vision Preview Model
        if file and file.filename:
            contents = await file.read()
            base64_image = base64.b64encode(contents).decode('utf-8')
            mime_type = file.content_type or "image/jpeg"
            image_url = f"data:{mime_type};base64,{base64_image}"

            completion = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"You are Tuto AI, a helpful tutor created by Imran Hossen. Answer directly based on this image: {question}"},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ]
            )
        else:
            # Text Only -> Llama 3.3
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are Tuto AI, a friendly academic assistant created by Imran Hossen. Respond clearly in whatever language the user speaks."},
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
