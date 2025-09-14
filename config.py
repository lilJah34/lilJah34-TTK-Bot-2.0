#!/usr/bin/env python3
"""
TTK Bot 2.0 - Configuration Management
System configuration with error handling and reliability features
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from pathlib import Path
import pytz

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str = "localhost"
    port: int = 5432
    name: str = "ttk_bot"
    user: str = "ttk_user"
    password: str = ""
    max_connections: int = 20
    connection_timeout: int = 30
    retry_attempts: int = 3

@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str = "8306498479:AAHOIrEZ64jOYcsP70K07_yb2n_Y9w1VMF0"
    webhook_url: str = ""
    admin_user_ids: List[int] = field(default_factory=lambda: [5791024861])
    webhook_port: int = 8443
    webhook_secret: str = ""
    api_timeout: int = 30
    retry_attempts: int = 3
    rate_limit_per_second: int = 30

@dataclass
class LocationConfig:
    """Location service configuration"""
    service_host: str = "0.0.0.0"
    service_port: int = 5001
    max_drivers: int = 100
    location_timeout_minutes: int = 30
    region_check_interval_seconds: int = 10
    gps_accuracy_threshold_meters: float = 50.0

@dataclass
class SchedulerConfig:
    """Job scheduler configuration"""
    timezone: str = "America/New_York"
    max_job_instances: int = 3
    misfire_grace_time_seconds: int = 30
    auto_save_interval_minutes: int = 5
    health_check_interval_minutes: int = 15

@dataclass
class SecurityConfig:
    """Security and encryption settings"""
    encryption_key: str = ""
    jwt_secret: str = ""
    session_timeout_hours: int = 24
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    require_2fa: bool = False

@dataclass
class ExternalAPIConfig:
    """External API integration settings"""
    google_sheets_credentials_path: str = "credentials/google_sheets.json"
    payment_processor_api_key: str = ""
    sms_service_api_key: str = ""
    email_service_api_key: str = ""
    maps_api_key: str = ""
    api_timeout_seconds: int = 30
    retry_attempts: int = 3

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    file_path: str = "logs/ttk_bot.log"
    max_file_size_mb: int = 100
    backup_count: int = 5
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_console: bool = True

@dataclass
class PerformanceConfig:
    """Performance and monitoring settings"""
    max_memory_usage_mb: int = 512
    max_cpu_usage_percent: float = 80.0
    response_timeout_seconds: int = 30
    cache_size_mb: int = 100
    enable_metrics: bool = True
    metrics_port: int = 9090

class Config:
    """
    Centralized configuration management with error handling and validation
    """
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config_dir = Path("config")
        self.data_dir = Path("data")
        self.logs_dir = Path("logs")
        self.credentials_dir = Path("credentials")
        
        # Configuration instances
        self.database = DatabaseConfig()
        self.telegram = TelegramConfig()
        self.location = LocationConfig()
        self.scheduler = SchedulerConfig()
        self.security = SecurityConfig()
        self.external_apis = ExternalAPIConfig()
        self.logging = LoggingConfig()
        self.performance = PerformanceConfig()
        
        # System state
        self.environment = os.getenv("TTK_ENVIRONMENT", "development")
        self.debug_mode = os.getenv("TTK_DEBUG", "false").lower() == "true"
        
        # Initialize configuration
        self._create_directories()
        self._load_configuration()
        self._validate_configuration()
    
    def _create_directories(self):
        """Create necessary directories"""
        try:
            directories = [
                self.config_dir,
                self.data_dir,
                self.logs_dir,
                self.credentials_dir
            ]
            
            for directory in directories:
                directory.mkdir(exist_ok=True)
                logger.debug(f"Ensured directory exists: {directory}")
                
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise
    
    def _load_configuration(self):
        """Load configuration from file and environment variables"""
        try:
            # Load from configuration file
            config_path = self.config_dir / self.config_file
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                self._apply_config_data(config_data)
                logger.info(f"Loaded configuration from {config_path}")
            else:
                logger.info("No configuration file found, using defaults")
            
            # Override with environment variables
            self._load_from_environment()
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data to dataclass instances"""
        try:
            # Apply database config
            if "database" in config_data:
                db_config = config_data["database"]
                for key, value in db_config.items():
                    if hasattr(self.database, key):
                        setattr(self.database, key, value)
            
            # Apply telegram config
            if "telegram" in config_data:
                tg_config = config_data["telegram"]
                for key, value in tg_config.items():
                    if hasattr(self.telegram, key):
                        setattr(self.telegram, key, value)
            
            # Apply location config
            if "location" in config_data:
                loc_config = config_data["location"]
                for key, value in loc_config.items():
                    if hasattr(self.location, key):
                        setattr(self.location, key, value)
                        
        except Exception as e:
            logger.error(f"Error applying configuration data: {e}")
            raise
    
    def _load_from_environment(self):
        """Load configuration overrides from environment variables"""
        try:
            # Database configuration
            self.database.host = os.getenv("TTK_DB_HOST", self.database.host)
            self.database.port = int(os.getenv("TTK_DB_PORT", str(self.database.port)))
            self.database.name = os.getenv("TTK_DB_NAME", self.database.name)
            self.database.user = os.getenv("TTK_DB_USER", self.database.user)
            self.database.password = os.getenv("TTK_DB_PASSWORD", self.database.password)
            
            # Telegram configuration
            self.telegram.bot_token = os.getenv("TTK_BOT_TOKEN", self.telegram.bot_token)
            self.telegram.webhook_url = os.getenv("TTK_WEBHOOK_URL", self.telegram.webhook_url)
            self.telegram.webhook_secret = os.getenv("TTK_WEBHOOK_SECRET", self.telegram.webhook_secret)
            
            # Location service configuration
            self.location.service_host = os.getenv("TTK_LOCATION_HOST", self.location.service_host)
            self.location.service_port = int(os.getenv("TTK_LOCATION_PORT", str(self.location.service_port)))
            
            # Security configuration
            self.security.encryption_key = os.getenv("TTK_ENCRYPTION_KEY", self.security.encryption_key)
            self.security.jwt_secret = os.getenv("TTK_JWT_SECRET", self.security.jwt_secret)
            
            logger.info("Applied environment variable overrides")
            
        except Exception as e:
            logger.error(f"Error loading environment variables: {e}")
            raise
    
    def _validate_configuration(self):
        """Validate configuration settings"""
        errors = []
        
        try:
            # Validate required fields
            if not self.telegram.bot_token and self.environment == "production":
                errors.append("Telegram bot token is required in production")
            
            if not self.security.encryption_key and self.environment == "production":
                errors.append("Encryption key is required in production")
            
            # Validate ranges
            if self.database.port < 1 or self.database.port > 65535:
                errors.append(f"Invalid database port: {self.database.port}")
            
            if self.location.service_port < 1 or self.location.service_port > 65535:
                errors.append(f"Invalid location service port: {self.location.service_port}")
            
            # Validate timezone
            try:
                pytz.timezone(self.scheduler.timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                errors.append(f"Invalid timezone: {self.scheduler.timezone}")
            
            if errors:
                error_message = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
                logger.error(error_message)
                raise ValueError(error_message)
            
            logger.info("Configuration validation passed")
            
        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
            raise
    
    def get_timezone(self):
        """Get configured timezone object"""
        return pytz.timezone(self.scheduler.timezone)
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"

# Global configuration instance
config = Config()

# Utility functions for easy access
def get_config() -> Config:
    """Get the global configuration instance"""
    return config

def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return config.database

def get_telegram_config() -> TelegramConfig:
    """Get Telegram configuration"""
    return config.telegram

def get_location_config() -> LocationConfig:
    """Get location service configuration"""
    return config.location

# Application constants for data manager integration
REGIONS = {
    "309_county": {"name": "🏢 309/County", "active": True},
    "norristown": {"name": "🏘️ Norristown", "active": True},
    "north": {"name": "🏙️ North Philly", "active": True},
    "upper_north": {"name": "🌆 Upper North", "active": True},
    "northeast": {"name": "🏘️ Northeast", "active": True},
    "sw_darby": {"name": "🌉 SW/Darby", "active": True},
    "west_philly": {"name": "🌉 West Philly", "active": True},
    "north_jersey": {"name": "🌊 North Jersey", "active": True},
    "south_jersey": {"name": "🌲 South Jersey", "active": True},
    "south_philly": {"name": "🏙️ South Philly", "active": True}
}

# Sub-areas for region confirmation
REGION_AREAS = {
    "309_county": [
        "Pottstown", "Spring City", "Phoenixville", "Collegeville", "Royersford"
    ],
    "norristown": [
        "Norristown", "East Norriton", "West Norriton", "Plymouth Meeting", "Conshohocken"
    ],
    "north": [
        "Temple", "Broad & Cecil B", "Kensington", "Fishtown", "Northern Liberties"
    ],
    "upper_north": [
        "Germantown", "Mount Airy", "Chestnut Hill", "East Mount Airy", "West Oak Lane"
    ],
    "northeast": [
        "Mayfair", "Bustleton", "Fox Chase", "Holmesburg", "Tacony"
    ],
    "sw_darby": [
        "Southwest Philly", "Darby", "Collingdale", "Yeadon", "Lansdowne"
    ],
    "west_philly": [
        "University City", "Mantua", "Powelton", "Cedar Park", "Cobbs Creek"
    ],
    "north_jersey": [
        "Camden", "Gloucester City", "Collingswood", "Cherry Hill", "Haddon Township"
    ],
    "south_jersey": [
        "Deptford", "Glassboro", "Washington Township", "Turnersville", "Sewell"
    ],
    "south_philly": [
        "Point Breeze", "Grays Ferry", "Newbold", "Girard Estate", "Italian Market"
    ]
}

NOTIFICATION_CATEGORIES = [
    "new_products",
    "fire_sales", 
    "region_updates",
    "order_updates",
    "promotions",
    "general_announcements"
]

PRODUCT_CATEGORIES = [
    "flower",
    "concentrates", 
    "edibles",
    "prerolls",
    "combos",
    "hidden"
]

STAR_RATINGS = ['⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐⭐⭐']

MUTE_TIMER_OPTIONS = [1, 2, 3, 5, 7, 10, 12]

# Default pricing structure by category and rating
DEFAULT_PRICES = {
    'flower': {
        '⭐⭐⭐': {'eighth': 35, 'quarter': 65, 'half': 125, 'oz': 240, '2oz': 450, 'qp': 900},
        '⭐⭐⭐⭐': {'eighth': 40, 'quarter': 75, 'half': 145, 'oz': 280, '2oz': 520, 'qp': 1040},
        '⭐⭐⭐⭐⭐': {'eighth': 45, 'quarter': 85, 'half': 165, 'oz': 320, '2oz': 600, 'qp': 1200}
    },
    'concentrates': {
        '⭐⭐⭐': {'gram': 40},
        '⭐⭐⭐⭐': {'gram': 45},
        '⭐⭐⭐⭐⭐': {'gram': 50}
    },
    'edibles': {
        '⭐⭐⭐': {'unit': 20},
        '⭐⭐⭐⭐': {'unit': 25},
        '⭐⭐⭐⭐⭐': {'unit': 30}
    },
    'prerolls': {
        '⭐⭐⭐': {'single': 12, 'pack_5': 55},
        '⭐⭐⭐⭐': {'single': 15, 'pack_5': 70},
        '⭐⭐⭐⭐⭐': {'single': 18, 'pack_5': 85}
    }
}

MAX_SAVED_ADDRESSES = 2

# Admin configuration
ADMIN_USER_IDS = [5791024861]  # From launch instructions