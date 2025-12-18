"""Input sanitization utilities for security."""

import html
import re
from typing import Optional


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML content by escaping special characters.
    This prevents XSS attacks by converting HTML entities.
    
    Args:
        text: The input text to sanitize
        
    Returns:
        Sanitized text with HTML entities escaped
    """
    return html.escape(text)


def sanitize_for_db(text: str) -> str:
    """
    Sanitize text before storing in database.
    Removes control characters but preserves newlines and tabs.
    
    Args:
        text: The input text to sanitize
        
    Returns:
        Sanitized text safe for database storage
    """
    # Remove control characters except newlines, tabs, and carriage returns
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return sanitized


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: The original filename
        
    Returns:
        Sanitized filename safe for storage
    """
    # Remove path separators and dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    # Limit length
    if len(sanitized) > 255:
        # Preserve extension
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_len = 255 - len(ext) - 1 if ext else 255
        sanitized = f"{name[:max_name_len]}.{ext}" if ext else name[:255]
    return sanitized or 'unnamed'


def sanitize_conversation_title(title: str) -> str:
    """
    Sanitize conversation title.
    
    Args:
        title: The conversation title
        
    Returns:
        Sanitized title
    """
    # Remove HTML and limit length
    sanitized = sanitize_html(title)
    sanitized = sanitize_for_db(sanitized)
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:197] + '...'
    return sanitized.strip() or '新对话'


def sanitize_chat_content(content: str) -> str:
    """
    Sanitize chat message content.
    Preserves markdown formatting but removes potentially dangerous content.
    
    Args:
        content: The chat message content
        
    Returns:
        Sanitized content
    """
    # Remove control characters
    sanitized = sanitize_for_db(content)
    # Don't escape HTML here as we want to preserve markdown
    # The frontend should handle rendering safely with react-markdown
    return sanitized


def sanitize_email(email: str) -> Optional[str]:
    """
    Validate and sanitize email address.
    
    Args:
        email: The email address
        
    Returns:
        Sanitized email or None if invalid
    """
    # Basic email validation
    email = email.strip().lower()
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, email):
        return email
    return None


def sanitize_username(username: str) -> str:
    """
    Sanitize username.
    
    Args:
        username: The username
        
    Returns:
        Sanitized username
    """
    # Remove HTML entities and control characters
    sanitized = sanitize_html(username)
    sanitized = sanitize_for_db(sanitized)
    # Remove leading/trailing whitespace
    sanitized = sanitized.strip()
    # Limit length
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    return sanitized or 'User'