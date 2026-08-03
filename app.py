import streamlit as st
from ai_brain import ask_ai_tutor

# পেজ সেটিংস ও সুন্দর টাইটেল
st.set_page_config(page_title="Tuto - AI Tutor", page_icon="🤖", layout="centered")

st.title("🤖 Tuto - AI Tutor")
st.write("Welcome! Ask me anything about your studies.")

# চ্যাট হিস্ট্রি ধরে রাখার জন্য Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# আগের চ্যাট হিস্ট্রি স্ক্রিনে দেখানো
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ইউজার মেসেজ ইনপুট বক্স (Gemini/ChatGPT এর মতো)
if prompt := st.chat_input("Type your question here..."):
    # ইউজারের মেসেজ চ্যাটে দেখানো ও সেভ করা
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI এর উত্তরের জন্য অপেক্ষা ও রেসপন্স আনা
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            history_for_ai = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
            response = ask_ai_tutor(prompt, history_for_ai)
            st.markdown(response)
    
    # AI এর উত্তর চ্যাট হিস্ট্রিতে সেভ করা
    st.session_state.messages.append({"role": "assistant", "content": response})
