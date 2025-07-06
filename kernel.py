import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments
from semantic_kernel.prompt_template import PromptTemplateConfig, KernelPromptTemplate, HandlebarsPromptTemplate
from dotenv import load_dotenv
import os

_kernel = None

def get_kernel() -> tuple[sk.Kernel, AzureChatPromptExecutionSettings]:
    load_dotenv()
    global _kernel
    if _kernel is None:
        _kernel = sk.Kernel()

    request_settings = AzureChatPromptExecutionSettings(service_id="az_resume_service")
    return _kernel, request_settings

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

async def load_prompt(template_name: str, arguments: KernelArguments | None = None) -> str | None:
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
        prompt_template = None
        rendered_prompt: str | None = None

        config = PromptTemplateConfig(template=prompt["template"], template_format=prompt["template_format"])
        if prompt["template_format"] == "semantic-kernel":
            prompt_template = KernelPromptTemplate(prompt_template_config=config)
        elif prompt["template_format"] == "handlebars":
            prompt_template = HandlebarsPromptTemplate(prompt_template_config=config)

        if prompt_template is not None:
            rendered_prompt = await prompt_template.render(kernel, arguments)
    return rendered_prompt