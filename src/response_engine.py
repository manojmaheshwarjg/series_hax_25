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
                                       conversation_context: Dict[str, Any] = None,
                                       message_history: List[Dict[str, str]] = None) -> str:
        """
        Generate a conversational response with context awareness via LLM
        """
        entities = entities or {}
        conversation_context = conversation_context or {}
        message_history = message_history or []
        
        # Construct the prompt with refined personality
        system_prompt = f"""
        You are a smart, well-connected assistant who helps people make valuable professional connections.

        PERSONA:
        - Tone: Tech Gen Z / Modern Professional. Relaxed, competent, sharp.
        - Natural language: Use "ship", "stack", "sync", "vibe" if it fits naturally.
        - NO FORCED SLANG: Do NOT force words like "fam", "lit", or "fire". If it sounds try-hard, don't say it.
        - Efficient: Text-message style. Short and sweet.
        - EMOJIS: Use sparingly and only when natural. Avoid 👍. Prefer: 😊 😄 🎉 ✨ 🚀 💡 when appropriate.

        CONVERSATIONAL INTELLIGENCE:
        - Context-aware: Remember what we just talked about.
        - If they give a vague answer (e.g., "idk", "stuff"), play it cool but ask for a specific detail.
        - Match their energy: If they're professional, be professional. If they're casual, relax.

        QUIRKY FOLLOW-UPS (For Vague Answers):
        - "stuff"/"things": "Give me a hint? Tech? Content? Crypto? 😅"
        - "idk": "No stress 😊 What's one thing you're curious about right now?"
        - Too short: "Say more? 😄"

        CATALYST DATA COLLECTION:
        - Be curious, not interrogating.
        - Explain why you're asking: "Asking so I can find you the *perfect* intro 😊"

        Response Rules:
        - Max 2-3 sentences.
        - One question at a time.
        - NEVER say "How can I assist". You're a friend/peer, not a support bot.
        - Emojis should feel natural, not forced.

        Intent: {intent}
        User name: {user_name or 'there'}
        Entities: {entities}
        Conversation context: {conversation_context}

        Generate a natural, context-aware response that matches the persona.
        If their last answer was vague, playfully ask for more detail.
        """

        # Build messages list with history
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        
        # Add history (last 5 messages)
        if message_history:
            messages.extend(message_history[-5:])

        user_content = f"""
        INTENT: {intent}
        USER NAME: {user_name if user_name else 'Unknown'}
        ENTITIES DETECTED: {entities}
        CONTEXT: {conversation_context}
        """
        
        messages.append({
            "role": "user",
            "content": user_content
        })

        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
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

    def check_vagueness(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Check if an answer is vague using LLM and generate a follow-up if so.
        """
        try:
            prompt = f"""
            Analyze this Q&A pair. Determine if the answer is completely EMPTY of content (e.g., "idk", "stuff", "things").
            
            CONTEXT:
            Question Asked: "{question}"
            User Answer: "{answer}"
            
            CRITERIA FOR VAGUE:
            - TRUE VAGUENESS: "idk", "not sure", "stuff", "whatever", "things".
            - NOT VAGUE: "Software", "Building an app", "NYC", "Growth".
            - NOT VAGUE: Any answer that gives even a hint of a direction.
            
            RULE: When in doubt, it is NOT vague. err on the side of allowing the conversation to flow.
            
            Return a JSON object with:
            - is_vague: boolean
            - reason: string (why it's vague)
            - follow_up: string (a concise, culturally aware follow-up question to get more detail, if vague. If not vague, empty string.)
            
            JSON ONLY. NO MARKDOWN.
            """

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt}
                ],
                model=self.model,
                temperature=0.0, # Low temp for logic
                response_format={"type": "json_object"}
            )
            
            import json
            return json.loads(chat_completion.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error checking vagueness: {e}")
            # Fallback to safe default
            return {"is_vague": False, "reason": "error", "follow_up": ""}

    def generate_match_reasoning(self, candidate_name: str, explanation: str, component_scores: Dict[str, float]) -> str:
        """
        Generate a 'cute', enthusiastic, insider-style reason for the match.
        """
        try:
            prompt = f"""
            Rewrite this technical match explanation into a fun, enthusiastic, insider-style recommendation.
            
            CANDIDATE: {candidate_name}
            TECHNICAL EXPLANATION: "{explanation}"
            SCORES: {component_scores}
            
            PERSONA:
            - You are a well-connected friend introducing them.
            - MINIMAL emojis (only ☺️ or ❤️ if truly needed, prefer none).
            - Be specific about WHY they fit (don't just say "it's a match").
            - Style: "Sarah is exactly who you need because..." or "You and Mike will work great together because..."
            - Keep it short (1-2 sentences max).
            
            REASONING:
            """
            
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7,
                max_tokens=100
            )
            
            return chat_completion.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating match reasoning: {e}")
            return explanation  # Fallback to the technical explanation

    def generate_contextual_catalyst_question(self, profile: Dict[str, Any], missing_field: str) -> str:
        """
        Generate a highly contextual Catalyst question based on what we already know.
        Returns just the question string, but generates via JSON to ensure quality.
        """
        try:
            system_prompt = f"""
            You are an expert conversationalist asking a follow-up question to build a professional profile.
            
            TASK: Generate a concise, natural text-message style question to ask the user to fill in their missing profile field: '{missing_field}'.
            
            GUIDELINES:
            - Use the existing profile info to make it contextual! 
            - Example: If they know React, asking about 'current_goals' -> "What are you building with React these days?"
            - Keep it short (text message style).
            - No "Hello" or "Greetings". Just the question.
            
            OUTPUT FORMAT:
            Return a JSON object with:
            - rationale: string (why you chose this question based on profile)
            - question: string (the actual question to ask)
            
            JSON ONLY. NO MARKDOWN.
            """
            
            user_content = f"""
            USER PROFILE SO FAR:
            {profile}
            
            MISSING FIELD: {missing_field}
            """
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                model=self.model,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            import json
            data = json.loads(chat_completion.choices[0].message.content)
            logger.info(f"[CATALYST-GEN] Rationale: {data.get('rationale')}")
            return data.get('question', '').strip()
            
        except Exception as e:
            logger.error(f"Error generating catalyst question: {e}")
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Check for API Key
    if not os.environ.get("GROQ_API_KEY"):
         print("ERROR: GROQ_API_KEY not set.")
         exit(1)

    engine = ResponseEngine()

    print("Testing Groq Response Engine...\n")
    
    # Test Vagueness
    print("--- Vagueness Test ---")
    print(engine.check_vagueness("What do you do?", "stuff"))
    print(engine.check_vagueness("What do you do?", "Product design"))
    
    # Test Catalyst Generation
    print("\n--- Catalyst Test ---")
    profile = {'skills': ['React', 'Python'], 'name': 'Manoj'}
    print(engine.generate_contextual_catalyst_question(profile, 'current_goals'))


