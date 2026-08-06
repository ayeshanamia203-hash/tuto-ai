# app.py - Streamlit Frontend Interface
import streamlit as st
from ai_brain import ask_ai_tutor, extract_text_from_pdf

st.set_page_config(page_title="Tuto - AI Tutor", page_icon="🤖", layout="wide")

# App Header
st.title("🤖 Tuto - AI Tutor")
st.caption("Your Personal AI Study Companion | Built by Imran Hossen")

# Sidebar Configuration
st.sidebar.header("🎓 Learning Context")

grade = st.sidebar.selectbox(
    "Select Grade / Level:",
    ["General / Self-Learner", "Class 6-8", "Class 9-10 / SSC", "HSC / College", "University / Undergraduate"]
)

subject = st.sidebar.selectbox(
    "Select Subject:",
    ["General Studies", "Mathematics", "Physics", "Chemistry", "Biology", "English", "ICT / Computer Science"]
)

st.sidebar.markdown("---")
st.sidebar.header("📄 Upload Study Material")
uploaded_file = st.sidebar.file_uploader(
    "Upload PDF or Photo (Book/Notes):", 
    type=["pdf", "png", "jpg", "jpeg"]
)

extracted_pdf_text = ""
image_data = None

if uploaded_file is not None:
    file_type = uploaded_file.name.split(".")[-1].lower()
    
    if file_type == "pdf":
        with st.spinner("Extracting text from PDF..."):
            extracted_pdf_text = extract_text_from_pdf(uploaded_file)
            st.sidebar.success("PDF Loaded Successfully! ✅")
    elif file_type in ["png", "jpg", "jpeg"]:
        image_data = uploaded_file
        st.sidebar.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        st.sidebar.success("Image Loaded Successfully! 📸")

if st.sidebar.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Prior Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Box
if prompt := st.chat_input("Ask Tuto anything about your studies..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Tuto is thinking..."):
            response = ask_ai_tutor(
                user_question=prompt,
                chat_history=st.session_state.messages[:-1],
                grade=grade,
                subject=subject,
                context_text=extracted_pdf_text,
                image_file=image_data
            )
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
