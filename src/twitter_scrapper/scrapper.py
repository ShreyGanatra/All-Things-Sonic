from dataclasses import dataclass
from typing import AsyncGenerator, Dict, List, Optional, Any, Union
from http.cookiejar import Cookie
from urllib.parse import urlencode
import os
import asyncio
from functools import partial

from src.twitter_scrapper.api import BEARER_TOKEN, request_api, ApiRequestResult
from src.twitter_scrapper.auth import TwitterUserAuth
from src.twitter_scrapper.twitter_auth_base import TwitterAuthBase, TwitterAuthOptions  
from src.twitter_scrapper.profile import (
    get_profile,
    get_user_id_by_screen_name,
    get_screen_name_by_user_id,
    Profile
)
from src.twitter_scrapper.search import (
    SearchAPI,
    SearchMode,
    search_profiles,
    fetch_search_tweets,
    fetch_search_profiles,
    fetch_quoted_tweets_page
)


from src.twitter_scrapper.timeline_v1 import QueryProfilesResponse, QueryTweetsResponse
from src.twitter_scrapper.tweets import (
    Tweet,
    create_create_tweet_request
)

TW_URL = 'https://twitter.com'
USER_TWEETS_URL = 'https://twitter.com/i/api/graphql/E3opETHurmVJflFsUBVuUQ/UserTweets'

@dataclass
class ScraperOptions:
    """Options for configuring the Twitter scraper."""
    fetch: Any  # Type for fetch function
    transform: Dict[str, Any]  # Transform options

class TwitterScraper:
    """
    An interface to Twitter's undocumented API.
    Reusing Scraper objects is recommended to minimize authentication overhead.
    """
    
    def __init__(self, bearer_token: str = None):
        """
        Create a new Scraper instance.
        
        Args:
            bearer_token: Optional bearer token, will use env var if not provided
        """
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN", BEARER_TOKEN)
        self.auth = None
        self.search_api = None
        self._event_loop = None

    def _ensure_event_loop(self):
        """Ensure we have an event loop to run async code"""
        try:
            self._event_loop = asyncio.get_event_loop()
        except RuntimeError:
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)

    async def login(self, username: str, password: str, email: str):
        """Login to Twitter with user credentials"""
        print("Creating TwitterUserAuth instance")
        self.auth = TwitterUserAuth(self.bearer_token)
        
        print("Starting login process")
        await self.auth.login(username, password, email)
        
        print("Checking login status")
        if not await self.auth.is_logged_in():
            raise Exception("Login failed: Unable to authenticate with provided credentials.")
        
        print("Creating SearchAPI instance")
        self.search_api = SearchAPI(self.auth)
        return self.auth

    async def search_tweets(
        self,
        query: str,
        search_mode: SearchMode = SearchMode.TOP,
        max_tweets: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for tweets.
        
        Args:
            query: Search query string
            search_mode: Category filter to apply (TOP, LATEST, PHOTOS, VIDEOS, USERS)
            max_tweets: Maximum number of tweets to return
            
        Returns:
            List of tweet dictionaries containing tweet data
        """
        if not self.search_api or not await self.auth.is_logged_in():
            raise ValueError("Must login before searching tweets")
            
        return await self.search_api.search_tweets(query, search_mode, max_tweets)

    async def send_tweet(
        self,
        text: str,
        replyToTweetId: str = None,
        mediaData: List[Dict[str, Any]] = None,
        hideLinkPreview: bool = False
    ) -> Dict[str, Any]:
        return await create_create_tweet_request(
            text,
            self.auth,
            replyToTweetId,
            mediaData,
            hideLinkPreview,
        );
