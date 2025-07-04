import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments
from semantic_kernel.prompt_template import PromptTemplateConfig, HandlebarsPromptTemplate
from streamlit.runtime.uploaded_file_manager import UploadedFile
from document_parser import get_parser_manager
from dotenv import load_dotenv
from user_profile import UserProfile
import os

_kernel = None
_parser = get_parser_manager()
def get_kernel() -> tuple[sk.Kernel, AzureChatPromptExecutionSettings]:
    load_dotenv()
    global _kernel
    if _kernel is None:
        _kernel = sk.Kernel()

        # Initialize Azure OpenAI service for resume processing
        az_resume_service = AzureChatCompletion(
            service_id="az_resume_service",
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY")
        )
        _kernel.add_service(az_resume_service)

    request_settings = AzureChatPromptExecutionSettings(service_id="az_resume_service")
    return _kernel, request_settings

def get_basic_args(user_profile: UserProfile, resume_file: UploadedFile | None=None) -> KernelArguments | None:
    """Get KernelArguments from UserProfile"""
    try:
        if resume_file:
            user_profile.resume = _parser.parse_document(resume_file)
    except (FileNotFoundError, IOError):
        print(f"Error loading resume. Please check the file.")
        return None

    arguments = KernelArguments(**user_profile.__dict__)
    return arguments

def get_yaml(template_name: str) -> dict | None:
    """Load YAML template from file"""
    prompt_path = f"prompts/{template_name}.yaml"
    try:
        with open(prompt_path, "r") as file:
            import yaml
            return yaml.safe_load(file)
    except (FileNotFoundError, IOError) as e:
        print(f"Prompt template '{template_name}' not found.")
        return None

async def get_prompt(template_name: str, arguments: KernelArguments | None = None) -> str | None:
    """Get rendered prompt"""
    kernel, _ = get_kernel()

    # Load the prompt template from a YAML file
    prompt = get_yaml(template_name)
    if prompt is None:
        print(f"Prompt template '{template_name}' not found.")
        return None
    elif arguments is None:
        return prompt["template"]
    else:
        config = PromptTemplateConfig(template=prompt["template"], template_format=prompt["template_format"])
        prompt_template = HandlebarsPromptTemplate(prompt_template_config=config)
    
    rendered_prompt = await prompt_template.render(kernel, arguments)
    return rendered_prompt