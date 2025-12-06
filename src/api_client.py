"""
Series API Client
Wrapper for Series messaging API with rate limiting and retry logic
"""

import requests
import logging
import time
import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import random
from error_handler import handle_api_error, APIClientError

load_dotenv()

logger = logging.getLogger(__name__)


class SeriesAPIClient:
    """Client for interacting with Series API"""

    def __init__(self):
        self.api_key = os.getenv('API_KEY')
        self.base_url = os.getenv('API_BASE_URL', 'https://api.series.io')
        self.sender_number = os.getenv('SENDER_NUMBER')

        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial retry delay in seconds

    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        now = time.time()
        time_since_last_request = now - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                     params: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                self._rate_limit()

                if method.upper() == 'GET':
                    response = requests.get(url, headers=self.headers, params=params, timeout=10)
                elif method.upper() == 'POST':
                    response = requests.post(url, headers=self.headers, json=data, timeout=10)
                elif method.upper() == 'PUT':
                    response = requests.put(url, headers=self.headers, json=data, timeout=10)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return None

                response.raise_for_status()

                # Return JSON response if available
                try:
                    return response.json()
                except:
                    return {'success': True}

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    # Exponential backoff with jitter
                    delay = self.retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts")
                    return None

        return None

    def get_chats(self) -> Optional[List[Dict]]:
        """Get list of all chats"""
        response = self._make_request('GET', '/api/chats')
        if response:
            return response.get('chats', [])
        return None

    def get_chat_messages(self, chat_id: str, limit: int = 100) -> Optional[List[Dict]]:
        """Get messages from a specific chat"""
        params = {'limit': limit}
        response = self._make_request('GET', f'/api/chats/{chat_id}/messages', params=params)
        if response:
            return response.get('messages', [])
        return None

    @handle_api_error
    def send_message(self, to_number: str, text: str, chat_id: Optional[str] = None) -> Optional[Dict]:
        """Send a text message"""
        data = {
            'from': self.sender_number,
            'to': to_number,
            'text': text
        }

        if chat_id:
            data['chat_id'] = chat_id

        logger.info(f"Sending message to {to_number}: {text[:50]}...")
        response = self._make_request('POST', '/api/chat_messages', data=data)

        if response:
            logger.info(f"Message sent successfully")
        else:
            logger.error(f"Failed to send message")
            raise APIClientError("Failed to send message")

        return response

    def send_typing_indicator(self, to_number: str, duration_ms: int = 3000) -> Optional[Dict]:
        """Send typing indicator"""
        data = {
            'from': self.sender_number,
            'to': to_number,
            'duration_ms': duration_ms
        }

        logger.debug(f"Sending typing indicator to {to_number} for {duration_ms}ms")
        return self._make_request('POST', '/api/typing_indicators', data=data)

    def send_reaction(self, message_id: str, reaction: str) -> Optional[Dict]:
        """Send a reaction to a message"""
        data = {
            'message_id': message_id,
            'reaction': reaction
        }

        logger.info(f"Sending reaction '{reaction}' to message {message_id}")
        return self._make_request('POST', '/api/reactions', data=data)

    def create_group_chat(self, participants: List[str], name: Optional[str] = None) -> Optional[Dict]:
        """Create a group chat"""
        data = {
            'participants': participants
        }

        if name:
            data['name'] = name

        logger.info(f"Creating group chat with {len(participants)} participants")
        return self._make_request('POST', '/api/chats', data=data)

    def get_user_info(self, phone_number: str) -> Optional[Dict]:
        """Get information about a user"""
        return self._make_request('GET', f'/api/users/{phone_number}')


# Utility functions for human-like messaging behavior

def calculate_typing_delay(text: str, complexity: int = 1) -> float:
    """
    Calculate realistic typing delay based on message length and complexity

    Args:
        text: The message text
        complexity: Complexity score (1-5), higher = more thinking time

    Returns:
        Delay in seconds
    """
    words = len(text.split())

    # Typing time (40-80 WPM)
    wpm = random.uniform(40, 80)
    typing_time = (words / wpm) * 60

    # Thinking time based on complexity
    thinking_time = complexity * random.uniform(1.5, 3.5)

    # Pause time for punctuation
    punctuation_count = text.count('.') + text.count('?') + text.count('!')
    pause_time = punctuation_count * random.uniform(0.3, 0.8)

    total_delay = typing_time + thinking_time + pause_time

    # Cap at reasonable maximum
    return min(total_delay, 15.0)


def send_message_with_typing(client: SeriesAPIClient, to_number: str, text: str,
                             complexity: int = 1, chat_id: Optional[str] = None) -> Optional[Dict]:
    """
    Send a message with realistic typing indicator

    Args:
        client: SeriesAPIClient instance
        to_number: Recipient phone number
        text: Message text
        complexity: Message complexity (1-5)
        chat_id: Optional chat ID

    Returns:
        API response
    """
    # Calculate delay
    delay = calculate_typing_delay(text, complexity)
    typing_duration_ms = int(delay * 1000)

    # Send typing indicator
    client.send_typing_indicator(to_number, typing_duration_ms)

    # Wait for the typing duration
    time.sleep(delay)

    # Send the actual message
    return client.send_message(to_number, text, chat_id)


if __name__ == "__main__":
    # Test the API client
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    client = SeriesAPIClient()

    # Test getting chats
    chats = client.get_chats()
    if chats:
        print(f"Found {len(chats)} chats")
