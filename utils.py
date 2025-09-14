#!/usr/bin/env python3
"""
TTK Bot 2.0 - Utility Functions
Geographic processing, error handling, and system utilities
"""

import asyncio
import functools
import logging
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import pytz
import json
import hashlib
import secrets
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Time utilities
def get_current_time() -> datetime:
    """Get current time in EST timezone."""
    est = pytz.timezone('US/Eastern')
    return datetime.now(est)

# Admin utilities  
def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    # Import here to avoid circular imports
    from config import Config
    config = Config()
    return user_id in config.telegram.admin_user_ids

# ID generation utilities
def generate_product_id() -> str:
    """Generate unique product ID."""
    timestamp = int(get_current_time().timestamp())
    random_suffix = secrets.token_hex(4)
    return f"prod_{timestamp}_{random_suffix}"

def generate_combo_id() -> str:
    """Generate unique combo ID."""
    timestamp = int(get_current_time().timestamp())
    random_suffix = secrets.token_hex(4)
    return f"combo_{timestamp}_{random_suffix}"

def generate_order_id() -> str:
    """Generate unique order ID."""
    timestamp = int(get_current_time().timestamp())
    random_suffix = secrets.token_hex(4)
    return f"order_{timestamp}_{random_suffix}"

# Notification utilities
def parse_mute_duration(duration_str: str) -> timedelta:
    """Parse mute duration string to timedelta."""
    if duration_str.endswith('d'):
        days = int(duration_str[:-1])
        return timedelta(days=days)
    elif duration_str.endswith('h'):
        hours = int(duration_str[:-1])
        return timedelta(hours=hours)
    else:
        # Default to days
        return timedelta(days=int(duration_str))

def clean_expired_mutes(notification_settings: dict) -> dict:
    """Remove expired mute settings."""
    current_time = get_current_time()
    cleaned_settings = {}
    
    for user_id, settings in notification_settings.items():
        if 'muted_until' in settings:
            mute_until = datetime.fromisoformat(settings['muted_until'])
            if current_time < mute_until:
                cleaned_settings[user_id] = settings
        else:
            cleaned_settings[user_id] = settings
    
    return cleaned_settings

# Price and calculation utilities
def format_price(price: float) -> str:
    """Format price for display."""
    return f"${price:.0f}"

def round_to_nearest_5(price: float) -> int:
    """Round price to nearest multiple of 5."""
    return int(round(price / 5) * 5)

def calculate_combo_price(products: list) -> int:
    """Calculate combo price based on products."""
    if not products:
        return 0
    
    total_price = sum(product.get('price', 0) for product in products)
    average_price = total_price / len(products)
    
    # Apply small discount for combo
    discounted_price = average_price * 0.95
    
    return round_to_nearest_5(discounted_price)

def calculate_fire_sale_price(original_price: float, discount_percent: int = 20) -> int:
    """Calculate fire sale price with discount."""
    discounted = original_price * (1 - discount_percent / 100)
    return round_to_nearest_5(discounted)

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def get_size_display_name(size: str) -> str:
    """Get display name for product size."""
    size_map = {
        'eighth': '⅛ oz',
        'quarter': '¼ oz', 
        'half': '½ oz',
        'oz': '1 oz',
        'gram': '1g',
        'unit': 'unit',
        'single': '1 roll',
        'pack_5': '5-pack'
    }
    return size_map.get(size, size)

def calculate_delivery_estimate(distance_miles: float) -> str:
    """Calculate delivery time estimate."""
    if distance_miles <= 5:
        return "20-30 minutes"
    elif distance_miles <= 10:
        return "30-45 minutes"
    elif distance_miles <= 15:
        return "45-60 minutes"
    else:
        return "60+ minutes"

def calculate_estimated_delivery_time(distance_miles: float) -> str:
    """Alias for calculate_delivery_estimate."""
    return calculate_delivery_estimate(distance_miles)

def validate_combo_selection(products: list, combo_type: str) -> tuple:
    """Validate combo product selection."""
    if combo_type == 'mixed_quarter':
        if len(products) != 2:
            return False, "Mixed Quarter requires exactly 2 products"
        for product in products:
            if product.get('grade') == '⭐⭐⭐':
                return False, "Mixed Quarter cannot include 3⭐ products"
    elif combo_type == 'mixed_half':
        if len(products) != 2:
            return False, "Mixed Half requires exactly 2 products"
    elif combo_type == 'mixed_oz':
        if len(products) != 2:
            return False, "Mixed Oz requires exactly 2 products"
    
    return True, "Valid combo selection"

# Geographic utilities
@dataclass
class Coordinate:
    """Geographic coordinate with utility methods"""
    latitude: float
    longitude: float
    
    def distance_to(self, other: 'Coordinate') -> float:
        """Calculate distance to another coordinate in meters using Haversine formula"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        delta_lat = math.radians(other.latitude - self.latitude)
        delta_lon = math.radians(other.longitude - self.longitude)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def is_within_radius(self, center: 'Coordinate', radius_meters: float) -> bool:
        """Check if this coordinate is within a radius of another coordinate"""
        return self.distance_to(center) <= radius_meters
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {"latitude": self.latitude, "longitude": self.longitude}

def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate GPS coordinates"""
    try:
        lat = float(latitude)
        lon = float(longitude)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (ValueError, TypeError):
        return False

def calculate_delivery_eta(distance_meters: float, traffic_factor: float = 1.0) -> int:
    """Calculate estimated delivery time in minutes"""
    # Base speed: 30 km/h in urban areas
    base_speed_ms = 8.33  # meters per second
    
    # Adjust for traffic
    adjusted_speed = base_speed_ms / traffic_factor
    
    # Calculate time in seconds, add buffer time
    travel_time_seconds = distance_meters / adjusted_speed
    buffer_time_seconds = 300  # 5 minutes buffer
    
    total_time_minutes = (travel_time_seconds + buffer_time_seconds) / 60
    
    return max(15, int(total_time_minutes))  # Minimum 15 minutes

# Error handling utilities
def retry_on_failure(max_attempts: int = 3, delay_seconds: float = 1.0, 
                    backoff_factor: float = 2.0, exceptions: Tuple = (Exception,)):
    """Decorator for retrying functions on failure with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay_seconds
            
            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}")
                    
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else func
    return decorator

def safe_execute(func: Callable, *args, default_return=None, log_errors=True, **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Error executing {func.__name__}: {e}")
        return default_return

# Data validation utilities
def validate_user_id(user_id: Union[str, int]) -> bool:
    """Validate Telegram user ID"""
    try:
        uid = int(user_id)
        return uid > 0
    except (ValueError, TypeError):
        return False

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input for safety"""
    if not isinstance(text, str):
        return ""
    
    sanitized = text.strip()
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

# Timezone utilities
def get_eastern_time() -> datetime:
    """Get current Eastern Time"""
    eastern = pytz.timezone('America/New_York')
    return datetime.now(eastern)

def convert_to_eastern(dt: datetime) -> datetime:
    """Convert datetime to Eastern Time"""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    eastern = pytz.timezone('America/New_York')
    return dt.astimezone(eastern)

# Security utilities
def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)

# JSON utilities
def safe_json_loads(json_string: str, default=None):
    """Safely load JSON with error handling"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Error parsing JSON: {e}")
        return default

def safe_json_dumps(obj, default=None, **kwargs) -> str:
    """Safely dump object to JSON with error handling"""
    try:
        return json.dumps(obj, **kwargs)
    except (TypeError, ValueError) as e:
        logger.warning(f"Error serializing to JSON: {e}")
        return json.dumps(default) if default is not None else "{}"

# Data manager utility functions
def get_current_time() -> datetime:
    """Get current time in Eastern timezone"""
    return get_eastern_time()

def parse_mute_duration(days: int) -> datetime:
    """Parse mute duration into expiry datetime"""
    return get_current_time() + timedelta(days=days)

def clean_expired_mutes(muted_categories: Dict[str, Dict]) -> Dict[str, Dict]:
    """Clean expired mute entries"""
    current_time = get_current_time()
    cleaned = {}
    
    for category, mute_data in muted_categories.items():
        try:
            expires_at = datetime.fromisoformat(mute_data['expires_at'])
            if current_time < expires_at:
                cleaned[category] = mute_data
        except (ValueError, KeyError):
            # Invalid mute data, skip
            continue
    
    return cleaned

def generate_combo_id() -> str:
    """Generate unique combo deal ID"""
    import time
    timestamp = str(int(time.time()))
    random_part = generate_secure_token(8)
    return f"combo_{timestamp}_{random_part}"

def is_muted(mute_data: Dict) -> bool:
    """Check if a mute is still active"""
    try:
        expires_at = datetime.fromisoformat(mute_data['expires_at'])
        return get_current_time() < expires_at
    except (ValueError, KeyError):
        return False

async def safe_execute_async(func: Callable, *args, default_return=None, log_errors=True, **kwargs):
    """Safely execute an async function with error handling"""
    try:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Error executing {func.__name__}: {e}")
        return default_return

# Missing utility functions used by handlers
def generate_product_id() -> str:
    """Generate unique product ID"""
    import time
    timestamp = str(int(time.time()))
    random_part = generate_secure_token(8)
    return f"prod_{timestamp}_{random_part}"

def generate_order_id() -> str:
    """Generate unique order ID"""
    import time
    timestamp = str(int(time.time()))
    random_part = generate_secure_token(8)
    return f"order_{timestamp}_{random_part}"

def format_price(price: float) -> str:
    """Format price for display"""
    return f"${price:.2f}"

def round_to_nearest_5(price: float) -> float:
    """Round price to nearest $5"""
    return round(price / 5) * 5

def calculate_combo_price(individual_prices: list, pricing_method: str = "discount") -> float:
    """Calculate combo pricing with discount"""
    total = sum(individual_prices)
    if pricing_method == "discount":
        return round(total * 0.85)  # 15% discount
    return total

def calculate_estimated_delivery_time(region: str) -> str:
    """Calculate estimated delivery time for region"""
    # Base delivery time estimates by region type
    if "north" in region.lower() or "northeast" in region.lower():
        return "45-60 minutes"
    elif "south" in region.lower():
        return "30-45 minutes"
    elif "jersey" in region.lower():
        return "60-90 minutes"
    elif "county" in region.lower():
        return "90-120 minutes"
    else:
        return "45-75 minutes"

def calculate_fire_sale_price(original_price: float, discount_percent: int = 25) -> float:
    """Calculate discounted price during fire sale"""
    return round(original_price * (1 - discount_percent / 100), 2)

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def get_size_display_name(size: str) -> str:
    """Convert internal size names to display names"""
    size_map = {
        'eighth': '1/8 oz',
        'quarter': '1/4 oz',
        'half': '1/2 oz',
        'oz': '1 oz',
        'gram': '1g',
        'single': '1x',
        'pack_5': '5-pack',
        'unit': '1 unit',
        'combo': 'Combo Deal'
    }
    return size_map.get(size, size.title())

def calculate_delivery_estimate(region: str, distance_km: float = None) -> str:
    """Calculate delivery estimate based on region and distance"""
    base_time = calculate_estimated_delivery_time(region)
    if distance_km:
        # Add 5 minutes per 5km
        extra_time = int(distance_km / 5) * 5
        if extra_time > 0:
            return f"{base_time} (+ {extra_time} min for distance)"
    return base_time