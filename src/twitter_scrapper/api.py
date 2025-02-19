from typing import Dict, Any, Union, Optional, Tuple, TypeVar, Generic
import json
import aiohttp
import asyncio
from datetime import datetime
from exceptions import ApiError
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

# Twitter API constants and configuration
BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAAFQODgEAAAAAVHTp76lzh3rFzcHbmHVvQxYYpTw%3DckAlMINMjmCaXbAN4XqJVdgMJaHqNOFgPMK0zN1qLqLQCF'


__all__ = [
    'BEARER_TOKEN',
    'request_api',
    'add_api_features',
    'ApiRequestResult',
    'ApiRequestError'
]

T = TypeVar('T')

@dataclass
class ApiRequestError:
    """API request error details."""
    status: int
    data: Dict[str, Any]
    message: str

@dataclass
class ApiRequestResult(Generic[T]):
    """API request result with success/error status."""
    success: bool
    value: Optional[T] = None
    err: Optional[ApiRequestError] = None

async def request_api(url: str, auth, method: str = 'GET', body: dict = None) -> Tuple[bool, Union[dict, ApiError]]:
    """
    Sends an HTTP request to the Twitter API using aiohttp.

    Args:
        url: The URL to send the request to.
        auth: The authentication object.
        method: The HTTP method (GET or POST).
        body: The request body (for POST requests).

    Returns:
        A tuple containing a boolean indicating success and either the JSON response or an ApiError.
    """
    # Prepare headers with proper compression handling
    headers = {
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
        'Accept-Language': 'en-US,en;q=0.9'
    }

    # Install auth headers
    await auth.install_to(headers, url)

    try:
        if method == 'GET':
            async with auth.client.session.get(url, headers=headers, ssl=False) as response:
                if not response.ok:
                    error = await ApiError.from_response(response)
                    return False, error
                return True, await response.json()
        elif method == 'POST':
            async with auth.client.session.post(url, headers=headers, json=body, ssl=False) as response:
                if not response.ok:
                    error = await ApiError.from_response(response)
                    return False, error
                return True, await response.json()
        else:
            return False, ValueError("Invalid method. Must be GET or POST")

    except ApiError as e:
        return False, e
    except Exception as e:
        return False, ApiError(None, None, str(e))

def add_api_features(o: dict) -> dict:
    """Adds feature flags to a dictionary."""
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
    return {**o, **features}

def add_api_params(params: dict, include_tweet_replies: bool) -> dict:
    """Adds common query parameters to a dictionary."""
    params["include_profile_interstitial_type"] = '1'
    params["include_blocking"] = '1'
    params["include_blocked_by"] = '1'
    params["include_followed_by"] = '1'
    params["include_want_retweets"] = '1'
    params["include_mute_edge"] = '1'
    params["include_can_dm"] = '1'
    params["include_can_media_tag"] = '1'
    params["include_ext_has_nft_avatar"] = '1'
    params["include_ext_is_blue_verified"] = '1'
    params["include_ext_verified_type"] = '1'
    params["skip_status"] = '1'
    params["cards_platform"] = 'Web-12'
    params["include_cards"] = '1'
    params["include_ext_alt_text"] = 'true'
    params["include_ext_limited_action_results"] = 'false'
    params["include_quote_count"] = 'true'
    params["include_reply_count"] = '1'
    params["tweet_mode"] = 'extended'
    params["include_ext_collab_control"] = 'true'
    params["include_ext_views"] = 'true'
    params["include_entities"] = 'true'
    params["include_user_entities"] = 'true'
    params["include_ext_media_color"] = 'true'
    params["include_ext_media_availability"] = 'true'
    params["include_ext_sensitive_media_warning"] = 'true'
    params["include_ext_trusted_friends_metadata"] = 'true'
    params["send_error_codes"] = 'true'
    params["simple_quoted_tweet"] = 'true'
    params["include_tweet_replies"] = str(include_tweet_replies).lower()
    params["ext"] = 'mediaStats,highlightedLabel,hasNftAvatar,voiceInfo,birdwatchPivot,enrichments,superFollowMetadata,unmentionInfo,editControl,collab_control,vibe'
    return params