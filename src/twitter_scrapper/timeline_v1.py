from typing import List, Optional
from dataclasses import dataclass
from tweets import Tweet
from profile import Profile

@dataclass
class QueryTweetsResponse:
    """Response containing tweets and pagination cursor."""
    tweets: List[Tweet]
    next_cursor: Optional[str] = None

@dataclass
class QueryProfilesResponse:
    """Response containing profiles and pagination cursor."""
    profiles: List[Profile]
    next_cursor: Optional[str] = None

def parse_timeline_tweets(timeline: dict) -> QueryTweetsResponse:
    """
    Parse timeline response into tweets.
    
    Args:
        timeline: Raw timeline response from Twitter API
        
    Returns:
        QueryTweetsResponse with parsed tweets and cursor
    """
    tweets = []
    next_cursor = None
    
    instructions = timeline.get('data', {}).get('user', {}).get('result', {}).get('timeline', {}).get('instructions', [])
    
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

def parse_timeline_profiles(timeline: dict) -> QueryProfilesResponse:
    """
    Parse timeline response into profiles.
    
    Args:
        timeline: Raw timeline response from Twitter API
        
    Returns:
        QueryProfilesResponse with parsed profiles and cursor
    """
    profiles = []
    next_cursor = None
    
    instructions = timeline.get('data', {}).get('user', {}).get('result', {}).get('timeline', {}).get('instructions', [])
    
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