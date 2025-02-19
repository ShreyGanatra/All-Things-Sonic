from typing import Optional, Dict, Any, AsyncGenerator, List
import json
from urllib.parse import urlencode
from enum import Enum

from api import request_api, add_api_features
from twitter_auth_base import TwitterAuthBase
from profile import Profile
from timeline_v1 import QueryProfilesResponse, QueryTweetsResponse
from timeline_async import get_tweet_timeline, get_user_timeline
from tweets import Tweet
from timeline_search import (
    SearchTimeline,
    parse_search_timeline_tweets,
    parse_search_timeline_users
)

class SearchMode(Enum):
    """Search mode for tweets"""
    LATEST = "Latest"
    TOP = "Top"
    PHOTOS = "Photos"
    VIDEOS = "Videos"
    USERS = "People"

class SearchAPI:
    def __init__(self, auth):
        self.auth = auth

    async def search_tweets(self, query: str, mode: SearchMode = SearchMode.LATEST, max_tweets: int = 20) -> List[Dict[str, Any]]:
        """
        Search for tweets using Twitter's GraphQL API.
        
        Args:
            query: Search query string
            mode: Search mode (Latest, Top, Photos, Videos, Users)
            max_tweets: Maximum number of tweets to return
            
        Returns:
            List of tweet objects
        """
        # Prepare request parameters
        variables = {
            'rawQuery': query,
            'count': max_tweets,
            'querySource': 'typed_query',
            'product': mode.value,
            'withDownvotePerspective': False,
            'withReactionsMetadata': False,
            'withReactionsPerspective': False
        }
        
        features = {
            'responsive_web_graphql_exclude_directive_enabled': True,
            'verified_phone_label_enabled': False,
            'creator_subscriptions_tweet_preview_api_enabled': True,
            'responsive_web_graphql_timeline_navigation_enabled': True,
            'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
            'c9s_tweet_anatomy_moderator_badge_enabled': True,
            'tweetypie_unmention_optimization_enabled': True,
            'responsive_web_edit_tweet_api_enabled': True,
            'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
            'view_counts_everywhere_api_enabled': True,
            'longform_notetweets_consumption_enabled': True,
            'responsive_web_twitter_article_tweet_consumption_enabled': False,
            'tweet_awards_web_tipping_enabled': False,
            'freedom_of_speech_not_reach_fetch_enabled': True,
            'standardized_nudges_misinfo': True,
            'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
            'longform_notetweets_rich_text_read_enabled': True,
            'longform_notetweets_inline_media_enabled': True,
            'responsive_web_media_download_video_enabled': False,
            'responsive_web_enhance_cards_enabled': False,
            'interactive_text_enabled': True,
            'vibe_api_enabled': True,
            'responsive_web_text_conversations_enabled': True,
            'blue_business_profile_image_shape_enabled': True
        }
        
        field_toggles = {
            'withArticleRichContentState': False
        }
        
        # Construct the URL with parameters
        params = {
            'variables': json.dumps(variables),
            'features': json.dumps(features),
            'fieldToggles': json.dumps(field_toggles)
        }
        
        url = f'https://twitter.com/i/api/graphql/gkjsKepM6gl_HmFWoWKfgg/SearchTimeline?{urlencode(params)}'
        
        # Prepare headers
        headers = {
            'authorization': f'Bearer {self.auth.bearer_token}',
            'content-type': 'application/json',
            'x-twitter-auth-type': 'OAuth2Client',
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'en',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Nokia G20) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.88 Mobile Safari/537.36',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://twitter.com/search'
        }
        
        # Install auth headers
        await self.auth.install_to(headers, url)
        
        # Make request
        async with self.auth.session.get(url, headers=headers) as response:
            if not response.ok:
                error_text = await response.text()
                raise Exception(f"Search failed: {response.status} - {error_text}")
                
            data = await response.json()
            
            tweets = []
            # Parse results following timeline-search.ts structure
            instructions = data.get('data', {}).get('search_by_raw_query', {}).get('search_timeline', {}).get('timeline', {}).get('instructions', [])
            
            for instruction in instructions:
                if instruction.get('type') == 'TimelineAddEntries':
                    entries = instruction.get('entries', [])
                    for entry in entries:
                        item_content = entry.get('content', {}).get('itemContent', {})
                        if item_content.get('tweetDisplayType') == 'Tweet':
                            tweet_result = item_content.get('tweet_results', {}).get('result', {})
                            legacy = tweet_result.get('legacy', {})
                            user = tweet_result.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {})
                            
                            tweet = {
                                'id': legacy.get('id_str'),
                                'text': legacy.get('full_text'),
                                'created_at': legacy.get('created_at'),
                                'favorite_count': legacy.get('favorite_count', 0),
                                'retweet_count': legacy.get('retweet_count', 0),
                                'views': tweet_result.get('views', {}).get('count'),
                                'user': {
                                    'id': user.get('id_str'),
                                    'screen_name': user.get('screen_name'),
                                    'name': user.get('name'),
                                    'profile_image_url': user.get('profile_image_url_https'),
                                    'verified': user.get('verified', False)
                                }
                            }
                            tweets.append(tweet)
            
            return tweets

def search_profiles(
    query: str,
    max_profiles: int,
    auth: TwitterAuthBase
) -> AsyncGenerator[Profile, None]:
    """
    Search for user profiles matching the given query.
    
    Args:
        query: The search query
        max_profiles: Maximum number of profiles to return
        auth: TwitterAuth instance for authorization
        
    Yields:
        Profile objects matching the search criteria
    """
    for profile in get_user_timeline(query, max_profiles, lambda q, mt, c:
        fetch_search_profiles(q, mt, auth, c)):
        yield profile

def fetch_search_tweets(
    query: str,
    max_tweets: int,
    search_mode: SearchMode,
    auth: TwitterAuthBase,
    cursor: Optional[str] = None
) -> QueryTweetsResponse:
    """
    Fetch a page of tweets matching the search query.
    
    Args:
        query: The search query
        max_tweets: Maximum tweets per page
        search_mode: Category filter to apply
        auth: TwitterAuth instance for authorization
        cursor: Optional pagination cursor
        
    Returns:
        QueryTweetsResponse containing tweets and next cursor
    """
    timeline = get_search_timeline(query, max_tweets, search_mode, auth, cursor)
    return parse_search_timeline_tweets(timeline)

def fetch_search_profiles(
    query: str,
    max_profiles: int,
    auth: TwitterAuthBase,
    cursor: Optional[str] = None
) -> QueryProfilesResponse:
    """
    Fetch a page of profiles matching the search query.
    
    Args:
        query: The search query
        max_profiles: Maximum profiles per page
        auth: TwitterAuth instance for authorization
        cursor: Optional pagination cursor
        
    Returns:
        QueryProfilesResponse containing profiles and next cursor
    """
    timeline = get_search_timeline(query, max_profiles, SearchMode.USERS, auth, cursor)
    return parse_search_timeline_users(timeline)

def get_search_timeline(
    query: str,
    max_items: int,
    search_mode: SearchMode,
    auth: TwitterAuthBase,
    cursor: Optional[str] = None
) -> SearchTimeline:
    """
    Get the raw search timeline response from Twitter's API.
    
    Args:
        query: The search query
        max_items: Maximum items to return
        search_mode: Category filter to apply
        auth: TwitterAuth instance for authorization
        cursor: Optional pagination cursor
        
    Returns:
        Raw SearchTimeline response from Twitter
    """
    if not auth.is_logged_in():
        raise Exception('Scraper is not logged-in for search.')

    if max_items > 50:
        max_items = 50

    variables: Dict[str, Any] = {
        'rawQuery': query,
        'count': max_items,
        'querySource': 'typed_query',
        'product': 'Top'
    }

    features = add_api_features({
        'longform_notetweets_inline_media_enabled': True,
        'responsive_web_enhance_cards_enabled': False,
        'responsive_web_media_download_video_enabled': False,
        'responsive_web_twitter_article_tweet_consumption_enabled': False,
        'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
        'interactive_text_enabled': False,
        'responsive_web_text_conversations_enabled': False,
        'vibe_api_enabled': False
    })

    field_toggles = {
        'withArticleRichContentState': False
    }

    if cursor:
        variables['cursor'] = cursor

    # Set product based on search mode
    if search_mode == SearchMode.LATEST:
        variables['product'] = 'Latest'
    elif search_mode == SearchMode.PHOTOS:
        variables['product'] = 'Photos'
    elif search_mode == SearchMode.VIDEOS:
        variables['product'] = 'Videos'
    elif search_mode == SearchMode.USERS:
        variables['product'] = 'People'

    params = {
        'variables': json.dumps(variables),
        'features': json.dumps(features),
        'fieldToggles': json.dumps(field_toggles)
    }

    url = f'https://api.twitter.com/graphql/gkjsKepM6gl_HmFWoWKfgg/SearchTimeline?{urlencode(params)}'
    
    result = request_api(url, auth)
    if not result.success:
        raise result.err

    return result.value

def fetch_quoted_tweets_page(
    quoted_tweet_id: str,
    max_tweets: int,
    auth: TwitterAuthBase,
    cursor: Optional[str] = None
) -> QueryTweetsResponse:
    """
    Fetch one page of tweets that quote a given tweet ID.
    
    Args:
        quoted_tweet_id: The tweet ID to find quotes of
        max_tweets: Maximum tweets per page
        auth: TwitterAuth instance for authorization
        cursor: Optional pagination cursor
        
    Returns:
        QueryTweetsResponse containing tweets and next cursor
    """
    if max_tweets > 50:
        max_tweets = 50

    variables = {
        'rawQuery': f'quoted_tweet_id:{quoted_tweet_id}',
        'count': max_tweets,
        'querySource': 'tdqt',
        'product': 'Top'
    }

    if cursor:
        variables['cursor'] = cursor

    features = add_api_features({
        'profile_label_improvements_pcf_label_in_post_enabled': True,
        'rweb_tipjar_consumption_enabled': True,
        'responsive_web_graphql_exclude_directive_enabled': True,
        'verified_phone_label_enabled': False,
        'creator_subscriptions_tweet_preview_api_enabled': True,
        'responsive_web_graphql_timeline_navigation_enabled': True,
        'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
        'premium_content_api_read_enabled': False,
        'communities_web_enable_tweet_community_results_fetch': True,
        'c9s_tweet_anatomy_moderator_badge_enabled': True,
        'responsive_web_grok_analyze_button_fetch_trends_enabled': False,
        'responsive_web_grok_analyze_post_followups_enabled': True,
        'responsive_web_jetfuel_frame': False,
        'responsive_web_grok_share_attachment_enabled': True,
        'articles_preview_enabled': True,
        'responsive_web_edit_tweet_api_enabled': True,
        'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
        'view_counts_everywhere_api_enabled': True,
        'longform_notetweets_consumption_enabled': True,
        'responsive_web_twitter_article_tweet_consumption_enabled': True,
        'tweet_awards_web_tipping_enabled': False,
        'creator_subscriptions_quote_tweet_preview_enabled': False,
        'freedom_of_speech_not_reach_fetch_enabled': True,
        'standardized_nudges_misinfo': True,
        'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
        'rweb_video_timestamps_enabled': True,
        'longform_notetweets_rich_text_read_enabled': True,
        'longform_notetweets_inline_media_enabled': True,
        'responsive_web_grok_image_annotation_enabled': False,
        'responsive_web_enhance_cards_enabled': False
    })

    field_toggles = {
        'withArticleRichContentState': False
    }

    params = {
        'variables': json.dumps(variables),
        'features': json.dumps(features),
        'fieldToggles': json.dumps(field_toggles)
    }

    url = f'https://x.com/i/api/graphql/1BP5aKg8NvTNvRCyyCyq8g/SearchTimeline?{urlencode(params)}'

    result = request_api(url, auth)
    if not result.success:
        raise result.err

    return parse_search_timeline_tweets(result.value) 