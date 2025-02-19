import  aiohttp.cookiejar
from typing import Optional
import aiohttp
import asyncio

class TwitterAuthOptions:
    def __init__(self, fetch=None, transform=None):
        self.fetch = fetch  # async function, default aiohttp.ClientSession().get/post
        self.transform = transform  # transform method for requests/responses

class TwitterAuthBase:
    def __init__(self, bearer_token: str, options: Optional[TwitterAuthOptions] = None):
        self.bearer_token = bearer_token
        self.options = options or TwitterAuthOptions()
        print("Initializing TwitterAuthBase")
        self.session = aiohttp.ClientSession()
        print("Session initialized")
        self.cookie_jar = aiohttp.cookiejar.CookieJar()
        print("Cookie jar initialized")
        self.guest_token = None
        print("Guest token initialized")

    async def install_to(self, headers: dict, url: str):
        """Install auth headers."""
        cookies_str = await self.get_cookie_string()
        if cookies_str:
            headers['cookie'] = cookies_str

    async def get_cookie_string(self) -> str:
        """Return cookies as a string."""
        return '; '.join([f"{cookie.key}={cookie.value}" for cookie in self.cookie_jar])

    async def close(self):
        """Close the aiohttp client session"""
        if not self.session.closed:
            await self.session.close()

    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return False

    def clear_cookies(self):
        """Clear all cookies"""
        self.cookie_jar.clear() 

    async def update_guest_token(self):
        guest_activate_url = 'https://api.twitter.com/1.1/guest/activate.json'

        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Cookie': await self.get_cookie_string(),
        }

        async with self.session.post(guest_activate_url, headers=headers, ssl=False) as res:
            if not res.ok:
                raise ValueError(f"Failed to activate guest token: {res.status}")
            o = await res.json()

            # Update cookies from response
            if res.cookies:
                self.cookie_jar.update_cookies(res.cookies)

        if o is None or 'guest_token' not in o:
            raise ValueError('guest_token not found.')

        new_guest_token = o['guest_token']
        if not isinstance(new_guest_token, str):
            raise TypeError('guest_token was not a string.')

        self.guest_token = new_guest_token
        self.guest_created_at = asyncio.get_event_loop().time()
