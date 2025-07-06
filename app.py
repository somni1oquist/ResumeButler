import asyncio
import streamlit as st
from constants import SUPPORTED_RESUME_TYPES
from agents.resume_agent import ResumeAgent
from semantic_kernel.agents import ChatHistoryAgentThread


# Initialisation
jd_text = ""
AGENT_AVATAR = "🤵"
USER_AVATAR = "👤"

# Functions
async def initialise_agents() -> ResumeAgent:
    """Initialise the agents for the app."""
    resume_agent = await ResumeAgent.create()
    return resume_agent

def check_required() -> bool:
    """Check if the required fields are filled."""
    passed = False
    if not resume_file:
        st.toast("Please upload your resume before proceeding.", icon=":material/warning:")
    if enable_jd and not jd_text:
        st.toast("Please enter a job description before proceeding.", icon=":material/warning:")
    else:
        passed = True
    return passed

def match_report() -> None:
    with st.spinner("Generating...", width="stretch"):
        match_report = asyncio.run(st.session_state.resume_agent.get_match_report({
            "resume_file": st.session_state.resume_file,
            "jd": jd_text,
        }, thread=st.session_state.resume_thread))
    st.session_state.messages.append({"role": "assistant", "content": match_report})
    st.chat_message("assistant", avatar=AGENT_AVATAR).markdown(match_report)

# Initialise session state variables
if "match" not in st.session_state:
    st.session_state.match = False
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "G'day! I'm your Resume Butler. Let's get started by uploading your resume and entering the job description."
    }]

if "resume_agent" not in st.session_state:
    st.session_state.resume_agent = asyncio.run(initialise_agents())

if "resume_thread" not in st.session_state:
    st.session_state.resume_thread = ChatHistoryAgentThread()

# Set the page configuration for the Streamlit app
st.set_page_config(
    page_title="Resume Butler",
    page_icon=":memo:",
    layout="wide"
)

# Sidebar configuration
st.sidebar.markdown("### Settings")
enable_jd = st.sidebar.checkbox("Analyse with JD", value=True, label_visibility="visible", disabled=True,
                                help="Enable this to analyse your resume with the job description provided.")
st.sidebar.markdown("### Upload Resume <span style='color: red;'>*</span>", unsafe_allow_html=True)
resume_file = st.sidebar.file_uploader("Resume", type=SUPPORTED_RESUME_TYPES)
if enable_jd:
    st.sidebar.markdown("### Job Description <span style='color: red;'>*</span>", unsafe_allow_html=True)
    jd_text = st.sidebar.text_area("Enter job description", height=160, label_visibility="collapsed")

st.title("Resume Butler", width="stretch")
st.caption("Your AI-powered resume butler. Upload your resume and enter job description to get started.")

for msg in st.session_state.messages:
    st.chat_message(msg["role"], avatar=AGENT_AVATAR).write(msg["content"])

# Buttons for actions
match_button, ask_button = st.columns([1, 1])
if not st.session_state.match:
    match_button = st.button("Generate Match Report", key="match_button", icon="📝",
                            help="Analyse your resume against the job description.")

if not st.session_state.match and match_button:
    if check_required():
        match_report()

user_input = st.chat_input(placeholder="Upload your resume and ask me anything about it or the job description...")
if user_input and check_required():
    # Display the user prompt
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user", avatar=USER_AVATAR).write(user_input)

    with st.spinner("Thinking...", width="stretch"):
        response = asyncio.run(st.session_state.resume_agent.ask({
            "user_input": user_input,
            "resume_file": resume_file,
            "jd": jd_text
        }, thread=st.session_state.resume_thread))

    if response and isinstance(response, str):
        st.session_state.messages.append({"role": "assistant", "content": str(response)})
        st.chat_message("assistant", avatar=AGENT_AVATAR).markdown(response)
    elif response is False:
        st.toast("Failed to generate HR response.", icon=":material/error:")