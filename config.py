"""
Configuration module for Trend Scout application.
Manages all settings, thresholds, and target parameters.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Centralized configuration for the Trend Scout application."""
    
    # Target Hashtags for Studio Pixelens niche
    TARGET_HASHTAGS = [
        'webdesign',
        'uidesign',
        'astrobuild',
        'webdevelopment',
        'creativeagency',
        'designtips',
        'uiux'
    ]
    
    # Instagram Authentication
    INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME', '')
    INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD', '')
    
    # Viral Algorithm Thresholds
    ER_THRESHOLD = float(os.getenv('ER_THRESHOLD', 0.03))  # 3% by default
    MIN_FOLLOWERS = int(os.getenv('MIN_FOLLOWERS', 1000))
    MAX_FOLLOWERS = int(os.getenv('MAX_FOLLOWERS', 500000))
    POST_AGE_DAYS = int(os.getenv('POST_AGE_DAYS', 45))
    
    # Safety Settings
    MIN_DELAY_SECONDS = int(os.getenv('MIN_DELAY_SECONDS', 15))
    MAX_DELAY_SECONDS = int(os.getenv('MAX_DELAY_SECONDS', 45))
    
    # Output Configuration
    OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'viral_trends.json')
    SESSION_FILE = 'session_data'
    
    # Logging
    LOG_FILE = 'trend_scout.log'
    LOG_LEVEL = 'INFO'
    
    @classmethod
    def validate(cls):
        """Validate configuration settings."""
        if cls.ER_THRESHOLD <= 0 or cls.ER_THRESHOLD > 1:
            raise ValueError(f"ER_THRESHOLD must be between 0 and 1, got {cls.ER_THRESHOLD}")
        
        if cls.MIN_FOLLOWERS >= cls.MAX_FOLLOWERS:
            raise ValueError(f"MIN_FOLLOWERS must be less than MAX_FOLLOWERS")
        
        if cls.POST_AGE_DAYS <= 0:
            raise ValueError(f"POST_AGE_DAYS must be positive, got {cls.POST_AGE_DAYS}")
        
        if cls.MIN_DELAY_SECONDS >= cls.MAX_DELAY_SECONDS:
            raise ValueError(f"MIN_DELAY_SECONDS must be less than MAX_DELAY_SECONDS")
        
        return True
    
    @classmethod
    def get_credentials(cls):
        """Get Instagram credentials, prompting if not in environment."""
        username = cls.INSTAGRAM_USERNAME
        password = cls.INSTAGRAM_PASSWORD
        
        if not username:
            username = input("Instagram Username: ")
        
        if not password:
            from getpass import getpass
            password = getpass("Instagram Password: ")
        
        return username, password
