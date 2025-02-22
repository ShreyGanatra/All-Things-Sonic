from typing import AsyncGenerator, Callable, Optional, TypeVar, Awaitable

from profile import Profile
from src.twitter_scrapper.tweets import Tweet
from src.twitter_scrapper.timeline_v1 import QueryTweetsResponse, QueryProfilesResponse

T = TypeVar('T', Tweet, Profile)
QueryResponse = TypeVar('QueryResponse', QueryTweetsResponse, QueryProfilesResponse)

async def get_timeline(
    query: str,
    max_items: int,
    fetch_callback: Callable[[str, int, Optional[str]], Awaitable[QueryResponse]]
) -> AsyncGenerator[T, None]:
    """
    Generic timeline fetcher that handles pagination.
    
    Args:
        query: Search query string
        max_items: Maximum items to return
        fetch_callback: Function to fetch a page of results
        
    Yields:
        Items from the timeline (tweets or profiles)
    """
    items_returned = 0
    cursor = None
    
    while items_returned < max_items:
        # Calculate how many items to request in this batch
        items_to_fetch = min(50, max_items - items_returned)
        
        # Fetch the next page
        result = await fetch_callback(query, items_to_fetch, cursor)
        
        # Extract items and cursor from response
        if isinstance(result, QueryTweetsResponse):
            items = result.tweets
            cursor = result.next_cursor
        else:
            items = result.profiles
            cursor = result.next_cursor
            
        # Yield each item
        for item in items:
            yield item
            items_returned += 1
            if items_returned >= max_items:
                break
                
        # Stop if no more pages
        if not cursor:
            break

async def get_tweet_timeline(
    query: str,
    max_tweets: int,
    fetch_callback: Callable[[str, int, Optional[str]], Awaitable[QueryTweetsResponse]]
) -> AsyncGenerator[Tweet, None]:
    """
    Fetch tweets from a timeline with pagination.
    
    Args:
        query: Search query string
        max_tweets: Maximum tweets to return
        fetch_callback: Function to fetch a page of tweets
        
    Yields:
        Tweet objects from the timeline
    """
    async for tweet in get_timeline(query, max_tweets, fetch_callback):
        yield tweet

async def get_user_timeline(
    query: str,
    max_profiles: int,
    fetch_callback: Callable[[str, int, Optional[str]], Awaitable[QueryProfilesResponse]]
) -> AsyncGenerator[Profile, None]:
    """
    Fetch user profiles from a timeline with pagination.
    
    Args:
        query: Search query string
        max_profiles: Maximum profiles to return
        fetch_callback: Function to fetch a page of profiles
        
    Yields:
        Profile objects from the timeline
    """
    async for profile in get_timeline(query, max_profiles, fetch_callback):
        yield profile 