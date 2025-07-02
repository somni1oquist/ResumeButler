import os
import streamlit as st


# Set the page configuration for the Streamlit app
st.set_page_config(
    page_title="Resume Butler",
    page_icon=":memo:",
    layout="wide"
)

# Sidebar configuration
with st.sidebar:
    st.markdown("### Settings")
    enable_jd = st.checkbox("Analyse with JD", value=True, label_visibility="visible",
                                  help="Enable this to analyse your resume with the job description provided.")
    st.markdown("### Upload Resume <span style='color: red;'>*</span>", unsafe_allow_html=True)
    resume_file = st.file_uploader("Upload your resume", type=["pdf", "docx"], label_visibility="collapsed")
    jd_text = None
    if enable_jd:
        st.markdown("### Job Description <span style='color: red;'>*</span>", unsafe_allow_html=True)
        jd_text = st.text_area("Enter job description", height=160, label_visibility="collapsed")

st.title("Resume Butler", width="stretch")
st.caption("Your AI-powered resume butler. Upload your resume and enter job description to get started.")

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "G'day! I'm your Resume Butler. Let's get started by uploading your resume and entering the job description."
    }]

for msg in st.session_state.messages:
    st.chat_message(msg["role"], avatar="🤵").markdown(msg["content"])

if user_prompt := st.chat_input(placeholder="Ask me anything about your resume or job description..."):
    if resume_file is None:
        st.toast("Please upload your resume file before proceeding.", icon=":material/warning:")
    elif enable_jd and not jd_text:
        st.toast("Please enter a job description to proceed.", icon=":material/warning:")
    else:
        # Display the user prompt
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        st.chat_message("user", avatar="👤").write(user_prompt)