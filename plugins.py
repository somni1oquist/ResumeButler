import io
from kernel import get_kernel
from utils import load_prompt
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.contents.utils.author_role import AuthorRole
from docx import Document
from constants import ServiceIDs
from user_profile import UserProfile


class RecruiterPlugin:
    """Plugin to analyse resumes and when job description is provided, generate match reports."""

    @kernel_function(name="get_match_report", description="Generate a match report between the resume and job description.")
    async def get_match_report(self, resume: str, jd: str | None = None) -> str:
        """Generate a match report between the resume and job description."""
        match_args = KernelArguments(resume=resume, jd=jd)
        match_prompt = await load_prompt("match", match_args)
        # Process with user profile if match prompt is found
        kernel, request_settings = get_kernel()
        request_settings.service_id = ServiceIDs.AZURE_HR_SERVICE
        result = None
        profile = UserProfile(resume=resume, jd=jd)
        if match_prompt and profile:
            result = await kernel.invoke_prompt(
                prompt=match_prompt,
                settings=request_settings,
                user_profile=profile,
                arguments=KernelArguments(user_profile=profile)
            )
        # Process without user profile if match prompt is found
        elif match_prompt:
            result = await kernel.invoke_prompt(
                prompt=match_prompt,
                settings=request_settings
            )

        if result and result.value:
            return result.value[0].content if isinstance(result.value, list) else result.value

        return "Failed to generate match report. Please check the input data or try again later."

class RevisionPlugin:
    """Plugin to handle resume revision based on user profile."""

    @kernel_function(name="revise_resume", description="Revise/update/edit/rewrite the resume based on JD optionally.")
    async def revise_resume(self, resume: str, jd: str | None = None) -> str:
        prompt = await self.get_revise_prompt(resume, jd)
        kernel, request_settings = get_kernel()
        request_settings.service_id = ServiceIDs.AZURE_HR_SERVICE
        result = await kernel.invoke_prompt(prompt=prompt, settings=request_settings)

        if result and result.value:
            return result.value[0].content if isinstance(result.value, list) else result.value

        return "Failed to revise the resume. Please check the input data or try again later."

    @kernel_function(name="reformat_content", description="Reformat the content to ensure it is suitable to export.")
    async def reformat_content(self, content: str) -> str:
        """Reformat the content to ensure it is suitable to export."""
        if not content:
            raise ValueError("Content cannot be empty.")
        prompt = "Instruction: " \
                "If not markdown, remove any markdown formatting and ensure the content is clean and ready for export. " \
                "If it is markdown, ensure it is properly formatted. " \
                "Return the reformatted content without any additional comments or notes." \
                f"\n\nContent:\n{content}"
        kernel, request_settings = get_kernel()
        request_settings.service_id = ServiceIDs.AZURE_HR_SERVICE
        result = await kernel.invoke_prompt(prompt=prompt, settings=request_settings)
        if result and result.value:
            return result.value[0].content if isinstance(result.value, list) else result.value

        return "Failed to reformat the content. Please check the input data or try again later."

    @kernel_function(name="export_txt", description="Export in txt format.")
    def export_txt(self, content: str) -> bytes:
        """Export the content as a text file."""
        if not content:
            raise ValueError("Content cannot be empty.")
        return content.encode('utf-8')

    @kernel_function(name="export_md", description="Export in markdown format.")
    def export_md(self, content: str) -> bytes:
        """Export the content as a Markdown file."""
        if not content:
            raise ValueError("Content cannot be empty.")
        return content.encode('utf-8')

    @kernel_function(name="export_docx", description="Export in DOCX format.")
    async def export_docx(self, content: str) -> bytes:
        """Export the content as a Microsoft Word file."""
        doc = Document()
        doc.add_paragraph(content)
        doc_stream = io.BytesIO()
        doc.save(doc_stream)
        doc_stream.seek(0)
        return doc_stream.read()

    async def get_revise_prompt(self, resume: str, jd: str | None = None) -> str:
        """Get the prompt for revising the resume based on user profile."""
        if not resume:
            raise ValueError("Resume is required to generate the revise prompt.")
        args = KernelArguments(
            resume=resume,
            jd=jd
        )
        prompt = await load_prompt("writer_agent", args)
        if not prompt:
            raise ValueError("Failed to load the revise resume prompt.")
        return prompt

def get_tool_output(thread):
    """Extract the last tool output from the chat history."""
    tool_outputs = [msg for msg in thread._chat_history if msg.role == AuthorRole.TOOL]
    if tool_outputs:
        func_result = tool_outputs[-1].items[0]
        if func_result.content_type == "message":
            # Text type
            return func_result.result
        elif func_result.content_type == "function_result":
            # File type
            func_name = func_result.function_name
            if func_name.startswith("export_"):
                # Handle export functions
                if func_result.result and isinstance(func_result.result, bytes):
                    return {
                        "content": func_result.result,
                        "ext": func_name.split("_")[-1],
                    }
            return func_result.result
    return None
