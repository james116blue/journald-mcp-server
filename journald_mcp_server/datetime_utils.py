#!/usr/bin/env python3
"""
Datetime utilities for journald MCP server.

Provides functions for parsing datetime inputs from LLM tools and formatting
journal entry timestamps into human-readable output.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Union
import dateparser

logger = logging.getLogger(__name__)


def parse_datetime_input(input_str: str) -> datetime:
    """
    Parse datetime input string into UTC datetime object.
    
    Supports natural language datetime strings like:
    - "2 hours ago"
    - "yesterday at 3pm"
    - "2024-01-15 14:30"
    - "now"
    - "today"
    
    Args:
        input_str: Datetime string to parse
        
    Returns:
        datetime: UTC datetime object
        
    Raises:
        ValueError: If the input cannot be parsed as a valid datetime
    """
    if not input_str or not input_str.strip():
        raise ValueError("Empty datetime input string")
    
    # Configure dateparser to return timezone-aware datetime in UTC
    settings = {
        'TIMEZONE': 'UTC',
        'RETURN_AS_TIMEZONE_AWARE': True,
        'TO_TIMEZONE': 'UTC',
    }
    
    parsed = dateparser.parse(input_str, settings=settings)
    
    if parsed is None:
        raise ValueError(f"Could not parse datetime from input: '{input_str}'")
    
    # Ensure the datetime is timezone-aware and in UTC
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    
    return parsed


def format_journal_timestamp(timestamp_val: Union[int, float, datetime, str]) -> str:
    """
    Format journal entry timestamp into human-readable string.
    
    Handles different timestamp formats from journal entries:
    - Microseconds since epoch (int/float)
    - datetime objects
    - ISO format strings
    
    Args:
        timestamp_val: Timestamp value from journal entry
        
    Returns:
        str: Human-readable datetime string in ISO format
        
    Raises:
        ValueError: If timestamp cannot be formatted
    """
    if timestamp_val is None:
        raise ValueError("Timestamp value is None")
    
    dt = None
    
    if isinstance(timestamp_val, (int, float)):
        # Convert microseconds to seconds and create datetime
        # Journal timestamps are typically in microseconds since epoch
        timestamp_s = timestamp_val / 1_000_000
        dt = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
    
    elif isinstance(timestamp_val, datetime):
        dt = timestamp_val
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
    
    elif isinstance(timestamp_val, str):
        try:
            dt = datetime.fromisoformat(timestamp_val)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
        except (ValueError, AttributeError):
            raise ValueError(f"Unsupported timestamp string format: {timestamp_val}")
    
    else:
        raise ValueError(f"Unsupported timestamp type: {type(timestamp_val)}")
    
    # Return ISO format for consistency
    return dt.isoformat()


def format_journal_timestamp_human(timestamp_val: Union[int, float, datetime, str]) -> str:
    """
    Format journal entry timestamp into more human-readable string.
    
    Example: "2024-01-15 14:30:45 UTC"
    
    Args:
        timestamp_val: Timestamp value from journal entry
        
    Returns:
        str: Human-readable datetime string
    """
    iso_str = format_journal_timestamp(timestamp_val)
    dt = datetime.fromisoformat(iso_str)
    
    # Format as "YYYY-MM-DD HH:MM:SS UTC"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
