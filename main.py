"""
Trend Scout - Instagram Viral Content Discovery Tool
Studio Pixelens | Web Design & UI/UX Niche

Scientific identification of viral content opportunities using engagement analysis.
Philosophy: Quality over Quantity. Hunt for "Outliers," not just popular posts.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import instaloader
from config import Config
from safety_manager import SafetyManager
from data_processor import PostProcessor


class TrendScout:
    """Main application class for discovering viral Instagram content."""
    
    def __init__(self, test_mode=False, limit=None):
        """
        Initialize Trend Scout application.
        
        Args:
            test_mode: If True, run in test mode with limited posts
            limit: Maximum number of posts to analyze per hashtag
        """
        # Validate configuration
        Config.validate()
        
        self.loader = instaloader.Instaloader(
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern='',
            quiet=True
        )
        
        self.safety = SafetyManager()
        self.processor = PostProcessor()
        self.test_mode = test_mode
        self.limit = limit
        
        self.viral_posts = []
        self.stats = {
            'total_analyzed': 0,
            'passed_age_filter': 0,
            'passed_follower_filter': 0,
            'passed_er_filter': 0,
            'total_viral': 0
        }
    
    def authenticate(self):
        """
        Authenticate with Instagram.
        Uses session persistence to minimize login frequency.
        """
        session_file = Path(Config.SESSION_FILE)
        
        try:
            # Try to load existing session
            if session_file.exists():
                self.safety.log_progress("🔑 Loading existing session...")
                username = Config.INSTAGRAM_USERNAME or input("Instagram Username: ")
                self.loader.load_session_from_file(username, session_file)
                self.safety.log_progress("✅ Session loaded successfully")
                return True
        except Exception as e:
            self.safety.log_progress(f"⚠️  Could not load session: {e}", 'warning')
        
        # Fresh login required
        username, password = Config.get_credentials()
        
        self.safety.log_progress(f"🔐 Logging in as {username}...")
        
        try:
            self.loader.login(username, password)
            
            # Save session for future use
            self.loader.save_session_to_file(session_file)
            self.safety.log_progress("✅ Login successful! Session saved.")
            return True
            
        except Exception as e:
            self.safety.log_progress(f"❌ Login failed: {e}", 'error')
            return False
    
    def is_viral(self, post, profile) -> tuple[bool, float]:
        """
        Core viral algorithm. Determines if a post qualifies as "viral."
        
        Filter Pipeline:
        1. Age: < 45 days
        2. Followers: 1,000 - 500,000
        3. Engagement Rate: > 3%
        
        Args:
            post: Instaloader Post object
            profile: Instaloader Profile object
        
        Returns:
            Tuple of (is_viral: bool, engagement_rate: float)
        """
        self.stats['total_analyzed'] += 1
        
        # Filter 1: Age (< 45 days)
        post_age = (datetime.now() - post.date_local.replace(tzinfo=None)).days
        if post_age > Config.POST_AGE_DAYS:
            return False, 0.0
        
        self.stats['passed_age_filter'] += 1
        
        # Filter 2: Follower count (1k - 500k)
        if profile.followers < Config.MIN_FOLLOWERS or profile.followers > Config.MAX_FOLLOWERS:
            return False, 0.0
        
        self.stats['passed_follower_filter'] += 1
        
        # Filter 3: Engagement Rate (> 3%)
        total_engagement = post.likes + post.comments
        
        # Prevent division by zero
        if profile.followers == 0:
            return False, 0.0
        
        engagement_rate = total_engagement / profile.followers
        
        if engagement_rate < Config.ER_THRESHOLD:
            return False, engagement_rate
        
        self.stats['passed_er_filter'] += 1
        self.stats['total_viral'] += 1
        
        return True, engagement_rate
    
    def analyze_hashtag(self, hashtag: str):
        """
        Analyze top posts from a specific hashtag.
        
        Args:
            hashtag: Hashtag to analyze (without # symbol)
        """
        self.safety.log_progress(f"\n🔍 Scanning #{hashtag}...")
        
        posts_analyzed = 0
        posts_found = 0
        
        try:
            # Get top posts for hashtag
            def get_posts():
                return self.loader.get_hashtag_posts(hashtag)
            
            posts = self.safety.safe_request(get_posts)
            
            if posts is None:
                self.safety.log_progress(f"⚠️  Could not retrieve posts for #{hashtag}", 'warning')
                return
            
            # Analyze each post
            for post in posts:
                # Apply limit if in test mode
                if self.limit and posts_analyzed >= self.limit:
                    self.safety.log_progress(f"🛑 Reached limit of {self.limit} posts for #{hashtag}")
                    break
                
                posts_analyzed += 1
                
                try:
                    # Get profile to check followers
                    def get_profile():
                        return instaloader.Profile.from_username(
                            self.loader.context,
                            post.owner_username
                        )
                    
                    profile = self.safety.safe_request(get_profile)
                    
                    if profile is None:
                        continue
                    
                    # Apply viral algorithm
                    is_viral, engagement_rate = self.is_viral(post, profile)
                    
                    if is_viral:
                        posts_found += 1
                        
                        # Format and store data
                        post_data = self.processor.format_post_data(post, profile, engagement_rate)
                        
                        # Validate before adding
                        if self.processor.validate_post_data(post_data):
                            self.viral_posts.append(post_data)
                            
                            self.safety.log_progress(
                                f"✨ VIRAL POST FOUND! @{profile.username} | "
                                f"ER: {engagement_rate*100:.2f}% | "
                                f"Score: {post_data['analysis']['virality_score']}"
                            )
                        else:
                            self.safety.log_progress(
                                f"⚠️  Invalid post data for {post.shortcode}",
                                'warning'
                            )
                
                except Exception as e:
                    self.safety.log_progress(
                        f"⚠️  Error analyzing post: {e}",
                        'warning'
                    )
                    continue
            
            self.safety.log_progress(
                f"📊 #{hashtag} Summary: {posts_found} viral posts from {posts_analyzed} analyzed"
            )
        
        except Exception as e:
            self.safety.log_progress(
                f"❌ Error scanning hashtag #{hashtag}: {e}",
                'error'
            )
    
    def scan_all_hashtags(self):
        """Scan all configured hashtags for viral content."""
        self.safety.log_progress("🚀 Starting Trend Scout...")
        self.safety.log_progress(f"🎯 Target: {len(Config.TARGET_HASHTAGS)} hashtags")
        self.safety.log_progress(f"📏 Filters: Age<{Config.POST_AGE_DAYS}d, "
                                f"Followers {Config.MIN_FOLLOWERS}-{Config.MAX_FOLLOWERS}, "
                                f"ER>{Config.ER_THRESHOLD*100}%")
        
        if self.test_mode:
            self.safety.log_progress(f"🧪 TEST MODE: Limited to {self.limit} posts per hashtag")
        
        for hashtag in Config.TARGET_HASHTAGS:
            self.analyze_hashtag(hashtag)
    
    def save_results(self):
        """Save viral posts to JSON file."""
        output_path = Path(Config.OUTPUT_FILE)
        
        # Sort by virality score (highest first)
        sorted_posts = sorted(
            self.viral_posts,
            key=lambda x: x['analysis']['virality_score'],
            reverse=True
        )
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_posts, f, indent=2, ensure_ascii=False)
        
        self.safety.log_progress(f"\n💾 Saved {len(sorted_posts)} viral posts to {output_path}")
    
    def print_summary(self):
        """Print execution summary statistics."""
        self.safety.log_progress("\n" + "="*60)
        self.safety.log_progress("📈 EXECUTION SUMMARY")
        self.safety.log_progress("="*60)
        self.safety.log_progress(f"Total posts analyzed: {self.stats['total_analyzed']}")
        self.safety.log_progress(f"  ├─ Passed age filter: {self.stats['passed_age_filter']}")
        self.safety.log_progress(f"  ├─ Passed follower filter: {self.stats['passed_follower_filter']}")
        self.safety.log_progress(f"  └─ Passed ER filter (VIRAL): {self.stats['passed_er_filter']}")
        self.safety.log_progress(f"\n🎯 Total viral posts discovered: {self.stats['total_viral']}")
        
        # Safety stats
        safety_stats = self.safety.get_stats()
        self.safety.log_progress(f"\n🛡️  Safety Statistics:")
        self.safety.log_progress(f"  ├─ Total requests: {safety_stats['total_requests']}")
        self.safety.log_progress(f"  └─ Rate limits encountered: {safety_stats['rate_limits_hit']}")
        self.safety.log_progress("="*60 + "\n")
    
    def run(self):
        """Main execution flow."""
        try:
            # Step 1: Authenticate
            if not self.authenticate():
                self.safety.log_progress("❌ Authentication failed. Exiting.", 'error')
                return False
            
            # Step 2: Scan hashtags
            self.scan_all_hashtags()
            
            # Step 3: Save results
            if self.viral_posts:
                self.save_results()
            else:
                self.safety.log_progress("\n⚠️  No viral posts found matching criteria.", 'warning')
            
            # Step 4: Print summary
            self.print_summary()
            
            return True
            
        except KeyboardInterrupt:
            self.safety.log_progress("\n\n⚠️  Interrupted by user. Saving current results...", 'warning')
            if self.viral_posts:
                self.save_results()
            self.print_summary()
            return False
        
        except Exception as e:
            self.safety.log_progress(f"\n❌ Fatal error: {e}", 'error')
            return False


def main():
    """Entry point with CLI argument support."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Trend Scout - Discover viral Instagram content in the Web Design niche'
    )
    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='Run in test mode with limited posts'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Limit number of posts to analyze per hashtag (default: 10 in test mode)'
    )
    
    args = parser.parse_args()
    
    # Create and run scout
    scout = TrendScout(
        test_mode=args.test_mode,
        limit=args.limit if args.test_mode else None
    )
    
    success = scout.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
