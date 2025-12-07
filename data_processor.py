"""
Data Processor module for extracting and structuring Instagram post data.
Transforms raw post data into semantic JSON format optimized for LLM analysis.
"""

from datetime import datetime
from typing import Dict, List, Optional
import re


class PostProcessor:
    """Processes Instagram post data into structured output format."""
    
    @staticmethod
    def extract_hashtags(caption: str) -> List[str]:
        """
        Extract hashtags from caption text.
        
        Args:
            caption: Post caption text
        
        Returns:
            List of hashtags (with # symbol)
        """
        if not caption:
            return []
        
        # Find all hashtags using regex
        hashtags = re.findall(r'#\w+', caption)
        return hashtags
    
    @staticmethod
    def get_media_type(post) -> str:
        """
        Determine media type from post object.
        
        Args:
            post: Instaloader Post object
        
        Returns:
            Media type string: 'Image', 'Video', or 'Carousel'
        """
        if post.typename == 'GraphSidecar':
            return 'Carousel'
        elif post.typename == 'GraphVideo':
            return 'Video'
        elif post.typename == 'GraphImage':
            return 'Image'
        else:
            return 'Unknown'
    
    @staticmethod
    def calculate_virality_score(engagement_rate: float, followers: int, likes: int, comments: int) -> float:
        """
        Calculate virality score based on multiple factors.
        
        Args:
            engagement_rate: Calculated ER (0-1 scale)
            followers: Follower count
            likes: Like count
            comments: Comment count
        
        Returns:
            Virality score (0-10 scale)
        """
        # Base score from engagement rate (0-5 points)
        base_score = engagement_rate * 100  # Convert to 0-100, then scale to 0-5
        base_score = min(base_score / 2, 5.0)
        
        # Bonus for high absolute engagement (0-3 points)
        total_engagement = likes + comments
        if total_engagement > 10000:
            engagement_bonus = 3.0
        elif total_engagement > 5000:
            engagement_bonus = 2.0
        elif total_engagement > 1000:
            engagement_bonus = 1.0
        else:
            engagement_bonus = 0.0
        
        # Bonus for optimal follower range (0-2 points)
        # Sweet spot: 5k-50k (more viral potential)
        if 5000 <= followers <= 50000:
            follower_bonus = 2.0
        elif 1000 <= followers <= 5000 or 50000 <= followers <= 100000:
            follower_bonus = 1.0
        else:
            follower_bonus = 0.0
        
        # Calculate final score (0-10)
        final_score = base_score + engagement_bonus + follower_bonus
        return round(min(final_score, 10.0), 2)
    
    @staticmethod
    def format_post_data(post, profile, engagement_rate: float) -> Dict:
        """
        Format post data into semantic JSON structure.
        
        Args:
            post: Instaloader Post object
            profile: Instaloader Profile object
            engagement_rate: Calculated engagement rate
        
        Returns:
            Dictionary in the specified output format
        """
        caption = post.caption or ""
        hashtags = PostProcessor.extract_hashtags(caption)
        media_type = PostProcessor.get_media_type(post)
        
        # Calculate virality score
        virality_score = PostProcessor.calculate_virality_score(
            engagement_rate,
            profile.followers,
            post.likes,
            post.comments
        )
        
        # Get media URL (prefer high-res, handle None safely)
        if post.typename == 'GraphVideo':
            # video_url might be None if video wasn't downloaded
            media_url = getattr(post, 'video_url', None) or post.url
        else:
            media_url = post.url
        
        # Format post date
        post_date = post.date_local.strftime('%Y-%m-%d')
        
        # Create hook preview (first 50 chars)
        hook_preview = caption[:50] + "..." if len(caption) > 50 else caption
        
        # Structure data according to specification
        return {
            "trend_id": post.shortcode,
            "analysis": {
                "virality_score": virality_score,
                "type": media_type,
                "engagement_rate": round(engagement_rate * 100, 2),  # Convert to percentage
                "posted_date": post_date
            },
            "content": {
                "hook_preview": hook_preview,
                "full_caption": caption,
                "tags": hashtags
            },
            "resource": media_url,
            "post_url": f"https://www.instagram.com/p/{post.shortcode}/",
            "creator": {
                "username": profile.username,
                "followers": profile.followers
            },
            "metrics": {
                "likes": post.likes,
                "comments": post.comments
            }
        }
    
    @staticmethod
    def validate_post_data(post_data: Dict) -> bool:
        """
        Validate that post data has all required fields.
        
        Args:
            post_data: Formatted post data dictionary
        
        Returns:
            True if valid, False otherwise
        """
        required_keys = ['trend_id', 'analysis', 'content', 'resource']
        
        for key in required_keys:
            if key not in post_data:
                return False
        
        # Check nested required fields
        if 'virality_score' not in post_data.get('analysis', {}):
            return False
        
        if 'full_caption' not in post_data.get('content', {}):
            return False
        
        return True
