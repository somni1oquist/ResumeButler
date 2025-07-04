import asyncio
import streamlit as st
from chat import chat, match


# Initialisation
jd_text = ""
# Set the page configuration for the Streamlit app
st.set_page_config(
    page_title="Resume Butler",
    page_icon=":memo:",
    layout="wide"
)

# Sidebar configuration
with st.sidebar:
    st.markdown("### Settings")
    enable_jd = st.checkbox("Analyse with JD", value=True, label_visibility="visible", disabled=True,
                                  help="Enable this to analyse your resume with the job description provided.")
    st.markdown("### Upload Resume <span style='color: red;'>*</span>", unsafe_allow_html=True)
    resume_file = st.file_uploader("Upload your resume", type=["pdf", "docx"],
                                   label_visibility="collapsed",
                                   on_change=lambda: st.session_state.update({"ready": False, "matched": False}))
    if enable_jd:
        st.markdown("### Job Description <span style='color: red;'>*</span>", unsafe_allow_html=True)
        jd_text = st.text_area("Enter job description", height=160, label_visibility="collapsed",
                               on_change=lambda: st.session_state.update({"ready": False, "matched": False}))

st.title("Resume Butler", width="stretch")
st.caption("Your AI-powered resume butler. Upload your resume and enter job description to get started, or ask me to create a new resume!")

# Check if the session state is initialised
if "ready" not in st.session_state:
    st.session_state.ready = False
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "G'day! I'm your Resume Butler. I can help you in multiple ways:\n\n🔍 **Analyze existing resume** - Upload your resume and job description for analysis\n🚀 **Create new resume** - Just say 'create resume' and I'll guide you through building one from scratch\n🔄 **Improve existing resume** - Say 'rewrite resume' to enhance your current resume\n\nWhat would you like to do today?"
    }]
if "matched" not in st.session_state:
    st.session_state.matched = False

for msg in st.session_state.messages:
    st.chat_message(msg["role"], avatar="🤵").write(msg["content"])

if not st.session_state.ready:
    st.button("Generate Match Report", key="ready_button", use_container_width=True,
              disabled=not resume_file or (enable_jd and not jd_text),
              help="Click when you are ready to start the analysis.", icon="📝",
              on_click=lambda: st.session_state.update({"ready": True}))
    
    # Add quick start buttons for agent features
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Create New Resume", use_container_width=True, 
                     help="Start creating a resume from scratch"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "I want to create a new resume"
            })
            st.rerun()
    
    with col2:
        if st.button("🔄 Improve Resume", use_container_width=True, 
                     help="Improve an existing resume",
                     disabled=not resume_file):
            st.session_state.messages.append({
                "role": "user", 
                "content": "I want to rewrite and improve my resume"
            })
            st.rerun()

if st.session_state.ready:
    if resume_file is None:
        st.toast("Please upload your resume file before proceeding.", icon=":material/warning:")
    elif enable_jd and not jd_text:
        st.toast("Please enter a job description to proceed.", icon=":material/warning:")
    else:
        # If the match report is not generated yet, generate it
        if st.session_state.matched is False:
            with st.spinner("Generating...", width="stretch"):
                match_report = asyncio.run(match(resume_file, jd_text))
            st.session_state.messages.append({"role": "assistant", "content": match_report})
            st.chat_message("assistant", avatar="🤵").markdown(match_report)
            st.session_state.matched = True

        # If the user is ready, allow them to ask questions
        if user_prompt := st.chat_input(placeholder="Ask me anything about your resume, job description, or say 'create resume' to start fresh!"):
            # Display the user prompt
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            st.chat_message("user", avatar="👤").write(user_prompt)

            with st.spinner("Thinking...", width="stretch"):
                response = asyncio.run(chat(user_prompt))

            if response and isinstance(response, str):
                st.session_state.messages.append({"role": "assistant", "content": str(response)})
                st.chat_message("assistant", avatar="🤵").markdown(response)
            elif response is False:
                st.toast("Failed to generate HR response.", icon=":material/error:")

# Handle agent mode interactions even when not ready
elif user_prompt := st.chat_input(placeholder="Ask me anything or say 'create resume' to get started!"):
    # Display the user prompt
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    st.chat_message("user", avatar="👤").write(user_prompt)

    with st.spinner("Thinking...", width="stretch"):
        response = asyncio.run(chat(user_prompt))

    if response and isinstance(response, str):
        st.session_state.messages.append({"role": "assistant", "content": str(response)})
        st.chat_message("assistant", avatar="🤵").markdown(response)
    elif response is False:
        st.toast("Failed to generate response.", icon=":material/error:")
