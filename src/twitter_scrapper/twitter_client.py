import asyncio
import aiohttp
from typing import Optional
from urllib.parse import urlparse

class TwitterClient:
    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.guest_token: Optional[str] = None
        self.guest_created_at: Optional[float] = None
        self.cookie_jar = aiohttp.CookieJar()
        # Configure the session to handle compression
        self.session = aiohttp.ClientSession(
            cookie_jar=self.cookie_jar,
            trust_env=True,
            headers={
                'Accept-Encoding': 'gzip, deflate',  # Remove br from accepted encodings
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Nokia G20) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.88 Mobile Safari/537.36'
            }
        )

    async def close(self):
        await self.session.close()

    def get_guest_created_at(self):
        return self.guest_created_at

    async def install_to(self, headers: dict):
        if self.should_update():
            await self.update_guest_token()

        token = self.guest_token
        if token is None:
            raise ValueError('Authentication token is null or undefined.')

        headers['authorization'] = f'Bearer {self.bearer_token}'
        headers['x-guest-token'] = token
        headers['Accept-Encoding'] = 'gzip, deflate'  # Remove br from accepted encodings

        cookies_string = await self.get_cookie_string()
        headers['cookie'] = cookies_string

        # Find ct0 cookie using key instead of name
        ct0_cookie = next((cookie for cookie in self.cookie_jar if cookie.key == 'ct0'), None)
        if ct0_cookie:
            headers['x-csrf-token'] = ct0_cookie.value

    async def get_cookies(self):
        url = self.get_cookie_jar_url()
        return list(self.cookie_jar)

    async def get_cookie_string(self) -> str:
        cookie_strings = []
        for cookie in self.cookie_jar:
            # For aiohttp's Morsel objects, just use key and value
            cookie_strings.append(f"{cookie.key}={cookie.value}")
        return "; ".join(cookie_strings)

    async def remove_cookie(self, key: str):
        # aiohttp.CookieJar doesn't have clear method with domain, path, key
        # so we need to iterate and delete
        for cookie in list(self.cookie_jar):
            if cookie.key == key:
                self.cookie_jar.discard(cookie)

    def get_cookie_jar_url(self) -> str:
        return 'https://twitter.com'

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

    def should_update(self) -> bool:
        return (
            self.guest_token is None or
            (self.guest_created_at is not None and
             asyncio.get_event_loop().time() - self.guest_created_at > 3 * 60 * 60)
        )

    def has_token(self) -> bool:
        return self.guest_token is not None 