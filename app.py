from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from ai_brain import ask_ai_tutor

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    history: list = []

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=HTML_PAGE)

@app.post("/chat")
async def chat(req: ChatRequest):
    # Build history in the format ai_brain expects
    history = [{"role": m["role"], "content": m["content"]} for m in req.history]
    response = ask_ai_tutor(req.message, history)
    return {"response": response}

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Tuto – AI Tutor</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #f0f2ff;
      height: 100dvh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* ── Header ── */
    header {
      background: linear-gradient(135deg, #4F46E5, #7C3AED);
      color: white;
      padding: 14px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      box-shadow: 0 2px 8px rgba(79,70,229,0.3);
      flex-shrink: 0;
    }
    header .logo { font-size: 1.8rem; }
    header h1 { font-size: 1.25rem; font-weight: 700; letter-spacing: -0.3px; }
    header p  { font-size: 0.78rem; opacity: 0.85; margin-top: 1px; }
    .clear-btn {
      margin-left: auto;
      background: rgba(255,255,255,0.18);
      border: 1px solid rgba(255,255,255,0.3);
      color: white;
      border-radius: 8px;
      padding: 6px 14px;
      font-size: 0.8rem;
      cursor: pointer;
      transition: background 0.2s;
    }
    .clear-btn:hover { background: rgba(255,255,255,0.28); }

    /* ── Chat area ── */
    #chat {
      flex: 1;
      overflow-y: auto;
      padding: 20px 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .msg {
      display: flex;
      gap: 10px;
      max-width: 85%;
      animation: fadeIn 0.25s ease;
    }
    @keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }

    .msg.user { align-self: flex-end; flex-direction: row-reverse; }
    .msg.bot  { align-self: flex-start; }

    .avatar {
      width: 34px; height: 34px;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.1rem;
      flex-shrink: 0;
    }
    .msg.bot  .avatar { background: linear-gradient(135deg,#4F46E5,#7C3AED); }
    .msg.user .avatar { background: linear-gradient(135deg,#059669,#10B981); }

    .bubble {
      padding: 11px 15px;
      border-radius: 18px;
      font-size: 0.93rem;
      line-height: 1.55;
      word-wrap: break-word;
    }
    .msg.bot  .bubble {
      background: white;
      color: #1f2937;
      border-bottom-left-radius: 4px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .msg.user .bubble {
      background: linear-gradient(135deg,#4F46E5,#7C3AED);
      color: white;
      border-bottom-right-radius: 4px;
    }

    /* ── Typing indicator ── */
    .typing .bubble {
      display: flex; gap: 5px; align-items: center;
      padding: 14px 18px;
    }
    .dot {
      width: 7px; height: 7px;
      border-radius: 50%;
      background: #9CA3AF;
      animation: bounce 1.2s infinite;
    }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes bounce {
      0%,60%,100% { transform: translateY(0); }
      30%          { transform: translateY(-6px); }
    }

    /* ── Input bar ── */
    #input-bar {
      display: flex;
      gap: 10px;
      padding: 14px 16px;
      background: white;
      border-top: 1px solid #e5e7eb;
      flex-shrink: 0;
    }
    #msg-input {
      flex: 1;
      border: 1.5px solid #d1d5db;
      border-radius: 24px;
      padding: 10px 18px;
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.2s;
      resize: none;
      line-height: 1.4;
      max-height: 120px;
      overflow-y: auto;
    }
    #msg-input:focus { border-color: #4F46E5; }
    #send-btn {
      width: 44px; height: 44px;
      border-radius: 50%;
      background: linear-gradient(135deg,#4F46E5,#7C3AED);
      border: none;
      color: white;
      font-size: 1.2rem;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
      transition: opacity 0.2s, transform 0.1s;
    }
    #send-btn:hover  { opacity: 0.9; }
    #send-btn:active { transform: scale(0.93); }
    #send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  </style>
</head>
<body>

<header>
  <div class="logo">🎓</div>
  <div>
    <h1>Tuto</h1>
    <p>AI Educational Tutor · GlobalTutor</p>
  </div>
  <button class="clear-btn" onclick="clearChat()">Clear</button>
</header>

<div id="chat"></div>

<div id="input-bar">
  <textarea id="msg-input" rows="1" placeholder="Ask Tuto anything…"></textarea>
  <button id="send-btn" onclick="sendMessage()">&#9650;</button>
</div>

<script>
  const chat     = document.getElementById('chat');
  const input    = document.getElementById('msg-input');
  const sendBtn  = document.getElementById('send-btn');
  let history    = [];

  function addMessage(role, text) {
    const isBot = role === 'bot';
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    div.innerHTML = `
      <div class="avatar">${isBot ? '🎓' : '🧑‍🎓'}</div>
      <div class="bubble">${escapeHtml(text).replace(/\\n/g,'<br>')}</div>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
    return div;
  }

  function addTyping() {
    const div = document.createElement('div');
    div.className = 'msg bot typing';
    div.id = 'typing';
    div.innerHTML = `<div class="avatar">🎓</div>
      <div class="bubble"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  function removeTyping() {
    const t = document.getElementById('typing');
    if (t) t.remove();
  }

  function escapeHtml(t) {
    return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;

    addMessage('user', text);
    addTyping();

    history.push({ role: 'user', content: text });

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history: history.slice(0,-1) })
      });
      const data = await res.json();
      removeTyping();
      addMessage('bot', data.response);
      history.push({ role: 'assistant', content: data.response });
    } catch(e) {
      removeTyping();
      addMessage('bot', 'Sorry, something went wrong. Please try again.');
    }

    sendBtn.disabled = false;
    input.focus();
  }

  function clearChat() {
    history = [];
    chat.innerHTML = '';
    greeting();
  }

  function greeting() {
    addMessage('bot',
      "Hi! I'm Tuto, your AI tutor from GlobalTutor 👋\\n\\n" +
      "I can help with Math, Science, English, Bangla, and any subject you're studying. Ask me anything!\\n\\n" +
      "আমি বাংলায়ও সাহায্য করতে পারি।"
    );
  }

  // Auto-grow textarea
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  });

  // Send on Enter (Shift+Enter for newline)
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  greeting();
</script>
</body>
</html>"""
