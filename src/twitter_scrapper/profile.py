# twitter_scraper/profile.py

import json
from typing import Optional, Dict, Any, List, Tuple, Union
from urllib.parse import urlencode
from dataclasses import dataclass
from twitter_auth_base import TwitterAuthBase

def get_avatar_original_size_url(url: str) -> str:
    """
    Appends '_orig' to the filename of a Twitter profile image URL to get the original size image.
    """
    return url.replace('_normal', '_orig')

@dataclass
class Profile:
    """A Twitter user profile."""
    id: str
    name: str
    screen_name: str
    description: str
    created_at: str
    followers_count: int
    friends_count: int
    statuses_count: int
    favourites_count: int
    listed_count: int
    media_count: int
    location: str
    verified: bool
    protected: bool
    profile_image_url: str
    profile_banner_url: Optional[str]
    profile_link_color: str
    pinned_tweet_ids: List[str]
    business_account: bool
    analytics_type: Optional[str]
    super_follows_eligible: bool
    super_followed_by: bool
    super_following: bool
    business_profile_state: str
    translator_type: str
    withheld_in_countries: List[str]
    verified_type: Optional[str]
    following: bool
    can_dm: bool
    following_by: bool
    notifications_enabled: bool
    muting: bool
    blocking: bool
    blocked_by: bool
    want_retweets: bool
    advertiser_account_type: Optional[str]
    advertiser_account_service_levels: List[str]
    analytics_access_level: Optional[str]
    is_blue_verified: bool
    has_nft_avatar: bool
    highlights_info: Dict[str, Any]
    creator_subscriptions_count: Optional[int]

    @classmethod
    def from_timeline_result(cls, result: Dict[str, Any]) -> 'Profile':
        """
        Create a Profile from timeline API result.
        
        Args:
            result: Raw profile data from timeline
            
        Returns:
            Profile object
        """
        legacy = result.get('legacy', {})
        
        return cls(
            id=legacy.get('id_str'),
            name=legacy.get('name', ''),
            screen_name=legacy.get('screen_name', ''),
            description=legacy.get('description', ''),
            created_at=legacy.get('created_at', ''),
            followers_count=legacy.get('followers_count', 0),
            friends_count=legacy.get('friends_count', 0),
            statuses_count=legacy.get('statuses_count', 0),
            favourites_count=legacy.get('favourites_count', 0),
            listed_count=legacy.get('listed_count', 0),
            media_count=legacy.get('media_count', 0),
            location=legacy.get('location', ''),
            verified=legacy.get('verified', False),
            protected=legacy.get('protected', False),
            profile_image_url=legacy.get('profile_image_url_https', ''),
            profile_banner_url=legacy.get('profile_banner_url'),
            profile_link_color=legacy.get('profile_link_color', ''),
            pinned_tweet_ids=legacy.get('pinned_tweet_ids_str', []),
            business_account=result.get('is_business_account', False),
            analytics_type=result.get('analytics_type'),
            super_follows_eligible=result.get('super_follows_eligible', False),
            super_followed_by=result.get('super_followed_by', False),
            super_following=result.get('super_following', False),
            business_profile_state=result.get('business_profile_state', ''),
            translator_type=legacy.get('translator_type', ''),
            withheld_in_countries=legacy.get('withheld_in_countries', []),
            verified_type=result.get('verified_type'),
            following=legacy.get('following', False),
            can_dm=legacy.get('can_dm', False),
            following_by=legacy.get('following_by', False),
            notifications_enabled=legacy.get('notifications_enabled', False),
            muting=legacy.get('muting', False),
            blocking=legacy.get('blocking', False),
            blocked_by=legacy.get('blocked_by', False),
            want_retweets=legacy.get('want_retweets', False),
            advertiser_account_type=result.get('advertiser_account_type'),
            advertiser_account_service_levels=result.get('advertiser_account_service_levels', []),
            analytics_access_level=result.get('analytics_access_level'),
            is_blue_verified=result.get('is_blue_verified', False),
            has_nft_avatar=result.get('has_nft_avatar', False),
            highlights_info=result.get('highlights_info', {}),
            creator_subscriptions_count=result.get('creator_subscriptions_count')
        )

async def get_profile(username: str, auth: TwitterAuthBase) -> Tuple[bool, Union[Profile, str]]:
    """
    Fetch a Twitter profile by username.
    
    Args:
        username: Twitter username without @ symbol
        auth: TwitterAuth instance for authorization
        
    Returns:
        Tuple of (success, result) where result is either Profile object or error message
    """
    variables = {
        'screen_name': username,
        'withSafetyModeUserFields': True
    }
    
    features = {
        'hidden_profile_likes_enabled': True,
        'hidden_profile_subscriptions_enabled': True,
        'responsive_web_graphql_exclude_directive_enabled': True,
        'verified_phone_label_enabled': False,
        'subscriptions_verification_info_verified_since_enabled': True,
        'highlights_tweets_tab_ui_enabled': True,
        'creator_subscriptions_tweet_preview_api_enabled': True,
        'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
        'responsive_web_graphql_timeline_navigation_enabled': True
    }
    
    field_toggles = {
        'withAuxiliaryUserLabels': False
    }
    
    params = {
        'variables': json.dumps(variables),
        'features': json.dumps(features),
        'fieldToggles': json.dumps(field_toggles)
    }
    
    url = f'https://twitter.com/i/api/graphql/G3KGOASz96M-Qu0nwmGXNg/UserByScreenName?{urlencode(params)}'
    
    async with auth.client.session.get(url) as response:
        if not response.ok:
            return False, f"Failed to fetch profile: {response.status}"
            
        data = await response.json()
        user_data = data.get('data', {}).get('user', {}).get('result', {})
        if not user_data:
            return False, "User not found"
            
        return True, Profile.from_timeline_result(user_data)

async def get_user_id_by_screen_name(screen_name: str, auth: TwitterAuthBase) -> str:
    """
    Get user ID from screen name.
    
    Args:
        screen_name: Twitter screen name
        auth: TwitterAuth instance for authorization
        
    Returns:
        User ID string
    """
    success, result = await get_profile(screen_name, auth)
    if not success:
        raise ValueError(result)
    return result.id

async def get_screen_name_by_user_id(user_id: str, auth: TwitterAuthBase) -> str:
    """
    Get screen name from user ID.
    
    Args:
        user_id: Twitter user ID
        auth: TwitterAuth instance for authorization
        
    Returns:
        Screen name string
    """
    variables = {
        'userId': user_id,
        'withSafetyModeUserFields': True
    }
    
    features = {
        'hidden_profile_likes_enabled': True,
        'hidden_profile_subscriptions_enabled': True,
        'responsive_web_graphql_exclude_directive_enabled': True,
        'verified_phone_label_enabled': False,
        'subscriptions_verification_info_verified_since_enabled': True,
        'highlights_tweets_tab_ui_enabled': True,
        'creator_subscriptions_tweet_preview_api_enabled': True,
        'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
        'responsive_web_graphql_timeline_navigation_enabled': True
    }
    
    field_toggles = {
        'withAuxiliaryUserLabels': False
    }
    
    params = {
        'variables': json.dumps(variables),
        'features': json.dumps(features),
        'fieldToggles': json.dumps(field_toggles)
    }
    
    url = f'https://twitter.com/i/api/graphql/GazOglcBp7_EQTYB7eaqlQ/UserByRestId?{urlencode(params)}'
    
    async with auth.client.session.get(url) as response:
        if not response.ok:
            raise ValueError(f"Failed to fetch user: {response.status}")
            
        data = await response.json()
        user_data = data.get('data', {}).get('user', {}).get('result', {})
        return user_data.get('legacy', {}).get('screen_name', '')