from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from .tweets import Tweet

# Type alias for timeline response
TimelineV2 = Dict[str, Any]

@dataclass
class TimelineArticle:
    """Article in a timeline."""
    id: str
    text: str
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None

def parse_timeline_tweets_v2(timeline_result: Dict[str, Any]) -> Tweet:
    """
    Parse a tweet from a v2 timeline result.
    
    Args:
        timeline_result: Raw tweet data from timeline
        
    Returns:
        Parsed Tweet object
    """
    tweet_data = timeline_result.get('legacy', {})
    user_data = timeline_result.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {})
    
    # Extract tweet fields
    tweet = Tweet(
        id=tweet_data.get('id_str'),
        text=tweet_data.get('full_text', ''),
        created_at=tweet_data.get('created_at'),
        author_id=user_data.get('id_str'),
        author_username=user_data.get('screen_name'),
        author_name=user_data.get('name'),
        reply_count=tweet_data.get('reply_count', 0),
        retweet_count=tweet_data.get('retweet_count', 0),
        like_count=tweet_data.get('favorite_count', 0),
        quote_count=tweet_data.get('quote_count', 0),
        conversation_id=tweet_data.get('conversation_id_str'),
        lang=tweet_data.get('lang'),
        source=tweet_data.get('source'),
        source_url=None,  # Not available in v2
        source_label=None,  # Not available in v2
        views=timeline_result.get('views', {}).get('count', 0),
        in_reply_to_status_id=tweet_data.get('in_reply_to_status_id_str'),
        in_reply_to_user_id=tweet_data.get('in_reply_to_user_id_str'),
        in_reply_to_screen_name=tweet_data.get('in_reply_to_screen_name'),
        quoted_status_id=tweet_data.get('quoted_status_id_str'),
        retweeted_status_id=tweet_data.get('retweeted_status_id_str'),
        retweeted=tweet_data.get('retweeted', False),
        favorited=tweet_data.get('favorited', False),
        possibly_sensitive=tweet_data.get('possibly_sensitive', False),
        filter_level=tweet_data.get('filter_level'),
        withheld_copyright=tweet_data.get('withheld_copyright', False),
        withheld_in_countries=tweet_data.get('withheld_in_countries', []),
        withheld_scope=tweet_data.get('withheld_scope'),
        place=tweet_data.get('place'),
        coordinates=tweet_data.get('coordinates'),
        entities=tweet_data.get('entities', {}),
        extended_entities=tweet_data.get('extended_entities', {}),
        card=tweet_data.get('card'),
        note_tweet=timeline_result.get('note_tweet', {}).get('note_tweet_results', {}).get('result', {}),
        edit_control=timeline_result.get('edit_control', {}),
        edit_perspective=timeline_result.get('edit_perspective', {}),
        is_translatable=timeline_result.get('is_translatable', False),
        views_blue=timeline_result.get('views_blue', False),
        trusted_friends_info=timeline_result.get('trusted_friends_info', {}),
        collaboration_control_info=timeline_result.get('collaboration_control_info', {})
    )
    
    return tweet

def parse_timeline_article(article_result: Dict[str, Any]) -> TimelineArticle:
    """
    Parse an article from a timeline result.
    
    Args:
        article_result: Raw article data from timeline
        
    Returns:
        Parsed TimelineArticle object
    """
    article_data = article_result.get('article', {})
    
    return TimelineArticle(
        id=article_data.get('id_str'),
        text=article_data.get('text', ''),
        title=article_data.get('title'),
        description=article_data.get('description'),
        url=article_data.get('url')
    ) 