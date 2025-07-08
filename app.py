import asyncio
import streamlit as st
from constants import SUPPORTED_RESUME_TYPES
from agents.orchestrator_agent import OrchestratorAgent
from semantic_kernel.agents import AgentGroupChat


# Initialisation
jd = ""
AGENT_AVATAR = "🤵"
USER_AVATAR = "👤"
file_type = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "md": "text/markdown",
}

# Functions
def random_str(length: int = 8) -> str:
    """Generate a random string of fixed length."""
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def check_required() -> bool:
    """Check if the required fields are filled."""
    passed = False
    if not resume_file:
        st.toast("Please upload your resume before proceeding.", icon=":material/warning:")
    if enable_jd and not jd:
        st.toast("Please enter a job description before proceeding.", icon=":material/warning:")
    else:
        passed = True
    return passed

def display_result(response) -> None:
    """Display the result of the agent's response."""
    if response and isinstance(response, str):
        st.session_state.messages.append({"role": "assistant", "content": str(response)})
        st.chat_message("assistant", avatar=AGENT_AVATAR).markdown(response)
    elif isinstance(response, dict) and "tool_output" in response:
        tool_output = response.get("tool_output")
        if tool_output:
            if isinstance(tool_output, str):
                st.session_state.messages.append({"role": "assistant", "content": str(tool_output)})
                st.chat_message("assistant", avatar=AGENT_AVATAR).markdown(tool_output)

            elif isinstance(tool_output, dict) and "content" in tool_output:
                file_ext = tool_output.get("ext", "txt")
                file_name = f"revised_resume-{random_str()}.{file_ext}"
                file_content = tool_output.get("content")

                if not file_content:
                    st.toast("No content generated for the revised resume.", icon=":material/error:")
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Revised resume generated: {file_name}"
                    })
                    st.chat_message("assistant", avatar=AGENT_AVATAR).markdown(f"Revised resume generated: {file_name}")
                    st.download_button(
                        label=f"{file_name}",
                        icon=":material/download_2:",
                        data=file_content,
                        file_name=file_name,
                        mime=file_type.get(file_ext, 'application/octet-stream'),
                        key="download_revised_resume"
                    )
    else:
        st.toast("Failed to generate HR response.", icon=":material/error:")

def match_report() -> None:
    with st.spinner("Generating...", width="stretch"):
        match_prompt = "Please provide a match report based on the uploaded resume and optional job description."
        match_report = asyncio.run(st.session_state.recruiter_agent.ask({
            "user_input": match_prompt,
            "resume_file": resume_file,
            "jd": jd,
        }))
    st.session_state.messages.append({"role": "assistant", "content": match_report})
    st.chat_message("assistant", avatar=AGENT_AVATAR).markdown(match_report)

# Initialise session state variables
if "match_clicked" not in st.session_state:
    st.session_state.match_clicked = False
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "G'day! I'm your Resume Butler. Let's get started by uploading your resume and entering the job description."
    }]

if "agent" not in st.session_state:
    st.session_state.agent = asyncio.run(OrchestratorAgent.create())
if "thread" not in st.session_state:
    st.session_state.thread = None

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
    jd = st.sidebar.text_area("Enter job description", height=160, label_visibility="collapsed")

st.title("Resume Butler", width="stretch")
st.caption("Your AI-powered resume butler. Upload your resume and enter job description to get started.")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message(msg["role"], avatar=USER_AVATAR).write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message(msg["role"], avatar=AGENT_AVATAR).write(msg["content"])

# Buttons for actions
if not st.session_state.get("match_clicked", False):
    if match_btn := st.button(
        "Generate Match Report",
        key="match_btn",
        icon="📝"
    ):
        if check_required():
            st.session_state.match_clicked = True
            st.rerun()

if st.session_state.get("match_clicked", False):
    match_report()
    st.session_state.match_clicked = False

user_input = st.chat_input(placeholder="Upload your resume and ask me anything about it or the job description...")
if user_input and check_required():
    # Display the user prompt
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user", avatar=USER_AVATAR).write(user_input)

    with st.spinner("Thinking...", width="stretch"):
        profile = {
            "resume": resume_file,
            "jd": jd
        }
        response = asyncio.run()

    display_result(response)
