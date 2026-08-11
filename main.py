from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import HTMLResponse
import os
import uvicorn
import base64
import re
from groq import Groq

app = FastAPI(title="Tuto AI Professional - Natural Vision Edition")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tuto AI - Smart Vision Edition</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- KaTeX Math Rendering CSS & JS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
    
    <!-- Marked.js for Markdown Rendering -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

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
        
        /* Auto Expanding Input Box & Image Preview Box */
        .input-wrapper {
            max-width: 850px;
            margin: 0 auto 25px auto;
            width: 90%;
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

        .plus-btn {
            background: none;
            border: none;
            color: var(--accent-color);
            font-size: 20px;
            cursor: pointer;
            padding: 5px;
            margin-bottom: 3px;
            transition: 0.2s;
        }
        .plus-btn:hover { color: #fff; }

        .chat-textarea {
            background: none;
            border: none;
            color: #ffffff;
            padding: 6px 0;
            width: 100%;
            outline: none;
            font-size: 15px;
            resize: none;
            max-height: 150px;
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
                    I am Tuto AI. Send me your Math, Physics, or Chemistry problems, or share any image to chat about it!
                </div>
            </div>
        </div>

        <div class="container max-width-850">
            <div class="input-wrapper">
                <div id="imagePreviewArea">
                    <img id="previewImgThumb" src="" alt="Thumbnail">
                    <button type="button" class="close-img-btn" onclick="clearImage()"><i class="fa-solid fa-xmark"></i></button>
                </div>

                <div class="input-row">
                    <button type="button" class="plus-btn" data-bs-toggle="modal" data-bs-target="#uploadModal">
                        <i class="fa-solid fa-circle-plus"></i>
                    </button>
                    <form id="chatForm" class="d-flex w-100 align-items-end">
                        <textarea id="question" class="chat-textarea" rows="1" placeholder="Message Tuto AI or attach photo..."></textarea>
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
            window.renderMathInElement(element, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\(', right: '\\)', display: false},
                    {left: '\\[', right: '\\]', display: true}
                ],
                throwOnError : false
            });
        }
    }

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
        
        const chatBox = document.getElementById('chatBox');
        const sendBtn = document.getElementById('sendBtn');

        const question = questionInput.value.trim();
        if (!question && !selectedFile) return;

        let userContentHTML = `<strong>You</strong><br>${question.replace(/\\n/g, '<br>')}`;
        
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
        formData.append('question', question || "Describe or analyze this image naturally.");
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
                <div class="bubble text-secondary"><i class="fa-solid fa-circle-notch fa-spin me-2"></i>Analyzing...</div>
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
                const htmlContent = marked.parse(data.response);
                const bubbleElem = loadingElem.querySelector('.bubble');
                bubbleElem.innerHTML = `<strong>Tuto AI</strong><br>${htmlContent}`;
                renderMathInElem(bubbleElem);
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

@app.post("/api/chat")
async def chat_endpoint(question: str = Form(...), file: UploadFile = File(None)):
    try:
        if not GROQ_API_KEY:
            return {"status": "error", "message": "GROQ_API_KEY missing in Render environment."}
        
        client = Groq(api_key=GROQ_API_KEY)
        
        SMART_SYSTEM_PROMPT = (
            "You are Tuto AI, a friendly, intelligent AI created by Imran Hossen. "
            "INSTRUCTIONS:\n"
            "1. Respond in the language the user speaks (Bangla, English, or Banglish).\n"
            "2. IF the user shares a Math/Science/Academic problem or text: Act like an expert tutor and break it down into clear numbered steps. ALWAYS use LaTeX for math formulas ($...$ for inline, $$...$$ for display).\n"
            "3. IF the user shares a personal photo, human portrait, object, or general image: Respond warmly, naturally, and conversationally like ChatGPT/Gemini. Do NOT force 'Step 1, Step 2' or treat human photos as math problems!\n"
            "4. Never output internal monologue, reasoning, or 'Plan:'."
        )

        if file and file.filename:
            contents = await file.read()
            base64_image = base64.b64encode(contents).decode('utf-8')
            mime_type = file.content_type or "image/jpeg"
            image_url = f"data:{mime_type};base64,{base64_image}"

            completion = client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                messages=[
                    {"role": "system", "content": SMART_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ]
            )
            raw_response = completion.choices[0].message.content
            final_response = clean_ai_response(raw_response)
        else:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SMART_SYSTEM_PROMPT},
                    {"role": "user", "content": question}
                ]
            )
            final_response = completion.choices[0].message.content
        
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
