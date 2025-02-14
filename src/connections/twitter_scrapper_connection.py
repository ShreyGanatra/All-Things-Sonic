import os
import json
import requests
from typing import Dict, Any, List
from urllib.parse import urlencode
from .base_connection import BaseConnection, Action, ActionParameter

class TwitterScrapperConnection(BaseConnection):
    def __init__(self, config):
        self.client = None
        super().__init__(config)

    @property
    def is_llm_provider(self):
        return False

    def validate_config(self, config) -> Dict[str, Any]:
        """Validate the configuration for Twitter connection."""
        required_fields = ["cookies_file"]
        optional_fields = ["username", "password"]
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required configuration field: {field}")
        
        return {
            "cookies_file": config.get("cookies_file"),
            "username": config.get("username"),
            "password": config.get("password")
        }

    def configure(self, **kwargs) -> bool:
        """Configure the Twitter client with credentials."""
        try:
            self.client = TwitterClient(
                username=self.config.get("username"),
                password=self.config.get("password"),
                cookies_file=self.config.get("cookies_file")
            )
            return True
        except Exception as e:
            print(f"Failed to configure Twitter client: {str(e)}")
            return False

    def is_configured(self, verbose=False) -> bool:
        """Check if the Twitter client is configured and logged in."""
        if verbose:
            print(f"Twitter client status: {'Configured' if self.client else 'Not configured'}")
        return self.client is not None and self.client.is_logged_in

    def register_actions(self) -> None:
        """Register available Twitter actions."""
        self.actions = {
            "search-tweets": Action(
                name="search-tweets",
                parameters=[
                    ActionParameter(
                        name="query",
                        required=True,
                        type=str,
                        description="Search query for finding tweets"
                    ),
                    ActionParameter(
                        name="count",
                        required=False,
                        type=int,
                        description="Number of tweets to return (default: 20)"
                    )
                ],
                description="Search for tweets using a given query"
            ),
            "post-tweet": Action(
                name="post-tweet",
                parameters=[
                    ActionParameter(
                        name="text",
                        required=True,
                        type=str,
                        description="Text content of the tweet"
                    ),
                    ActionParameter(
                        name="media_paths",
                        required=False,
                        type=list,
                        description="List of paths to media files to attach"
                    )
                ],
                description="Post a new tweet with optional media attachments"
            ),
            "like-tweet": Action(
                name="like-tweet",
                parameters=[
                    ActionParameter(
                        name="tweet_id",
                        required=True,
                        type=str,
                        description="ID of the tweet to like"
                    )
                ],
                description="Like a tweet with the given ID"
            ),
            "retweet-tweet": Action(
                name="retweet-tweet",
                parameters=[
                    ActionParameter(
                        name="tweet_id",
                        required=True,
                        type=str,
                        description="ID of the tweet to retweet"
                    )
                ],
                description="Retweet a tweet with the given ID"
            )
        }

    def search_tweets(self, query: str, count: int = 20) -> Dict:
        """Search for tweets using the given query."""
        if not self.is_configured():
            return {"error": "Twitter client not configured"}
        
        try:
            results = self.client.search_tweets(query, count)
            return {
                "status": "success",
                "data": results
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def post_tweet(self, text: str, media_paths: List[str] = None) -> Dict:
        """Post a new tweet with optional media attachments."""
        if not self.is_configured():
            return {"error": "Twitter client not configured"}
        
        try:
            result = self.client.post_tweet(text, media_paths)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def like_tweet(self, tweet_id: str) -> Dict:
        """Like a tweet with the given ID."""
        if not self.is_configured():
            return {"error": "Twitter client not configured"}
        
        try:
            result = self.client.like_tweet(tweet_id)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def retweet_tweet(self, tweet_id: str) -> Dict:
        """Retweet a tweet with the given ID."""
        if not self.is_configured():
            return {"error": "Twitter client not configured"}
        
        try:
            result = self.client.retweet_tweet(tweet_id)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

class TwitterClient:
    def __init__(self, username=None, password=None, cookies_file="cookies.json"):
        self.username = username
        self.password = password
        self.cookies = {}
        self.cookies_file = cookies_file
        self.is_logged_in = False

        # Initialize session
        self.session = requests.Session()

        # Load cookies if they exist
        if os.path.exists(self.cookies_file):
            self.load_cookies()

        # If username and password were provided, try login
        if username and password and not self.is_logged_in:
            self.login()

    def login(self):
        print("Login not implemented yet. Using cookies.json if available.")
        self.is_logged_in = True

    def save_cookies(self):
        with open(self.cookies_file, "w") as f:
            json.dump(requests.utils.dict_from_cookiejar(self.session.cookies), f)
        print("Cookies saved to", self.cookies_file)

    def load_cookies(self):
        try:
            with open(self.cookies_file, "r") as f:
                self.cookies = json.load(f)
                self.session.cookies = requests.utils.cookiejar_from_dict(self.cookies)
                self.is_logged_in = True
                print("Cookies loaded from", self.cookies_file)
        except FileNotFoundError:
            print("Cookies file not found.")
        except json.JSONDecodeError:
            print("Error decoding cookies file. Ignoring.")

    def _api_request(self, url, method="GET", params=None, data=None, headers=None):
        """Handles API requests with session and cookie management."""
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        all_headers = default_headers.copy()
        if headers:
            all_headers.update(headers)

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, headers=all_headers)
            elif method.upper() == "POST":
                response = self.session.post(url, data=data, params=params, headers=all_headers)
            else:
                raise ValueError("Invalid HTTP method")

            response.raise_for_status()
            return response.json() if 'json' in response.headers.get('Content-Type', '') else response.text
        except requests.exceptions.RequestException as e:
            print(f"API Request Error: {e}")
            return None

    def search_tweets(self, query, count=20):
        """Searches for tweets using a given query."""
        search_url = "https://api.twitter.com/2/tweets/search/recent"
        params = {
            "query": query,
            "max_results": count
        }
        
        headers = {
            "Authorization": f"Bearer YOUR_BEARER_TOKEN_HERE",
            "Content-Type": "application/json"
        }
        
        data = self._api_request(search_url, method="GET", params=params, headers=headers)
        if data:
            return data
        else:
            print("Tweet search failed.")
            return None

    def post_tweet(self, text, media_paths=None):
        print("Posting is not implemented. Please use the Twitter API v1 or v2.")
        return None

    def like_tweet(self, tweet_id):
        print("Liking is not implemented. Please use the Twitter API v1 or v2.")
        return None

    def retweet_tweet(self, tweet_id):
        print("Retweeting is not implemented. Please use the Twitter API v1 or v2.")
        return None 