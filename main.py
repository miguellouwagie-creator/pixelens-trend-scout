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
        
        # Configuración con CAMUFLAJE DE NAVEGADOR (User Agent Spoofing)
        # Configuración con CAMUFLAJE DE NAVEGADOR (User Agent Spoofing)
        self.loader = instaloader.Instaloader(
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern='',
            quiet=True,
            # ESTA ES LA LÍNEA QUE FALTABA: El disfraz de Edge
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        )
        
        self.safety = SafetyManager()
        self.processor = PostProcessor()
        self.test_mode = test_mode
        self.limit = limit
        
        self.viral_posts = []
        self.stats = {
            'total_analyzed': 0,
            'passed_age_filter': 0,
            'passed_engagement_floor': 0,
            'passed_follower_filter': 0,
            'passed_er_filter': 0,
            'total_viral': 0,
            'api_calls_saved': 0,
            'age_limit_breaks': 0
        }
        
        # Calculate minimum engagement needed (optimization)
        self.min_engagement_needed = Config.MIN_FOLLOWERS * Config.ER_THRESHOLD
    
    def authenticate(self):
        """
        Authenticate with Instagram using browser cookies.
        Bypasses soft bans by injecting existing session cookies from browser.
        """
        try:
            # Import browser_cookie3 inside function to avoid dependency issues
            import browser_cookie3
        except ImportError:
            self.safety.log_progress(
                "❌ browser_cookie3 not installed. Run: pip install browser-cookie3",
                'error'
            )
            return False
        
        self.safety.log_progress("🍪 Loading Instagram cookies from browser...")
        
        # Try browsers in order: Chrome → Edge → Firefox
        browsers = [
            ('Chrome', lambda: browser_cookie3.chrome(domain_name='.instagram.com')),
            ('Edge', lambda: browser_cookie3.edge(domain_name='.instagram.com')),
            ('Firefox', lambda: browser_cookie3.firefox(domain_name='.instagram.com'))
        ]
        
        cookies_loaded = False
        
        for browser_name, cookie_loader in browsers:
            try:
                self.safety.log_progress(f"  Trying {browser_name}...")
                cookies = cookie_loader()
                
                # Apply cookies to instaloader session
                self.loader.context._session.cookies = cookies
                cookies_loaded = True
                self.safety.log_progress(f"  ✅ Cookies loaded from {browser_name}")
                break
                
            except PermissionError as e:
                self.safety.log_progress(
                    f"  ⚠️  {browser_name} database locked. Close {browser_name} and try again.",
                    'warning'
                )
                continue
            except Exception as e:
                # Browser not found or no cookies - try next
                self.safety.log_progress(f"  ⏭️  {browser_name} not available", 'debug')
                continue
        
        if not cookies_loaded:
            self.safety.log_progress(
                "❌ Could not load cookies from any browser.\n"
                "   Make sure you're logged into Instagram in Chrome, Edge, or Firefox.\n"
                "   If browser is open, close it to unlock the cookie database.",
                'error'
            )
            return False
        
        # Verify authentication by attempting to get own profile
        self.safety.log_progress("🔍 Verifying authentication...")
        
        try:
            # Try to access Instagram API with loaded cookies
            username = Config.INSTAGRAM_USERNAME or 'instagram'  # Fallback to any username
            test_profile = instaloader.Profile.from_username(
                self.loader.context,
                username
            )
            
            self.safety.log_progress("✅ Authentication verified! Ready to scout trends.")
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if 'login' in error_msg or 'authentication' in error_msg or '401' in error_msg:
                self.safety.log_progress(
                    "❌ Cookie authentication failed. Possible causes:\n"
                    "   1. Instagram session expired - log in again in your browser\n"
                    "   2. Instagram detected automation - wait a few hours\n"
                    "   3. Cookies not properly loaded - ensure you're logged in",
                    'error'
                )
            else:
                self.safety.log_progress(
                    f"❌ Verification failed: {e}\n"
                    "   Try logging into Instagram in your browser and run again.",
                    'error'
                )
            
            return False
    
    def check_age_and_engagement_floor(self, post) -> tuple[bool, int, int]:
        """
        Fast pre-filter (no API calls). Check age and minimum engagement.
        
        This is the first stage of the viral algorithm - filters out posts
        without making expensive Profile API calls.
        
        Args:
            post: Instaloader Post object
        
        Returns:
            Tuple of (should_continue: bool, post_age: int, total_engagement: int)
        """
        # Filter 1: Age (< 45 days)
        post_age = (datetime.now() - post.date_local.replace(tzinfo=None)).days
        if post_age > Config.POST_AGE_DAYS:
            return False, post_age, 0
        
        self.stats['passed_age_filter'] += 1
        
        # Filter 2: Engagement Floor (lazy evaluation)
        # If engagement is less than MIN_FOLLOWERS * ER_THRESHOLD,
        # it's mathematically impossible to meet the ER threshold
        total_engagement = post.likes + post.comments
        
        if total_engagement < self.min_engagement_needed:
            # Skip profile API call - definitely won't be viral
            self.stats['api_calls_saved'] += 1
            return False, post_age, total_engagement
        
        self.stats['passed_engagement_floor'] += 1
        return True, post_age, total_engagement
    
    def check_profile_metrics(self, profile, total_engagement: int) -> tuple[bool, float]:
        """
        Second stage of viral algorithm (requires API call).
        Check follower count and calculate accurate engagement rate.
        
        Args:
            profile: Instaloader Profile object
            total_engagement: Pre-calculated engagement count
        
        Returns:
            Tuple of (is_viral: bool, engagement_rate: float)
        """
        # Filter 3: Follower count (1k - 500k)
        if profile.followers < Config.MIN_FOLLOWERS or profile.followers > Config.MAX_FOLLOWERS:
            return False, 0.0
        
        self.stats['passed_follower_filter'] += 1
        
        # Filter 4: Engagement Rate (> 3%)
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
        Analyze top posts from a specific hashtag with optimized filtering.
        
        Uses two-stage filtering:
        1. Fast pre-filter (age + engagement floor) - no API calls
        2. Slow profile check (followers + ER) - only for qualified posts
        
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
                
                self.stats['total_analyzed'] += 1
                
                try:
                    # STAGE 1: Fast pre-filter (NO API CALL)
                    should_continue, post_age, total_engagement = self.check_age_and_engagement_floor(post)
                    
                    if not should_continue:
                        # Check if we hit the age limit - BREAK completely
                        if post_age > Config.POST_AGE_DAYS:
                            self.stats['age_limit_breaks'] += 1
                            self.safety.log_progress(
                                f"🛑 Reached time limit for #{hashtag} (posts older than {Config.POST_AGE_DAYS} days)"
                            )
                            break  # Stop scanning this hashtag
                        # Otherwise, just skip this post (low engagement)
                        continue
                    
                    posts_analyzed += 1
                    
                    # STAGE 2: Profile check (EXPENSIVE API CALL)
                    # Only executed if post passed stage 1
                    def get_profile():
                        return instaloader.Profile.from_username(
                            self.loader.context,
                            post.owner_username
                        )
                    
                    profile = self.safety.safe_request(get_profile)
                    
                    if profile is None:
                        continue
                    
                    # Apply profile-based viral checks
                    is_viral, engagement_rate = self.check_profile_metrics(profile, total_engagement)
                    
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
        self.safety.log_progress(f"⚡ Lazy Evaluation: Min engagement={int(self.min_engagement_needed)} "
                                f"(saves ~90% of API calls)")
        
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
        self.safety.log_progress(f"Total posts scanned: {self.stats['total_analyzed']}")
        self.safety.log_progress(f"  ├─ Passed age filter: {self.stats['passed_age_filter']}")
        self.safety.log_progress(f"  ├─ Passed engagement floor: {self.stats['passed_engagement_floor']}")
        self.safety.log_progress(f"  ├─ Passed follower filter: {self.stats['passed_follower_filter']}")
        self.safety.log_progress(f"  └─ Passed ER filter (VIRAL): {self.stats['passed_er_filter']}")
        self.safety.log_progress(f"\n🎯 Total viral posts discovered: {self.stats['total_viral']}")
        
        # Optimization stats
        self.safety.log_progress(f"\n⚡ Optimization Statistics:")
        self.safety.log_progress(f"  ├─ API calls saved (lazy eval): {self.stats['api_calls_saved']}")
        self.safety.log_progress(f"  └─ Hashtags stopped early (age limit): {self.stats['age_limit_breaks']}")
        
        # Calculate efficiency percentage
        total_potential_calls = self.stats['total_analyzed']
        if total_potential_calls > 0:
            efficiency = (self.stats['api_calls_saved'] / total_potential_calls) * 100
            self.safety.log_progress(f"  💡 Efficiency gain: {efficiency:.1f}% fewer API calls")
        
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
