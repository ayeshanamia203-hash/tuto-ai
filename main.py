import base64
import io
import os
import re
import tempfile
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse
import google.generativeai as genai
from groq import Groq
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Tuto AI Professional Edition")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

chat_sessions = {}

class TitleRequest(BaseModel):
    prompt: str

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tuto AI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- KaTeX Math Rendering -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
    
    <!-- Marked.js -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

    <!-- Highlight.js -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>

    <style>
        :root[data-theme="dark"] {
            --bg-color: #131314;
            --sidebar-bg: #1e1e20;
            --text-color: #ffffff;
            --text-muted: #ccc;
            --accent-color: #a8c7fa;
            --border-color: #2d2d30;
            --input-bg: #1e1e20;
            --input-border: #3c4043;
            --btn-hover: #2b2a33;
            --bubble-text: #ffffff;
            --strong-color: #a8c7fa;
            --modal-bg: #1e1e20;
        }

        :root[data-theme="light"] {
            --bg-color: #ffffff;
            --sidebar-bg: #f0f4f9;
            --text-color: #1f1f1f;
            --text-muted: #555555;
            --accent-color: #0b57d0;
            --border-color: #e1e3e1;
            --input-bg: #f0f4f9;
            --input-border: #c4c7c5;
            --btn-hover: #e3e3e3;
            --bubble-text: #1f1f1f;
            --strong-color: #0b57d0;
            --modal-bg: #ffffff;
        }

        * { box-sizing: border-box; }
        html, body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
            transition: background-color 0.3s, color 0.3s;
        }
        body { display: flex; }
        .sidebar {
            width: 260px;
            background-color: var(--sidebar-bg);
            padding: 20px;
            display: flex;
            flex-direction: column;
            border-right: 1px solid var(--border-color);
            flex-shrink: 0;
            height: 100%;
            transition: all 0.3s ease;
            z-index: 1000;
        }
        .sidebar.collapsed { margin-left: -260px; }
        .sidebar-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 999;
        }
        .new-chat-btn {
            background-color: var(--input-bg);
            color: var(--text-color);
            border: 1px solid var(--border-color);
            border-radius: 30px;
            padding: 10px 15px;
            font-weight: 500;
            transition: 0.2s;
        }
        .new-chat-btn:hover { background-color: var(--btn-hover); }
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
            color: var(--text-muted);
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 5px;
            transition: background 0.2s, color 0.2s;
            user-select: none;
        }
        .history-item:hover, .history-item.active {
            background-color: var(--btn-hover);
            color: var(--text-color);
        }
        .history-title {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 150px;
        }

        .main-chat {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100vh;
            height: 100dvh;
            overflow: hidden;
            position: relative;
            transition: all 0.3s ease;
            width: 100%;
        }
        .chat-header {
            padding: 15px 25px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
        }
        .toggle-btn, .theme-btn {
            background: none;
            border: none;
            color: var(--text-color);
            font-size: 18px;
            cursor: pointer;
            padding: 6px 12px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .theme-btn { font-size: 14px; font-weight: 500; border: 1px solid var(--border-color); }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px 20px;
            max-width: 850px;
            margin: 0 auto;
            width: 100%;
            display: flex;
            flex-direction: column;
        }
        .welcome-screen {
            margin: auto 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 40px 20px;
        }
        .welcome-avatar {
            width: 54px;
            height: 54px;
            border-radius: 50%;
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: #ffffff;
            font-size: 22px;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .message { display: flex; gap: 15px; margin-bottom: 25px; position: relative; }
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
            max-width: 88%;
            font-size: 16px;
            line-height: 1.6;
            color: var(--bubble-text) !important;
            width: 100%;
            word-wrap: break-word;
        }
        .bubble strong { color: var(--strong-color) !important; }
        .bubble table { width: 100%; border-collapse: collapse; margin: 10px 0; color: var(--text-color); }
        .bubble table, .bubble th, .bubble td { border: 1px solid var(--border-color); padding: 8px; }
        .uploaded-img-preview { max-width: 200px; border-radius: 10px; margin-bottom: 10px; border: 1px solid var(--border-color); }
        .pdf-badge {
            background-color: var(--btn-hover);
            border: 1px solid #e11d48;
            color: #ff4d4d;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 14px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
        }
        .tts-btn {
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 14px;
            margin-left: 8px;
        }
        .input-container-box { padding: 10px 15px 15px 15px; background: var(--bg-color); flex-shrink: 0; width: 100%; }
        .input-wrapper {
            max-width: 850px;
            margin: 0 auto;
            width: 100%;
            background-color: var(--input-bg);
            border: 1px solid var(--input-border);
            border-radius: 24px;
            padding: 8px 15px;
            display: flex;
            flex-direction: column;
        }
        #filePreviewArea { display: none; position: relative; width: fit-content; margin-bottom: 8px; }
        #previewImgThumb { width: 70px; height: 70px; object-fit: cover; border-radius: 12px; border: 1px solid var(--border-color); }
        #pdfPreviewThumb { display: none; background: var(--btn-hover); border: 1px solid #e11d48; color: #ff4d4d; padding: 8px 12px; border-radius: 10px; font-size: 13px; }
        .close-img-btn {
            position: absolute; top: -6px; right: -6px; background: #e11d48; color: #fff;
            border: none; border-radius: 50%; width: 22px; height: 22px; font-size: 12px; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
        }
        .input-row { display: flex; align-items: center; gap: 10px; }
        .plus-btn { background: none; border: none; color: var(--accent-color); font-size: 18px; cursor: pointer; padding: 5px; }
        .chat-textarea {
            background: none; border: none; color: var(--text-color); padding: 6px 0; width: 100%;
            outline: none; font-size: 15px; resize: none; max-height: 120px; min-height: 28px; line-height: 1.4;
        }

        /* Soundwave Voice / Send Button */
        .action-btn {
            background-color: var(--text-color);
            color: var(--bg-color);
            border: none;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            flex-shrink: 0;
            font-size: 14px;
        }
        .action-btn:hover { background-color: var(--accent-color); color: #ffffff; }

        .modal-content { background-color: var(--modal-bg); color: var(--text-color); border: 1px solid var(--border-color); }
        .modal-btn {
            background-color: var(--input-bg); color: var(--text-color); border: 1px solid var(--border-color);
            border-radius: 15px; padding: 15px; width: 100%; text-align: left; margin-bottom: 10px;
        }
        .modal-btn:hover { background-color: var(--btn-hover); color: var(--accent-color); }

        /* Voice Assistant Overlay Modal */
        .voice-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(19, 19, 20, 0.95);
            z-index: 2000;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            backdrop-filter: blur(10px);
        }
        .voice-overlay.active { display: flex; }
        .voice-orb {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899);
            background-size: 200% 200%;
            animation: orbGlow 3s infinite ease-in-out;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 46px;
            box-shadow: 0 0 50px rgba(139, 92, 246, 0.5);
            margin-bottom: 30px;
        }
        .voice-orb.speaking { animation: orbPulse 0.8s infinite ease-in-out; }
        @keyframes orbGlow {
            0% { background-position: 0% 50%; transform: scale(1); }
            50% { background-position: 100% 50%; transform: scale(1.05); }
            100% { background-position: 0% 50%; transform: scale(1); }
        }
        @keyframes orbPulse {
            0% { transform: scale(1); box-shadow: 0 0 30px rgba(236, 72, 153, 0.6); }
            50% { transform: scale(1.2); box-shadow: 0 0 70px rgba(236, 72, 153, 0.9); }
            100% { transform: scale(1); box-shadow: 0 0 30px rgba(236, 72, 153, 0.6); }
        }
        .close-voice-btn {
            position: absolute;
            top: 30px;
            right: 30px;
            background: var(--btn-hover);
            border: 1px solid var(--border-color);
            color: #ffffff;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            font-size: 20px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>

    <div class="sidebar" id="sidebar">
        <div class="d-flex justify-content-between align-items-center mb-3 d-md-none">
            <span class="fw-bold">Menu</span>
            <button class="btn btn-sm text-secondary" onclick="toggleSidebar()"><i class="fa-solid fa-xmark fa-xl"></i></button>
        </div>
        <button class="new-chat-btn w-100 mb-2" onclick="startNewChat()"><i class="fa-solid fa-plus me-2"></i> New Chat</button>
        <div class="history-list" id="historyList"></div>
    </div>

    <div class="main-chat">
        <div class="chat-header">
            <div class="d-flex align-items-center">
                <button class="toggle-btn" onclick="toggleSidebar()"><i class="fa-solid fa-bars"></i></button>
                <h5 class="m-0 fw-bold ms-2"><i class="fa-solid fa-graduation-cap me-2 text-warning"></i>Tuto AI</h5>
            </div>
            <button class="theme-btn" id="themeToggleBtn" onclick="toggleTheme()"><i class="fa-solid fa-sun" id="themeIcon"></i> <span id="themeText">Light</span></button>
        </div>

        <div class="chat-container" id="chatBox"></div>

        <div class="input-container-box">
            <div class="input-wrapper">
                <div id="filePreviewArea">
                    <img id="previewImgThumb" src="" alt="Thumbnail" style="display: none;">
                    <div id="pdfPreviewThumb"><i class="fa-solid fa-file-pdf me-2"></i><span id="pdfFileName">document.pdf</span></div>
                    <button type="button" class="close-img-btn" onclick="clearSelectedFile()"><i class="fa-solid fa-xmark"></i></button>
                </div>

                <div class="input-row">
                    <button type="button" class="plus-btn" data-bs-toggle="modal" data-bs-target="#uploadModal">
                        <i class="fa-solid fa-circle-plus"></i>
                    </button>
                    <form id="chatForm" class="d-flex w-100 align-items-center gap-2 m-0">
                        <textarea id="question" class="chat-textarea" rows="1" placeholder="Message Tuto AI, attach photo or PDF..."></textarea>
                        
                        <!-- Dynamic Button: Soundwave Icon (fa-wave-square) / Send Arrow (↑) -->
                        <button type="button" class="action-btn" id="actionBtn" onclick="handleActionClick()" title="Voice Assistant / Send">
                            <i class="fa-solid fa-wave-square" id="actionIcon"></i>
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Live Voice Assistant Overlay -->
    <div class="voice-overlay" id="voiceOverlay">
        <button class="close-voice-btn" onclick="stopVoiceAssistant()"><i class="fa-solid fa-xmark"></i></button>
        <div class="voice-orb" id="voiceOrb"><i class="fa-solid fa-wave-square"></i></div>
        <h4 class="fw-bold mb-2" id="voiceStatus">Listening...</h4>
        <p class="text-secondary fs-6" id="voiceSubtext">Speak in any language</p>
    </div>

    <input type="file" id="galleryInput" accept="image/*" style="display: none;" onchange="handleFileSelect(this)">
    <input type="file" id="cameraInput" accept="image/*" capture="environment" style="display: none;" onchange="handleFileSelect(this)">
    <input type="file" id="pdfInput" accept="application/pdf" style="display: none;" onchange="handleFileSelect(this)">

    <div class="modal fade" id="uploadModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header border-0">
                    <h5 class="modal-title fw-bold"><i class="fa-solid fa-paperclip me-2 text-primary"></i>Attach File</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <button class="modal-btn" onclick="triggerCamera()"><i class="fa-solid fa-camera fa-lg me-3 text-warning"></i> <strong>Take Photo</strong></button>
                    <button class="modal-btn" onclick="triggerGallery()"><i class="fa-solid fa-images fa-lg me-3 text-info"></i> <strong>Upload Photo</strong></button>
                    <button class="modal-btn" onclick="triggerPDF()"><i class="fa-solid fa-file-pdf fa-lg me-3 text-danger"></i> <strong>Upload PDF Document</strong></button>
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
    const actionBtn = document.getElementById('actionBtn');
    const actionIcon = document.getElementById('actionIcon');
    const voiceOverlay = document.getElementById('voiceOverlay');
    const voiceOrb = document.getElementById('voiceOrb');
    const voiceStatus = document.getElementById('voiceStatus');

    let allSessions = JSON.parse(localStorage.getItem('tuto_all_sessions')) || {};
    let currentSessionId = localStorage.getItem('tuto_current_session_id') || null;

    let recognition = null;
    let isVoiceAssistantActive = false;

    // Toggle Soundwave Icon (fa-wave-square) and Send Arrow (↑)
    function updateActionButtonState() {
        const hasContent = questionInput.value.trim().length > 0 || selectedFile !== null;
        if (hasContent) {
            actionIcon.className = "fa-solid fa-arrow-up";
            actionBtn.title = "Send Message";
        } else {
            actionIcon.className = "fa-solid fa-wave-square";
            actionBtn.title = "Voice Assistant";
        }
    }

    function handleActionClick() {
        const hasContent = questionInput.value.trim().length > 0 || selectedFile !== null;
        if (hasContent) {
            submitChatMessage();
        } else {
            startVoiceAssistant();
        }
    }

    /* Live Interactive Voice Assistant Mode */
    function startVoiceAssistant() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Your browser does not support Speech Recognition. Please use Chrome/Edge.");
            return;
        }

        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = ''; // Auto-detect language

        isVoiceAssistantActive = true;
        voiceOverlay.classList.add('active');
        voiceStatus.innerText = "Listening...";
        voiceOrb.classList.remove('speaking');

        recognition.start();

        recognition.onresult = async (event) => {
            const userSpeech = event.results[0][0].transcript;
            voiceStatus.innerText = "Thinking...";
            questionInput.value = userSpeech;
            
            // Send user speech to AI backend
            const aiResponse = await submitChatMessage(true);
            
            if (aiResponse && isVoiceAssistantActive) {
                speakVoiceAssistantResponse(aiResponse);
            } else {
                stopVoiceAssistant();
            }
        };

        recognition.onerror = () => {
            if (isVoiceAssistantActive) stopVoiceAssistant();
        };

        recognition.onend = () => {
            if (isVoiceAssistantActive && voiceStatus.innerText === "Listening...") {
                stopVoiceAssistant();
            }
        };
    }

    function speakVoiceAssistantResponse(text) {
        if (!('speechSynthesis' in window)) {
            stopVoiceAssistant();
            return;
        }

        window.speechSynthesis.cancel();
        let cleanText = text.replace(/<[^>]*>?/gm, '').replace(/[*#]/g, '');
        const utterance = new SpeechSynthesisUtterance(cleanText);

        if (/[\u0980-\u09FF]/.test(cleanText)) {
            utterance.lang = 'bn-BD';
        } else {
            utterance.lang = 'en-US';
        }

        voiceStatus.innerText = "Tuto AI Speaking...";
        voiceOrb.classList.add('speaking');

        utterance.onend = () => {
            if (isVoiceAssistantActive) {
                startVoiceAssistant();
            }
        };

        utterance.onerror = () => { stopVoiceAssistant(); };

        window.speechSynthesis.speak(utterance);
    }

    function stopVoiceAssistant() {
        isVoiceAssistantActive = false;
        if (recognition) {
            try { recognition.stop(); } catch(e){}
        }
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        voiceOverlay.classList.remove('active');
        voiceOrb.classList.remove('speaking');
    }

    function initTheme() {
        const savedTheme = localStorage.getItem('tuto_theme') || 'dark';
        setTheme(savedTheme);
    }

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        setTheme(currentTheme === 'dark' ? 'light' : 'dark');
    }

    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('tuto_theme', theme);
        document.getElementById('themeIcon').className = theme === 'light' ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
        document.getElementById('themeText').innerText = theme === 'light' ? 'Dark' : 'Light';
    }

    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        sidebar.classList.toggle('collapsed');
        if (window.innerWidth <= 768) {
            overlay.classList.toggle('active', !sidebar.classList.contains('collapsed'));
        }
    }

    function checkMobileSidebarAutoCollapse() {
        if (window.innerWidth <= 768) {
            document.getElementById('sidebar').classList.add('collapsed');
            document.getElementById('sidebarOverlay').classList.remove('active');
        }
    }

    function speakText(btn) {
        if (!('speechSynthesis' in window)) return;
        const bubbleElem = btn.closest('.bubble');
        let textToSpeak = bubbleElem ? bubbleElem.innerText.replace(/^Tuto AI/i, '').trim() : '';
        
        if (window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
            btn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
            return;
        }

        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        utterance.lang = /[\u0980-\u09FF]/.test(textToSpeak) ? 'bn-BD' : 'en-US';
        btn.innerHTML = '<i class="fa-solid fa-volume-xmark text-warning"></i>';
        utterance.onend = () => { btn.innerHTML = '<i class="fa-solid fa-volume-high"></i>'; };
        utterance.onerror = () => { btn.innerHTML = '<i class="fa-solid fa-volume-high"></i>'; };
        window.speechSynthesis.speak(utterance);
    }

    const DEFAULT_WELCOME = `
        <div id="welcomeScreen" class="welcome-screen">
            <div class="welcome-avatar mb-3">AI</div>
            <h2 class="fw-bold mb-2">Hello there!</h2>
            <p class="text-secondary fs-5 m-0">How can I assist you today?</p>
        </div>
    `;

    window.addEventListener('DOMContentLoaded', () => {
        initTheme();
        checkMobileSidebarAutoCollapse();
        if (!currentSessionId || !allSessions[currentSessionId]) {
            startNewChat(false);
        } else {
            renderSidebarHistory();
            loadSession(currentSessionId);
        }
        updateActionButtonState();
    });

    questionInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        updateActionButtonState();
    });

    questionInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitChatMessage();
        }
    });

    function saveSessionsToStorage() {
        localStorage.setItem('tuto_all_sessions', JSON.stringify(allSessions));
        localStorage.setItem('tuto_current_session_id', currentSessionId);
    }

    function startNewChat(shouldRender = true) {
        currentSessionId = 'session_' + Date.now();
        allSessions[currentSessionId] = { title: 'New Chat', html: DEFAULT_WELCOME, messages: [], isPinned: false };
        saveSessionsToStorage();
        if (shouldRender) {
            renderSidebarHistory();
            loadSession(currentSessionId);
        }
        checkMobileSidebarAutoCollapse();
    }

    function loadSession(sessionId) {
        currentSessionId = sessionId;
        saveSessionsToStorage();
        chatBox.innerHTML = allSessions[sessionId].html || DEFAULT_WELCOME;
        chatBox.scrollTop = chatBox.scrollHeight;
        renderSidebarHistory();
        checkMobileSidebarAutoCollapse();
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
                </div>
            `;
        });
    }

    function triggerGallery() { closeModal(); document.getElementById('galleryInput').click(); }
    function triggerCamera() { closeModal(); document.getElementById('cameraInput').click(); }
    function triggerPDF() { closeModal(); document.getElementById('pdfInput').click(); }
    function closeModal() {
        const modalElem = document.getElementById('uploadModal');
        const modalInstance = bootstrap.Modal.getInstance(modalElem);
        if (modalInstance) modalInstance.hide();
    }

    function handleFileSelect(input) {
        if (input.files && input.files[0]) {
            selectedFile = input.files[0];
            const previewArea = document.getElementById('filePreviewArea');
            const imgThumb = document.getElementById('previewImgThumb');
            const pdfThumb = document.getElementById('pdfPreviewThumb');

            if (selectedFile.type === 'application/pdf') {
                imgThumb.style.display = 'none';
                pdfThumb.style.display = 'inline-block';
                document.getElementById('pdfFileName').innerText = selectedFile.name;
            } else {
                pdfThumb.style.display = 'none';
                imgThumb.style.display = 'block';
                imgThumb.src = URL.createObjectURL(selectedFile);
            }
            previewArea.style.display = 'block';
            updateActionButtonState();
        }
    }

    function clearSelectedFile() {
        selectedFile = null;
        document.getElementById('filePreviewArea').style.display = 'none';
        updateActionButtonState();
    }

    document.getElementById('chatForm').addEventListener('submit', (e) => {
        e.preventDefault();
        submitChatMessage();
    });

    async function submitChatMessage(isVoiceMode = false) {
        const question = questionInput.value.trim();
        if (!question && !selectedFile) return null;

        const welcomeElem = document.getElementById('welcomeScreen');
        if (welcomeElem) chatBox.innerHTML = '';

        let userContentHTML = question ? `<strong>You</strong><br>${question.replace(/\n/g, '<br>')}` : '';
        if (selectedFile) {
            if (selectedFile.type === 'application/pdf') {
                userContentHTML = `<div class="pdf-badge"><i class="fa-solid fa-file-pdf"></i> ${selectedFile.name}</div>` + (userContentHTML ? `<br>${userContentHTML}` : '');
            } else {
                const imgURL = URL.createObjectURL(selectedFile);
                userContentHTML = `<img src="${imgURL}" class="uploaded-img-preview">` + (userContentHTML ? `<br>${userContentHTML}` : '');
            }
        }

        chatBox.innerHTML += `
            <div class="message">
                <div class="avatar user-avatar">You</div>
                <div class="bubble">${userContentHTML}</div>
            </div>
        `;
        
        const formData = new FormData();
        formData.append('question', question);
        formData.append('session_id', currentSessionId);
        if (selectedFile) formData.append('file', selectedFile);

        questionInput.value = '';
        questionInput.style.height = 'auto';
        clearSelectedFile();
        updateActionButtonState();
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
            const response = await fetch('/api/chat', { method: 'POST', body: formData });
            const data = await response.json();
            const loadingElem = document.getElementById(loadingId);
            
            if (data.status === 'success') {
                let htmlContent = typeof marked !== 'undefined' ? marked.parse(data.response) : data.response;
                const bubbleElem = loadingElem.querySelector('.bubble');
                bubbleElem.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <strong>Tuto AI</strong>
                        <button type="button" class="tts-btn" onclick="speakText(this)"><i class="fa-solid fa-volume-high"></i></button>
                    </div>
                    <div>${htmlContent}</div>
                `;
                allSessions[currentSessionId].html = chatBox.innerHTML;
                saveSessionsToStorage();
                return data.response;
            } else {
                loadingElem.querySelector('.bubble').innerHTML = `<span class="text-danger">Error: ${data.message}</span>`;
                return null;
            }
        } catch (error) {
            document.getElementById(loadingId).querySelector('.bubble').innerHTML = `<span class="text-danger">Server connection error.</span>`;
            return null;
        } finally {
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }
</script>
</body>
</html>
"""

def clean_ai_response(text: str) -> str:
    if not text: return ""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return text.strip()

def extract_pdf_text(contents: bytes) -> str:
    pdf_text = ""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(contents))
        for page in reader.pages:
            t = page.extract_text()
            if t: pdf_text += t + "\n"
    except Exception:
        raw_matches = re.findall(rb'\((.*?)\)', contents)
        extracted_strings = [m.decode('utf-8', errors='ignore') for m in raw_matches if len(m) > 3]
        pdf_text = " ".join(extracted_strings)
    return pdf_text.strip()

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_LAYOUT

@app.post("/api/chat")
async def chat_endpoint(
    question: str = Form(""), 
    session_id: str = Form("default"),
    file: UploadFile = File(None)
):
    global chat_sessions
    try:
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        SMART_SYSTEM_PROMPT = (
            "You are Tuto AI, an interactive, friendly AI tutor created solely by Imran Hossen. "
            "Answer concisely and naturally in whatever language the user speaks to you."
        )

        messages_payload = [{"role": "system", "content": SMART_SYSTEM_PROMPT}]
        messages_payload.extend(chat_sessions[session_id][-10:])

        if file and file.filename:
            filename = file.filename.lower()
            contents = await file.read()

            if filename.endswith(".pdf"):
                if not GROQ_API_KEY:
                    return {"status": "error", "message": "GROQ_API_KEY missing."}
                client = Groq(api_key=GROQ_API_KEY)
                user_q = question if question else "Summarize key points from this document."
                extracted_text = extract_pdf_text(contents)
                pdf_prompt = f"PDF Text:\n{extracted_text[:6000]}\n\nUser Question: {user_q}"
                
                messages_payload.append({"role": "user", "content": pdf_prompt})
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_payload
                )
                final_response = clean_ai_response(completion.choices[0].message.content)
                return {"status": "success", "question": user_q, "response": final_response}

            else:
                if not GEMINI_API_KEY:
                    return {"status": "error", "message": "GEMINI_API_KEY missing."}

                genai.configure(api_key=GEMINI_API_KEY)
                mime_type = file.content_type or "image/jpeg"
                image_parts = [{"mime_type": mime_type, "data": contents}]
                user_q = question if question else "Acknowledge image."

                gemini_model = genai.GenerativeModel('models/gemini-1.5-flash')
                response = gemini_model.generate_content([f"{SMART_SYSTEM_PROMPT}\n{user_q}", image_parts[0]])
                
                final_response = clean_ai_response(response.text)
                return {"status": "success", "question": user_q, "response": final_response}

        else:
            if not GROQ_API_KEY:
                return {"status": "error", "message": "GROQ_API_KEY missing."}
            
            client = Groq(api_key=GROQ_API_KEY)
            messages_payload.append({"role": "user", "content": question})

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages_payload
            )

            final_response = clean_ai_response(completion.choices[0].message.content)
            return {"status": "success", "question": question, "response": final_response}

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
