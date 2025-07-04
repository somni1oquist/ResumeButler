import asyncio
from kernel import get_kernel, get_prompt
from user_profile import UserProfile
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import ChatHistory
import re


class ResumeButlerAgent:
    """Agent for goal-driven resume creation and improvement"""
    
    def __init__(self, user_profile: UserProfile, chat_history: ChatHistory):
        self.user_profile = user_profile
        self.chat_history = chat_history
        self.kernel = None
        self.request_settings = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure kernel is initialized"""
        if not self._initialized:
            try:
                self.kernel, self.request_settings = get_kernel()
                self._initialized = True
            except Exception as e:
                print(f"Failed to initialize kernel: {e}")
                raise e
    
    async def detect_intent(self, user_message: str) -> str:
        """Detect user intent from their message"""
        self._ensure_initialized()
        
        args = KernelArguments(
            user_message=user_message,
            existing_resume=self.user_profile.resume is not None,
            chat_history=str(self.chat_history)[-500:]  # Last 500 chars for context
        )
        
        intent_prompt = await get_prompt("agent_intent", args)
        if intent_prompt:
            response = await self.kernel.invoke_prompt(intent_prompt, settings=self.request_settings)
            intent = str(response).strip().lower()
            # Validate intent
            if intent in ['create', 'rewrite', 'chat', 'export']:
                return intent
        
        # Default fallback logic
        if self.user_profile.resume is None:
            return 'create'
        else:
            return 'chat'
    
    async def collect_missing_information(self, user_message: str = None) -> str:
        """Collect missing information from user for resume generation"""
        self._ensure_initialized()
        
        args = KernelArguments(
            user_profile=self.user_profile,
            target_role=self.user_profile.target_role,
            user_message=user_message,
            last_question=self.user_profile.last_question
        )
        
        collection_prompt = await get_prompt("field_collection", args)
        if collection_prompt:
            response = await self.kernel.invoke_prompt(collection_prompt, settings=self.request_settings)
            question = str(response).strip()
            self.user_profile.last_question = question
            return question
        
        return "I need some information to create your resume. Let's start with your full name."
    
    async def generate_resume(self, target_role: str = None, job_description: str = None) -> str:
        """Generate a complete resume based on user profile"""
        self._ensure_initialized()
        
        args = KernelArguments(
            existing_resume=self.user_profile.resume,
            user_profile=self.user_profile,
            target_role=target_role or self.user_profile.target_role,
            job_description=job_description or self.user_profile.jd
        )
        
        generation_prompt = await get_prompt("resume_generation", args)
        if generation_prompt:
            response = await self.kernel.invoke_prompt(generation_prompt, settings=self.request_settings)
            generated_resume = str(response).strip()
            self.user_profile.generated_resume = generated_resume
            return generated_resume
        
        return "❌ Failed to generate resume. Please try again."
    
    def parse_user_information(self, user_message: str) -> dict:
        """Parse user message to extract structured information"""
        info = {}
        
        # Email detection
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, user_message)
        if emails:
            info['email'] = emails[0]
        
        # Phone detection (basic patterns)
        phone_pattern = r'(\+?1?[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, user_message)
        if phones and len(''.join(phones[0])) >= 10:
            info['phone'] = ''.join(phones[0])
        
        # Name detection (if user says "my name is" or "I'm")
        name_patterns = [
            r'my name is ([A-Za-z\s]+?)(?:\s+and|$)',
            r'I\'m ([A-Za-z\s]+?)(?:\s+and|$)',
            r'I am ([A-Za-z\s]+?)(?:\s+and|$)'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up common trailing words
                name = re.sub(r'\s+(and|with|at).*$', '', name, flags=re.IGNORECASE)
                info['name'] = name
                break
        
        return info
    
    def update_profile_from_message(self, user_message: str):
        """Update user profile with information from their message"""
        parsed_info = self.parse_user_information(user_message)
        
        # Update profile with parsed information
        for key, value in parsed_info.items():
            if hasattr(self.user_profile, key) and value:
                setattr(self.user_profile, key, value)
        
        # Context-based updates based on what was last asked
        if self.user_profile.last_question:
            last_q = self.user_profile.last_question.lower()
            
            # Direct field updates based on question context
            if 'name' in last_q and not parsed_info.get('name'):
                self.user_profile.name = user_message.strip()
            elif 'email' in last_q and not parsed_info.get('email'):
                if '@' in user_message:
                    self.user_profile.email = user_message.strip()
            elif 'phone' in last_q and not parsed_info.get('phone'):
                # Clean phone number
                phone_clean = re.sub(r'[^\d+()-]', '', user_message)
                if len(phone_clean) >= 10:
                    self.user_profile.phone = phone_clean
            elif 'location' in last_q:
                self.user_profile.location = user_message.strip()
            elif 'linkedin' in last_q:
                self.user_profile.linkedin = user_message.strip()
            elif 'summary' in last_q or 'objective' in last_q:
                self.user_profile.summary = user_message.strip()
            elif 'experience' in last_q or 'job' in last_q:
                if self.user_profile.experience:
                    self.user_profile.experience += f"\n\n{user_message.strip()}"
                else:
                    self.user_profile.experience = user_message.strip()
            elif 'education' in last_q or 'degree' in last_q:
                if self.user_profile.education:
                    self.user_profile.education += f"\n\n{user_message.strip()}"
                else:
                    self.user_profile.education = user_message.strip()
            elif 'skills' in last_q:
                if self.user_profile.skills:
                    self.user_profile.skills += f", {user_message.strip()}"
                else:
                    self.user_profile.skills = user_message.strip()
            elif 'certification' in last_q:
                if self.user_profile.certifications:
                    self.user_profile.certifications += f"\n{user_message.strip()}"
                else:
                    self.user_profile.certifications = user_message.strip()
            elif 'project' in last_q:
                if self.user_profile.projects:
                    self.user_profile.projects += f"\n\n{user_message.strip()}"
                else:
                    self.user_profile.projects = user_message.strip()
    
    async def process_message(self, user_message: str) -> str:
        """Main agent processing function"""
        # Update profile with any information from the message
        self.update_profile_from_message(user_message)
        
        # If we're in agent mode, continue with that workflow
        if self.user_profile.agent_mode in ['create', 'rewrite']:
            # Check if we have enough information to generate
            if self.user_profile.is_ready_for_generation():
                # Ask if user wants to generate the resume
                if any(word in user_message.lower() for word in ['yes', 'generate', 'create', 'ready', 'go ahead']):
                    generated_resume = await self.generate_resume()
                    self.user_profile.agent_mode = 'preview'
                    return f"🎉 **Your resume has been generated!**\n\n{generated_resume}\n\n---\n\n💡 **What would you like to do next?**\n- Type 'export' to download your resume\n- Type 'revise' to make changes\n- Ask questions about your resume"
                else:
                    return f"Great! I have enough information to create your resume. Your profile is {self.user_profile.get_completion_percentage():.0f}% complete.\n\nWould you like me to generate your resume now? (Just say 'yes' or 'generate')"
            else:
                # Continue collecting information
                return await self.collect_missing_information(user_message)
        
        elif self.user_profile.agent_mode == 'preview':
            # Handle post-generation actions
            if 'export' in user_message.lower():
                return "📄 **Resume Export Options:**\n\n• **Markdown** - Copy the text above\n• **PDF** - Coming soon!\n• **DOCX** - Coming soon!\n\nFor now, you can copy the resume text above and paste it into your preferred document editor."
            elif 'revise' in user_message.lower() or 'change' in user_message.lower():
                self.user_profile.agent_mode = 'create'  # Back to collection mode
                return "What would you like to revise? I can help you update any section of your resume."
            else:
                # Default to regular chat about the resume
                return await self._chat_about_resume(user_message)
        
        else:
            # Detect intent and set mode
            intent = await self.detect_intent(user_message)
            self.user_profile.agent_mode = intent
            
            if intent == 'create':
                return f"🚀 **Let's create your resume!**\n\nI'll help you build a professional resume from scratch. Your current profile is {self.user_profile.get_completion_percentage():.0f}% complete.\n\n" + await self.collect_missing_information(user_message)
            elif intent == 'rewrite':
                if self.user_profile.resume:
                    return f"🔄 **Let's improve your resume!**\n\nI'll help you rewrite and enhance your existing resume. Your current profile is {self.user_profile.get_completion_percentage():.0f}% complete.\n\n" + await self.collect_missing_information(user_message)
                else:
                    self.user_profile.agent_mode = 'create'
                    return f"I don't see an existing resume to rewrite. Let's create a new one instead!\n\n" + await self.collect_missing_information(user_message)
            elif intent == 'export':
                if self.user_profile.generated_resume:
                    return "📄 **Resume Export Options:**\n\n• **Markdown** - Copy the text above\n• **PDF** - Coming soon!\n• **DOCX** - Coming soon!\n\nFor now, you can copy the resume text above and paste it into your preferred document editor."
                else:
                    return "I don't have a generated resume to export. Would you like me to create one for you first?"
            else:
                # Default chat mode
                return await self._chat_about_resume(user_message)
    
    async def _chat_about_resume(self, user_message: str) -> str:
        """Handle general chat about resume/career topics"""
        # Use existing HR chat functionality
        from chat import chat
        return await chat(user_message)