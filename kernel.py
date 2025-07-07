import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from dotenv import load_dotenv

_kernel = None

def get_kernel() -> tuple[sk.Kernel, AzureChatPromptExecutionSettings]:
    """
    Get the semantic kernel and its execution settings.
    If the kernel is not initialized, it will be created.

    Returns:
        tuple: A tuple containing the semantic kernel and an empty execution settings.
    """
    load_dotenv()
    global _kernel
    if _kernel is None:
        _kernel = sk.Kernel()
    return _kernel, AzureChatPromptExecutionSettings()
