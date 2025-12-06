"""
Response Variation Engine
Generates natural, varied responses using Groq AI
"""

import os
import random
import logging
from typing import Dict, List, Optional, Any
from groq import Groq
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ResponseEngine:
    """Generates human-like, varied responses using Groq"""

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found. Response generation will fail.")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

        # Fallback templates in case of API failure
        self.fallback_templates = {
            'default': "I'm here to help you connect with people. What do you need?",
            'error': "I'm having a bit of trouble connecting to my brain right now. Can you try again?"
        }

    def generate_response(self, intent: str, context: Dict[str, Any] = None) -> str:
        """
        Generate a varied response for an intent using Groq
        """
        return self.generate_conversational_response(intent, conversation_context=context)

    def generate_conversational_response(self, intent: str, user_name: Optional[str] = None,
                                       entities: Dict[str, List[str]] = None,
                                       conversation_context: Dict[str, Any] = None) -> str:
        """
        Generate a conversational response with context awareness via LLM
        """
        entities = entities or {}
        conversation_context = conversation_context or {}
        
        # Construct the prompt
        system_prompt = """
        You are "Series AI", a super-intelligent, friendly, and highly well-connected networking assistant.
        Your goal is to help people find the right professional connections to accelerate their careers and projects.
        
        PERSONALITY:
        - **Professional but Casual**: Think "smart, helpful friend in the tech industry". Use conversational language, but remain polite and respectful.
        - **Enthusiastic & Proactive**: You love connecting people. If you see a potential match, you get excited.
        - **Concise**: This is a chat interface. Keep messages short (1-3 sentences usuallly). Avoid big blocks of text.
        - **Empathetic**: If the user is struggling, acknowledge it before jumping to solutions.
        - **Adaptive**: Match the user's energy. If they are brief, be brief. If they are detailed, be more detailed.
        
        GUIDELINES:
        1. **Robotic Language**: NEVER use phrases like "I understand", "As an AI language model", or "I have processed your request".
        2. **Implicit Needs**: If the user complains about a problem (e.g., "AWS is killing me"), treat it as a request for help from an expert.
        3. **Celebration**: If the user shares a win (e.g., "Just raised seed round!"), celebrate with them using emojis (🎉, 🚀).
        4. **Uncertainty**: If the request is vague (e.g., "I need a dev"), ask clarifying questions (e.g., "What stack? For a confusing project or a startup?").
        5. **Confirming Action**: When you say you are searching, make it sound active (e.g., "Scouring my network now...", "Let me check my rolodex...").
        6. **No Preaching**: Don't give advice unless asked. Focus on *who* can help, not *how* to fix it.

        OUTPUT FORMAT:
        - Just the raw response text. No quotes. No "Response:" prefix.
        """

        # DEFENSE-IN-DEPTH: Warn if context looks like search requirements for non-search intent
        search_related_intents = {
            'explicit_intro_request',
            'implicit_need',
            'question',
            'clarification'
        }

        if intent not in search_related_intents and conversation_context:
            # Check if context contains search-like fields
            search_indicators = ['role', 'technology', 'seniority', 'experience']
            has_search_indicators = any(key in str(conversation_context).lower() for key in search_indicators)

            if has_search_indicators:
                logger.warning(
                    f"[RESPONSE-ENGINE-WARNING] Context contains search indicators "
                    f"({conversation_context}) but intent is '{intent}' (non-search). "
                    f"This may cause the bot to treat search requirements as user attributes!"
                )

        user_content = f"""
        INTENT: {intent}
        USER NAME: {user_name if user_name else 'Unknown'}
        ENTITIES DETECTED: {entities}
        CONTEXT: {conversation_context}
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ],
                model=self.model,
                temperature=0.7, # Higher temperature for variation
                max_tokens=150
            )

            response = chat_completion.choices[0].message.content.strip()
            return response

        except Exception as e:
            logger.error(f"Error generating response with Groq: {e}")
            return self.fallback_templates.get('default')

    def generate_match_description(self, match_profile: Dict[str, Any]) -> str:
        """
        Generate a compelling description of a match using Groq
        """
        try:
            prompt = f"""
            Describe this person briefly and compellingly to someone who might want to meet them.
            Highlight the most impressive parts.
            
            PROFILE: {match_profile}
            """
            
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception:
            return "A great match from my network."

    def adapt_tone(self, response: str, communication_style: str) -> str:
        """
        Adapt response tone using Groq
        """
        # Skip adaptation for neutral or unknown styles to avoid LLM confusion
        if communication_style in ['neutral', 'unknown', None, '']:
            return response

        try:
            prompt = f"""
            Rewrite the following message to match a {communication_style} communication style.
            Keep the meaning exactly the same.

            IMPORTANT: Return ONLY the rewritten message text. Do NOT include any explanation, meta-commentary, or phrases like "Here is the rewritten message".

            MESSAGE: "{response}"

            REWRITTEN MESSAGE:
            """

            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.5
            )
            adapted = chat_completion.choices[0].message.content.strip()

            # If the response contains meta-commentary, just return original
            if "here is" in adapted.lower() or "rewritten" in adapted.lower():
                logger.warning("LLM returned meta-commentary, using original response")
                return response

            return adapted
        except Exception:
            return response

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Check for API Key
    if not os.environ.get("GROQ_API_KEY"):
         print("ERROR: GROQ_API_KEY not set.")
         exit(1)

    engine = ResponseEngine()

    print("Testing Groq Response Engine...\n")
    
    contexts = [
        ('explicit_intro_request', {'role': ['investor'], 'industry': ['AI']}),
        ('implicit_need', {'problem': 'struggling with React performance'}),
        ('feedback_positive', {}),
    ]

    for intent, entities in contexts:
        print(f"Intent: {intent}, Entities: {entities}")
        resp = engine.generate_conversational_response(intent, user_name="Manoj", entities=entities)
        print(f"Response: {resp}\n")

