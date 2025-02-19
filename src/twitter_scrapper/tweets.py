from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime

@dataclass
class Tweet:
    """A Twitter tweet."""
    id: str
    text: str
    created_at: str
    author_id: str
    author_username: str
    author_name: str
    reply_count: int
    retweet_count: int
    like_count: int
    quote_count: int
    conversation_id: str
    lang: str
    source: str
    source_url: Optional[str]
    source_label: Optional[str]
    views: int
    in_reply_to_status_id: Optional[str]
    in_reply_to_user_id: Optional[str]
    in_reply_to_screen_name: Optional[str]
    quoted_status_id: Optional[str]
    retweeted_status_id: Optional[str]
    retweeted: bool
    favorited: bool
    possibly_sensitive: bool
    filter_level: Optional[str]
    withheld_copyright: bool
    withheld_in_countries: List[str]
    withheld_scope: Optional[str]
    place: Optional[Dict[str, Any]]
    coordinates: Optional[Dict[str, Any]]
    entities: Dict[str, Any]
    extended_entities: Dict[str, Any]
    card: Optional[Dict[str, Any]]
    note_tweet: Optional[Dict[str, Any]]
    edit_control: Dict[str, Any]
    edit_perspective: Dict[str, Any]
    is_translatable: bool
    views_blue: bool
    trusted_friends_info: Dict[str, Any]
    collaboration_control_info: Dict[str, Any]

    @classmethod
    def from_timeline_result(cls, result: Dict[str, Any]) -> 'Tweet':
        """
        Create a Tweet from timeline API result.
        
        Args:
            result: Raw tweet data from timeline
            
        Returns:
            Tweet object
        """
        legacy = result.get('legacy', {})
        user = result.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {})
        
        return cls(
            id=legacy.get('id_str'),
            text=legacy.get('full_text', ''),
            created_at=legacy.get('created_at'),
            author_id=user.get('id_str'),
            author_username=user.get('screen_name'),
            author_name=user.get('name'),
            reply_count=legacy.get('reply_count', 0),
            retweet_count=legacy.get('retweet_count', 0),
            like_count=legacy.get('favorite_count', 0),
            quote_count=legacy.get('quote_count', 0),
            conversation_id=legacy.get('conversation_id_str'),
            lang=legacy.get('lang'),
            source=legacy.get('source'),
            source_url=None,  # Not available in timeline result
            source_label=None,  # Not available in timeline result
            views=result.get('views', {}).get('count', 0),
            in_reply_to_status_id=legacy.get('in_reply_to_status_id_str'),
            in_reply_to_user_id=legacy.get('in_reply_to_user_id_str'),
            in_reply_to_screen_name=legacy.get('in_reply_to_screen_name'),
            quoted_status_id=legacy.get('quoted_status_id_str'),
            retweeted_status_id=legacy.get('retweeted_status_id_str'),
            retweeted=legacy.get('retweeted', False),
            favorited=legacy.get('favorited', False),
            possibly_sensitive=legacy.get('possibly_sensitive', False),
            filter_level=legacy.get('filter_level'),
            withheld_copyright=legacy.get('withheld_copyright', False),
            withheld_in_countries=legacy.get('withheld_in_countries', []),
            withheld_scope=legacy.get('withheld_scope'),
            place=legacy.get('place'),
            coordinates=legacy.get('coordinates'),
            entities=legacy.get('entities', {}),
            extended_entities=legacy.get('extended_entities', {}),
            card=legacy.get('card'),
            note_tweet=result.get('note_tweet', {}).get('note_tweet_results', {}).get('result', {}),
            edit_control=result.get('edit_control', {}),
            edit_perspective=result.get('edit_perspective', {}),
            is_translatable=result.get('is_translatable', False),
            views_blue=result.get('views_blue', False),
            trusted_friends_info=result.get('trusted_friends_info', {}),
            collaboration_control_info=result.get('collaboration_control_info', {})
        )

@dataclass
class TweetQuery:
    """Query parameters for filtering tweets."""
    text: Optional[str] = None
    min_replies: Optional[int] = None
    min_retweets: Optional[int] = None
    min_likes: Optional[int] = None
    exclude_replies: bool = False
    exclude_retweets: bool = False
    exclude_quotes: bool = False
    include_retweets: bool = True
    include_quotes: bool = True
    include_replies: bool = True
    min_date: Optional[datetime] = None
    max_date: Optional[datetime] = None

@dataclass
class PollData:
    """Data for creating a poll in a tweet."""
    duration_minutes: int
    options: List[str]

@dataclass
class Retweeter:
    """User who retweeted a tweet."""
    user_id: str
    screen_name: str
    name: str
    profile_image_url: str

def create_create_tweet_request(
    text: str,
    reply_to_tweet_id: Optional[str] = None,
    media_data: Optional[List[Dict[str, Any]]] = None,
    hide_link_preview: bool = False
) -> Dict[str, Any]:
    """
    Create request body for posting a tweet.
    
    Args:
        text: Tweet text content
        reply_to_tweet_id: Optional ID of tweet to reply to
        media_data: Optional list of media attachments
        hide_link_preview: Whether to hide link previews
        
    Returns:
        Request body dictionary
    """
    variables = {
        'tweet_text': text,
        'dark_request': False,
        'media': {
            'media_entities': media_data or [],
            'possibly_sensitive': False
        },
        'semantic_annotation_ids': []
    }
    
    if reply_to_tweet_id:
        variables['reply'] = {
            'in_reply_to_tweet_id': reply_to_tweet_id,
            'exclude_reply_user_ids': []
        }
        
    if hide_link_preview:
        variables['card_uri'] = ''
        
    features = {
        'tweetypie_unmention_optimization_enabled': True,
        'responsive_web_edit_tweet_api_enabled': True,
        'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
        'view_counts_everywhere_api_enabled': True,
        'longform_notetweets_consumption_enabled': True,
        'responsive_web_twitter_article_tweet_consumption_enabled': False,
        'tweet_awards_web_tipping_enabled': False,
        'longform_notetweets_rich_text_read_enabled': True,
        'longform_notetweets_inline_media_enabled': True,
        'responsive_web_graphql_exclude_directive_enabled': True,
        'verified_phone_label_enabled': False,
        'freedom_of_speech_not_reach_fetch_enabled': True,
        'standardized_nudges_misinfo': True,
        'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
        'responsive_web_media_download_video_enabled': False,
        'responsive_web_enhance_cards_enabled': False
    }
    
    field_toggles = {
        'withArticleRichContentState': False
    }
    
    return {
        'variables': variables,
        'features': features,
        'fieldToggles': field_toggles,
        'queryId': 'SoVnbfCycZ7fERGCwpZkYA'
    }

def create_create_tweet_request_v2(
    text: str,
    reply_to_tweet_id: Optional[str] = None,
    poll_data: Optional[PollData] = None
) -> Dict[str, Any]:
    """
    Create request body for posting a tweet using v2 API.
    
    Args:
        text: Tweet text content
        reply_to_tweet_id: Optional ID of tweet to reply to
        poll_data: Optional poll data
        
    Returns:
        Request body dictionary
    """
    variables = {
        'tweet_text': text,
        'dark_request': False,
        'semantic_annotation_ids': []
    }
    
    if reply_to_tweet_id:
        variables['reply'] = {
            'in_reply_to_tweet_id': reply_to_tweet_id,
            'exclude_reply_user_ids': []
        }
        
    if poll_data:
        variables['poll_options'] = poll_data.options
        variables['poll_duration_minutes'] = poll_data.duration_minutes
        
    features = {
        'tweetypie_unmention_optimization_enabled': True,
        'responsive_web_edit_tweet_api_enabled': True,
        'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
        'view_counts_everywhere_api_enabled': True,
        'longform_notetweets_consumption_enabled': True,
        'responsive_web_twitter_article_tweet_consumption_enabled': False,
        'tweet_awards_web_tipping_enabled': False,
        'longform_notetweets_rich_text_read_enabled': True,
        'longform_notetweets_inline_media_enabled': True,
        'responsive_web_graphql_exclude_directive_enabled': True,
        'verified_phone_label_enabled': False,
        'freedom_of_speech_not_reach_fetch_enabled': True,
        'standardized_nudges_misinfo': True,
        'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
        'responsive_web_media_download_video_enabled': False,
        'responsive_web_enhance_cards_enabled': False
    }
    
    field_toggles = {
        'withArticleRichContentState': False
    }
    
    return {
        'variables': variables,
        'features': features,
        'fieldToggles': field_toggles,
        'queryId': 'SoVnbfCycZ7fERGCwpZkYA'
    }

def create_quote_tweet_request(
    text: str,
    quoted_tweet_id: str,
    media_data: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Create request body for posting a quote tweet.
    
    Args:
        text: Tweet text content
        quoted_tweet_id: ID of tweet to quote
        media_data: Optional list of media attachments
        
    Returns:
        Request body dictionary
    """
    variables = {
        'tweet_text': text,
        'quoted_tweet_id': quoted_tweet_id,
        'dark_request': False,
        'media': {
            'media_entities': media_data or [],
            'possibly_sensitive': False
        },
        'semantic_annotation_ids': []
    }
    
    features = {
        'tweetypie_unmention_optimization_enabled': True,
        'responsive_web_edit_tweet_api_enabled': True,
        'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
        'view_counts_everywhere_api_enabled': True,
        'longform_notetweets_consumption_enabled': True,
        'responsive_web_twitter_article_tweet_consumption_enabled': False,
        'tweet_awards_web_tipping_enabled': False,
        'longform_notetweets_rich_text_read_enabled': True,
        'longform_notetweets_inline_media_enabled': True,
        'responsive_web_graphql_exclude_directive_enabled': True,
        'verified_phone_label_enabled': False,
        'freedom_of_speech_not_reach_fetch_enabled': True,
        'standardized_nudges_misinfo': True,
        'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
        'responsive_web_media_download_video_enabled': False,
        'responsive_web_enhance_cards_enabled': False
    }
    
    field_toggles = {
        'withArticleRichContentState': False
    }
    
    return {
        'variables': variables,
        'features': features,
        'fieldToggles': field_toggles,
        'queryId': 'SoVnbfCycZ7fERGCwpZkYA'
    }

def create_create_note_tweet_request(
    text: str,
    reply_to_tweet_id: Optional[str] = None,
    media_data: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Create request body for posting a note tweet.
    
    Args:
        text: Tweet text content
        reply_to_tweet_id: Optional ID of tweet to reply to
        media_data: Optional list of media attachments
        
    Returns:
        Request body dictionary
    """
    variables = {
        'tweet_text': text,
        'dark_request': False,
        'media': {
            'media_entities': media_data or [],
            'possibly_sensitive': False
        },
        'semantic_annotation_ids': []
    }
    
    if reply_to_tweet_id:
        variables['reply'] = {
            'in_reply_to_tweet_id': reply_to_tweet_id,
            'exclude_reply_user_ids': []
        }
        
    features = {
        'tweetypie_unmention_optimization_enabled': True,
        'responsive_web_edit_tweet_api_enabled': True,
        'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
        'view_counts_everywhere_api_enabled': True,
        'longform_notetweets_consumption_enabled': True,
        'responsive_web_twitter_article_tweet_consumption_enabled': False,
        'tweet_awards_web_tipping_enabled': False,
        'longform_notetweets_rich_text_read_enabled': True,
        'longform_notetweets_inline_media_enabled': True,
        'responsive_web_graphql_exclude_directive_enabled': True,
        'verified_phone_label_enabled': False,
        'freedom_of_speech_not_reach_fetch_enabled': True,
        'standardized_nudges_misinfo': True,
        'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
        'responsive_web_media_download_video_enabled': False,
        'responsive_web_enhance_cards_enabled': False
    }
    
    field_toggles = {
        'withArticleRichContentState': False
    }
    
    return {
        'variables': variables,
        'features': features,
        'fieldToggles': field_toggles,
        'queryId': 'SoVnbfCycZ7fERGCwpZkYA'
    }

def create_create_long_tweet_request(
    text: str,
    reply_to_tweet_id: Optional[str] = None,
    media_data: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Create request body for posting a long tweet.
    
    Args:
        text: Tweet text content
        reply_to_tweet_id: Optional ID of tweet to reply to
        media_data: Optional list of media attachments
        
    Returns:
        Request body dictionary
    """
    variables = {
        'tweet_text': text,
        'dark_request': False,
        'media': {
            'media_entities': media_data or [],
            'possibly_sensitive': False
        },
        'semantic_annotation_ids': []
    }
    
    if reply_to_tweet_id:
        variables['reply'] = {
            'in_reply_to_tweet_id': reply_to_tweet_id,
            'exclude_reply_user_ids': []
        }
        
    features = {
        'tweetypie_unmention_optimization_enabled': True,
        'responsive_web_edit_tweet_api_enabled': True,
        'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
        'view_counts_everywhere_api_enabled': True,
        'longform_notetweets_consumption_enabled': True,
        'responsive_web_twitter_article_tweet_consumption_enabled': False,
        'tweet_awards_web_tipping_enabled': False,
        'longform_notetweets_rich_text_read_enabled': True,
        'longform_notetweets_inline_media_enabled': True,
        'responsive_web_graphql_exclude_directive_enabled': True,
        'verified_phone_label_enabled': False,
        'freedom_of_speech_not_reach_fetch_enabled': True,
        'standardized_nudges_misinfo': True,
        'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
        'responsive_web_media_download_video_enabled': False,
        'responsive_web_enhance_cards_enabled': False
    }
    
    field_toggles = {
        'withArticleRichContentState': False
    }
    
    return {
        'variables': variables,
        'features': features,
        'fieldToggles': field_toggles,
        'queryId': 'SoVnbfCycZ7fERGCwpZkYA'
    } 