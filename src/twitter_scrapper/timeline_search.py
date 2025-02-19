from typing import Dict, Any, TypeVar, List
from dataclasses import dataclass

from timeline_v1 import QueryTweetsResponse, QueryProfilesResponse
from tweets import Tweet
from profile import Profile

# Type alias for search timeline response
SearchTimeline = Dict[str, Any]

def parse_search_timeline_tweets(timeline: SearchTimeline) -> QueryTweetsResponse:
    """
    Parse search timeline response into tweets.
    
    Args:
        timeline: Raw search timeline response from Twitter API
        
    Returns:
        QueryTweetsResponse with parsed tweets and cursor
    """
    tweets = []
    next_cursor = None
    
    instructions = timeline.get('data', {}).get('search_by_raw_query', {}).get('search_timeline', {}).get('timeline', {}).get('instructions', [])
    
    for instruction in instructions:
        if instruction['type'] == 'TimelineAddEntries':
            for entry in instruction['entries']:
                if 'tweet' in entry['content']:
                    tweet_result = entry['content']['tweet']['result']
                    if tweet_result['__typename'] == 'Tweet':
                        tweets.append(Tweet.from_timeline_result(tweet_result))
                elif entry['content'].get('type') == 'TimelineTimelineCursor' and entry['content'].get('cursorType') == 'Bottom':
                    next_cursor = entry['content'].get('value')
                    
    return QueryTweetsResponse(tweets=tweets, next_cursor=next_cursor)

def parse_search_timeline_users(timeline: SearchTimeline) -> QueryProfilesResponse:
    """
    Parse search timeline response into user profiles.
    
    Args:
        timeline: Raw search timeline response from Twitter API
        
    Returns:
        QueryProfilesResponse with parsed profiles and cursor
    """
    profiles = []
    next_cursor = None
    
    instructions = timeline.get('data', {}).get('search_by_raw_query', {}).get('search_timeline', {}).get('timeline', {}).get('instructions', [])
    
    for instruction in instructions:
        if instruction['type'] == 'TimelineAddEntries':
            for entry in instruction['entries']:
                if 'user' in entry['content']:
                    user_result = entry['content']['user']['result']
                    if user_result['__typename'] == 'User':
                        profiles.append(Profile.from_timeline_result(user_result))
                elif entry['content'].get('type') == 'TimelineTimelineCursor' and entry['content'].get('cursorType') == 'Bottom':
                    next_cursor = entry['content'].get('value')
                    
    return QueryProfilesResponse(profiles=profiles, next_cursor=next_cursor) 