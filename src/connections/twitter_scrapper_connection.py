import os
import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv, set_key
from src.connections.base_connection import BaseConnection, Action, ActionParameter
from src.twitter_scrapper.scrapper import TwitterScraper
from src.twitter_scrapper.search import SearchMode
from src.helpers import print_h_bar
from langgraph.prebuilt import ToolExecutor

logger = logging.getLogger("connections.twitter_scrapper_connection")

class TwitterScrapperError(Exception):
    """Base exception for Twitter scrapper errors"""
    pass

class TwitterScrapperConfigurationError(TwitterScrapperError):
    """Raised when there are configuration/credential issues"""
    pass

class TwitterScrapperAPIError(TwitterScrapperError):
    """Raised when Twitter API requests fail"""
    pass

class TwitterScrapperConnection(BaseConnection):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.scraper = None
        self.config = self.validate_config(config)
        # Initialize a single event loop for all async operations
        self._loop = None
        self.test_connection()

    @property
    def is_llm_provider(self) -> bool:
        return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Twitter scrapper configuration from JSON"""
        # Set default values if not provided
        if "timeline_read_count" not in config:
            config["timeline_read_count"] = 20
        if "tweet_interval" not in config:
            config["tweet_interval"] = 5

        # Validate values
        if not isinstance(config["timeline_read_count"], int) or config["timeline_read_count"] <= 0:
            raise ValueError("timeline_read_count must be a positive integer")
        if not isinstance(config["tweet_interval"], int) or config["tweet_interval"] <= 0:
            raise ValueError("tweet_interval must be a positive integer")

        return config

    def _get_credentials(self) -> Dict[str, str]:
        """Get Twitter scrapper credentials from environment"""
        logger.debug("Retrieving Twitter scrapper credentials")
        load_dotenv()

        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        username = os.getenv('TWITTER_USERNAME')
        password = os.getenv('TWITTER_PASSWORD')
        email = os.getenv('TWITTER_EMAIL')

        if not bearer_token:
            raise TwitterScrapperConfigurationError("Missing TWITTER_BEARER_TOKEN in environment")
        if not username:
            raise TwitterScrapperConfigurationError("Missing TWITTER_USERNAME in environment")
        if not password:
            raise TwitterScrapperConfigurationError("Missing TWITTER_PASSWORD in environment")
        if not email:
            raise TwitterScrapperConfigurationError("Missing TWITTER_EMAIL in environment")

        return {
            "bearer_token": bearer_token,
            "username": username,
            "password": password,
            "email": email
        }

    def test_connection(self) -> bool:
        """Test the Twitter scrapper connection"""
        try:
            if not self.scraper:
                credentials = self._get_credentials()
                self.scraper = TwitterScraper(credentials["bearer_token"])
                
                async def _login():
                    await self.scraper.login(
                        credentials["username"],
                        credentials["password"],
                        credentials["email"]
                    )
                    self.register_actions()
                
                # Get the shared event loop
                loop = self._get_event_loop()
                
                # Run the login in the shared loop
                loop.run_until_complete(_login())
                print("Login successful in test connection")
                    
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def configure(self) -> None:
        """Sets up Twitter scrapper authentication"""
        logger.info("Starting Twitter scrapper authentication setup")

        # Check existing configuration
        if self.test_connection():
            logger.info("Twitter scrapper is already configured")
            response = input("Do you want to reconfigure? (y/n): ")
            if response.lower() != 'y':
                return

        setup_instructions = [
            "\n🐦 TWITTER SCRAPPER AUTHENTICATION SETUP",
            "\n📝 Required environment variables:",
            "1. TWITTER_BEARER_TOKEN - Your Twitter API Bearer Token",
            "2. TWITTER_USERNAME - Your Twitter username",
            "3. TWITTER_PASSWORD - Your Twitter password",
            "4. TWITTER_EMAIL - Your Twitter email address"
        ]
        logger.info("\n".join(setup_instructions))
        print_h_bar()

        try:
            credentials = self._get_credentials()
            self.scraper = TwitterScraper(credentials["bearer_token"])

            # Attempt login with credentials
            self.scraper.login(
                credentials["username"],
                credentials["password"],
                credentials["email"]
            )

            logger.info("\n✅ Twitter scrapper authentication successfully set up!")
            return True

        except Exception as e:
            error_msg = f"Setup failed: {str(e)}"
            logger.error(error_msg)
            raise TwitterScrapperConfigurationError(error_msg)

    def initialize(self) -> None:
        """Initialize the connection"""
        if not self.test_connection():
            raise TwitterScrapperConfigurationError("Twitter scrapper is not configured")
            
        try:
            credentials = self._get_credentials()
            self.scraper = TwitterScraper(credentials["bearer_token"])
            
            # Attempt login
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.scraper.login(
                    credentials["username"],
                    credentials["password"],
                    credentials["email"]
                )
            )
            
        except Exception as e:
            error_msg = f"Failed to initialize connection: {str(e)}"
            logger.error(error_msg)
            raise TwitterScrapperConfigurationError(error_msg)

    def perform_action(self, action_name: str, kwargs) -> Any:
        """Execute a Twitter scrapper action with validation"""

        logger.debug(f"Performing action: {action_name}")
        # if action_name not in self.actions:
        #     raise KeyError(f"Unknown action: {action_name}")

        # Ensure connection
        if not self.scraper:
            self.test_connection()
            
        # Add config parameters if not provided
        if "count" in kwargs and kwargs["count"] is None:
            kwargs["count"] = self.config["timeline_read_count"]

        method_name = action_name
        method_name = method_name.replace("_", "-")
        method = getattr(self, method_name)
        
        return method(**kwargs)

        # Use the tool executor pattern
        # connection_name = self.__class__.__name__.lower().replace('connection', '')
        # tool_name = f"{connection_name}_{action_name}"
        
        # try:
        #     result = self.tool_executor.invoke({"name": tool_name, "arguments": kwargs})
        #     return result
        # except Exception as e:
        #     logger.error(f"Error executing action {action_name}: {e}")
        #     raise TwitterScrapperAPIError(f"Failed to execute {action_name}: {str(e)}")

    def get_user_tweets(self, username: str, count: int = None) -> List[Dict]:
        """Get tweets from a specific user"""
        logger.debug(f"Getting tweets for user {username}, count: {count or self.config['timeline_read_count']}")
        try:
            tweets = self.scraper.get_user_tweets(username, count or self.config["timeline_read_count"])
            logger.debug(f"Retrieved {len(tweets)} tweets")
            return tweets
        except Exception as e:
            logger.error(f"Failed to get user tweets: {str(e)}")
            raise TwitterScrapperAPIError(f"Failed to get tweets for user {username}: {str(e)}")

    def get_user_profile(self, username: str) -> Dict:
        """Get user profile information"""
        logger.debug(f"Getting profile for user {username}")
        try:
            profile = self.scraper.get_profile(username)
            logger.debug(f"Retrieved profile for {username}")
            return profile
        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            raise TwitterScrapperAPIError(f"Failed to get profile for user {username}: {str(e)}")

    def search_tweets(self, query: str, count: int = None) -> List[Dict]:
        """Search for tweets matching a query"""
        print(f"Searching tweets with query: {query}, count: {count or self.config['timeline_read_count']}")
        try:
            # Define the search function
            async def _search_tweets():

                if not self.scraper:
                    self.test_connection()
                return await self.scraper.search_tweets(
                    query,
                    search_mode=SearchMode.TOP,
                    max_tweets=count or self.config["timeline_read_count"]
                )
            
            # Get the shared event loop
            loop = self._get_event_loop()
            
            # Run the search in the shared loop
            tweets = loop.run_until_complete(_search_tweets())
            logger.debug(f"Retrieved {len(tweets)} tweets")
            return tweets
                
        except Exception as e:
            logger.error(f"Failed to search tweets: {str(e)}")
            raise TwitterScrapperAPIError(f"Failed to search tweets: {str(e)}")

    def get_tweet_replies(self, tweet_id: str, count: int = None) -> List[Dict]:
        """Get replies to a specific tweet"""
        logger.debug(f"Getting replies for tweet {tweet_id}, count: {count or self.config['timeline_read_count']}")
        try:
            replies = self.scraper.get_tweet_replies(tweet_id, count or self.config["timeline_read_count"])
            logger.debug(f"Retrieved {len(replies)} replies")
            return replies
        except Exception as e:
            logger.error(f"Failed to get tweet replies: {str(e)}")
            raise TwitterScrapperAPIError(f"Failed to get replies for tweet {tweet_id}: {str(e)}")

    def send_tweet(self, tweet: str, replyToTweetId: str = None, mediaData: List[Dict[str, Any]] = None, hideLinkPreview: bool = False) -> None:
        """Send a tweet"""
        logger.debug(f"Sending tweet: {tweet}")
        try:
            # Define the send tweet function
            async def _send_tweet():
                await self.scraper.send_tweet(tweet, replyToTweetId, mediaData, hideLinkPreview)
            
            # Get the shared event loop
            loop = self._get_event_loop()
            
            # Run the send tweet operation in the shared loop
            loop.run_until_complete(_send_tweet())
                
        except Exception as e:
            logger.error(f"Failed to send tweet: {str(e)}")
            raise TwitterScrapperAPIError(f"Failed to send tweet: {str(e)}")

    def _get_event_loop(self):
        """Get or create an event loop for async operations"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    def disconnect(self) -> None:
        """Cleanup resources"""
        logger.debug("Disconnecting Twitter scrapper")
        if self.scraper and self.scraper.auth:
            try:
                self.scraper.auth.close()
            except Exception as e:
                logger.error(f"Error closing auth: {str(e)}")
                
        # Close the event loop if it exists
        if self._loop and not self._loop.is_closed():
            try:
                # Cancel all running tasks
                for task in asyncio.all_tasks(self._loop):
                    task.cancel()
                
                # Close the loop
                self._loop.close()
            except Exception as e:
                logger.error(f"Error closing event loop: {str(e)}")
        
        self.scraper = None
        self._loop = None

    def is_configured(self, verbose = False) -> bool:
        """Check if Twitter scrapper credentials are configured and valid"""
        logger.debug("Checking Twitter scrapper configuration status")
        try:
            # Check if credentials exist
            self._get_credentials()
            return True
        except Exception as e:
            if verbose:
                error_msg = str(e)
                if isinstance(e, TwitterScrapperConfigurationError):
                    error_msg = f"Configuration error: {error_msg}"
                elif isinstance(e, TwitterScrapperAPIError):
                    error_msg = f"API validation error: {error_msg}"
                logger.error(f"Configuration validation failed: {error_msg}")
            return False

    def register_actions(self) -> None:
        """Register available Twitter scrapper actions"""
        self.actions = {
           
            "search-tweets": Action(
                name="search-tweets",
                parameters=[
                    ActionParameter("query", True, str, "Search query for tweets"),
                    ActionParameter("count", False, int, "Number of tweets to retrieve")
                ],
                description="Search for tweets matching a query"
            ),
            "send-tweet": Action(
                name="send-tweet",
                parameters=[
                    ActionParameter("tweet", True, str, "Tweet to send"),
                    ActionParameter("replyToTweetId", False, str, "ID of the tweet to reply to"),
                    ActionParameter("mediaData", False, List[Dict[str, Any]], "Media data to include in the tweet"),
                    ActionParameter("hideLinkPreview", False, bool, "Hide the link preview in the tweet")
                ],
                description="Post a tweet"
            ),
            
        }
        
        # Create tool executor for registered actions
        try:
            tools = [self._create_tool(action) for action in self.actions.values()]
            self.tool_executor = ToolExecutor(tools)
        except Exception as e:
            logger.error(f"Failed to create tool executor: {e}")
            raise e
