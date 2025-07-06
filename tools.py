from kernel import get_kernel, load_prompt
from semantic_kernel.functions import KernelArguments, kernel_function
from user_profile import UserProfile
from constants import ServiceIDs


class RevisionPlugin:
    """Plugin to handle resume revision based on user profile."""

    @kernel_function(name="revise_resume", description="Revise, update or edit the resume based on user profile.")
    async def revise_resume(self, user_profile: UserProfile) -> str:
        prompt = await self.get_revise_prompt(user_profile)
        kernel, request_settings = get_kernel()
        request_settings.service_id = ServiceIDs.AZURE_RESUME_SERVICE
        result = await kernel.invoke_prompt(prompt=prompt, settings=request_settings)
        if result and result.value:
            return str(result.value[-1])
        return "Failed to revise the resume. Please check the input data or try again later."

    async def get_revise_prompt(self, user_profile: UserProfile) -> str:
        """Get the prompt for revising the resume based on user profile."""
        if not user_profile:
            raise ValueError("User profile is required to generate the revise prompt.")
        args = KernelArguments(
            resume=user_profile.resume,
            jd=user_profile.jd
        )
        prompt = await load_prompt("revise_resume", args)
        if not prompt:
            raise ValueError("Failed to load the revise resume prompt.")
        return prompt

    
