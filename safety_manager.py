"""
Safety Manager module for handling rate limits, delays, and error recovery.
Protects against Instagram IP bans and ensures robust operation.
"""

import time
import random
import logging
from datetime import datetime
from config import Config


class SafetyManager:
    """Manages safety mechanisms to prevent rate limiting and handle errors."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.request_count = 0
        self.last_request_time = None
        self.rate_limit_hit_count = 0
    
    def _setup_logger(self):
        """Setup logging configuration."""
        logging.basicConfig(
            filename=Config.LOG_FILE,
            level=getattr(logging, Config.LOG_LEVEL),
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Also log to console
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
        
        return logging.getLogger(__name__)
    
    def human_delay(self):
        """
        Implement random delay to mimic human behavior.
        Range: 15-45 seconds (configurable via environment).
        """
        delay = random.uniform(Config.MIN_DELAY_SECONDS, Config.MAX_DELAY_SECONDS)
        self.logger.info(f"⏱️  Waiting {delay:.1f} seconds (human emulation)...")
        time.sleep(delay)
        self.request_count += 1
        self.last_request_time = datetime.now()
    
    def handle_rate_limit(self, severity='medium'):
        """
        Handle rate limit scenarios with exponential backoff.
        
        Args:
            severity: 'low', 'medium', or 'high' based on error type
        """
        self.rate_limit_hit_count += 1
        
        wait_times = {
            'low': 60,      # 1 minute
            'medium': 300,  # 5 minutes
            'high': 900     # 15 minutes
        }
        
        wait_seconds = wait_times.get(severity, 300)
        
        # Exponential backoff if we keep hitting limits
        if self.rate_limit_hit_count > 1:
            wait_seconds *= self.rate_limit_hit_count
        
        self.logger.warning(
            f"⚠️  Rate limit detected (severity: {severity}). "
            f"Pausing for {wait_seconds/60:.1f} minutes..."
        )
        
        time.sleep(wait_seconds)
    
    def safe_request(self, func, *args, max_retries=3, **kwargs):
        """
        Wrapper for safe execution of Instagram requests with retry logic.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments for the function
            max_retries: Maximum number of retry attempts
        
        Returns:
            Result of the function or None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                # Add delay before request (except first overall request)
                if self.request_count > 0:
                    self.human_delay()
                
                result = func(*args, **kwargs)
                
                # Reset rate limit counter on success
                if self.rate_limit_hit_count > 0:
                    self.logger.info("✅ Rate limit cleared, resuming normal operation")
                    self.rate_limit_hit_count = 0
                
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Rate limit detection
                if '429' in error_msg or 'rate limit' in error_msg or 'too many requests' in error_msg:
                    self.handle_rate_limit('high')
                    continue
                
                # Connection errors
                elif 'connection' in error_msg or 'timeout' in error_msg:
                    self.logger.warning(f"🌐 Connection error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(5 * (attempt + 1))  # Progressive backoff
                        continue
                
                # Login errors
                elif 'login' in error_msg or 'authentication' in error_msg:
                    self.logger.error(f"🔒 Authentication error: {e}")
                    raise  # Re-raise auth errors immediately
                
                # Other errors
                else:
                    self.logger.error(f"❌ Error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
        
        # All retries exhausted
        self.logger.error(f"💥 Max retries exhausted for function {func.__name__}")
        return None
    
    def log_progress(self, message, level='info'):
        """Log progress messages."""
        log_func = getattr(self.logger, level, self.logger.info)
        log_func(message)
    
    def get_stats(self):
        """Get current safety statistics."""
        return {
            'total_requests': self.request_count,
            'rate_limits_hit': self.rate_limit_hit_count,
            'last_request': self.last_request_time
        }
