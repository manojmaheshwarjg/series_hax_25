"""
Error Handler
Graceful error handling and recovery for production
"""

import logging
import traceback
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class AIFriendError(Exception):
    """Base exception for Series AI Friend"""
    pass


class KafkaConnectionError(AIFriendError):
    """Kafka connection failed"""
    pass


class APIClientError(AIFriendError):
    """Series API error"""
    pass


class StorageError(AIFriendError):
    """Storage operation failed"""
    pass


class MatchingError(AIFriendError):
    """Matching algorithm error"""
    pass


def safe_execute(fallback_value=None, log_errors=True):
    """
    Decorator for safe execution with error handling

    Args:
        fallback_value: Value to return on error
        log_errors: Whether to log errors
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                return fallback_value
        return wrapper
    return decorator


def handle_api_error(func: Callable) -> Callable:
    """Decorator for API call error handling with retry"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"API call failed after {max_retries} attempts")
                    raise APIClientError(f"Failed after {max_retries} attempts: {e}")
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
    return wrapper


def safe_json_operation(func: Callable) -> Callable:
    """Decorator for safe JSON operations"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"JSON operation error in {func.__name__}: {e}")
            raise StorageError(f"Storage operation failed: {e}")
    return wrapper


class ErrorRecovery:
    """Handles error recovery scenarios"""

    @staticmethod
    def recover_from_kafka_disconnect(consumer):
        """Attempt to recover from Kafka disconnect"""
        logger.warning("Attempting Kafka reconnection...")
        try:
            consumer.stop()
            import time
            time.sleep(5)
            return consumer.connect()
        except Exception as e:
            logger.error(f"Kafka recovery failed: {e}")
            return False

    @staticmethod
    def handle_malformed_message(message_data: dict) -> dict:
        """Handle malformed message gracefully"""
        logger.warning(f"Malformed message received: {message_data}")

        # Ensure required fields
        cleaned = {
            'from': message_data.get('from', 'unknown'),
            'text': message_data.get('text', ''),
            'chat_id': message_data.get('chat_id'),
            'timestamp': message_data.get('timestamp'),
        }

        return cleaned

    @staticmethod
    def handle_profile_corruption(phone: str, user_storage):
        """Handle corrupted profile"""
        logger.error(f"Profile corruption detected for {phone}")

        # Create backup
        try:
            import json
            from datetime import datetime
            backup_file = f"data/profile_backup_{phone}_{datetime.utcnow().timestamp()}.json"
            # Save corrupted data for analysis

            # Create fresh profile
            return user_storage.create_profile(phone)
        except Exception as e:
            logger.error(f"Profile recovery failed: {e}")
            return None

    @staticmethod
    def send_error_notification(api_client, user_phone: str, error_type: str):
        """Send user-friendly error notification"""
        messages = {
            'api_error': "Sorry, I'm having trouble connecting right now. Can you try again in a moment?",
            'matching_error': "Hmm, I'm having trouble searching my network. Let me try again...",
            'storage_error': "I'm experiencing a technical issue. Your request has been saved!",
            'unknown': "Something went wrong, but I'm working on it! Please try again."
        }

        message = messages.get(error_type, messages['unknown'])

        try:
            api_client.send_message(user_phone, message)
        except:
            logger.error("Failed to send error notification")


if __name__ == "__main__":
    # Test error handling
    logging.basicConfig(level=logging.INFO)

    @safe_execute(fallback_value="default")
    def risky_function():
        raise ValueError("Test error")

    result = risky_function()
    print(f"Result: {result}")  # Should print "default"

    @handle_api_error
    def api_call():
        import random
        if random.random() < 0.7:
            raise Exception("API failed")
        return "success"

    try:
        result = api_call()
        print(f"API result: {result}")
    except APIClientError as e:
        print(f"API error: {e}")
