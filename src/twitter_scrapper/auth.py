# twitter_scraper/auth.py

import aiohttp
from typing import Optional, Dict, Any
from src.twitter_scrapper.exceptions import ApiError
from src.twitter_scrapper.profile import Profile, get_avatar_original_size_url, get_profile, get_screen_name_by_user_id, get_user_id_by_screen_name

import json
import base64
import otpauth
import asyncio
from urllib.parse import urlencode
from aiohttp import FormData
from src.twitter_scrapper.twitter_auth_base import TwitterAuthBase, TwitterAuthOptions


class TwitterUserAuth(TwitterAuthBase):
    """
    Authentication with username and password.
    """
    def __init__(self, bearer_token: str, options: Optional[TwitterAuthOptions] = None):
        super().__init__(bearer_token, options)
        self.user_profile = None

    async def is_logged_in(self) -> bool:
        """Check if user is logged in by verifying credentials"""
        try:
            # First check if we have necessary cookies
            cookies = list(self.cookie_jar)
            auth_token = next((cookie for cookie in cookies if cookie.key == 'auth_token'), None)
            if not auth_token:
                print("No auth_token cookie found")
                return False

            # Then verify with the API
            async with self.session.get(
                'https://api.twitter.com/1.1/account/verify_credentials.json',
                headers=await self._get_auth_headers(),
                ssl=False
            ) as res:
                if not res.ok:
                    print(f"Credentials verification failed with status {res.status}")
                    return False
                    
                verify = await res.json()
                if verify.get('errors'):
                    print(f"Verification returned errors: {verify['errors']}")
                    return False
                    
                # If we have a screen_name in the response, we're logged in
                if verify.get('screen_name'):
                    print(f"Successfully verified login for user {verify['screen_name']}")
                    return True
                    
                return False
        except Exception as e:
            print(f"Error checking login status: {str(e)}")
            # If we have auth_token cookie, consider us logged in even if verification fails
            return bool(auth_token)

    async def _get_auth_headers(self) -> dict:
        """Get headers needed for authenticated requests"""
        headers = {
            'authorization': f'Bearer {self.bearer_token}',
            'content-type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Nokia G20) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.88 Mobile Safari/537.36',
            'x-twitter-auth-type': 'OAuth2Client',
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'en',
        }
        await self.install_to(headers, '')
        return headers

    async def install_csrf_token(self, headers: dict):
        """Install X-CSRF-TOKEN"""
        cookies = list(self.cookie_jar)
        x_csrf_token = next((cookie for cookie in cookies if cookie.key == 'ct0'), None)
        if x_csrf_token:
            headers['x-csrf-token'] = x_csrf_token.value

    async def install_to(self, headers: dict, url: str):
        """Install common headers for authed requests"""
        await super().install_to(headers, url)
        await self.install_csrf_token(headers)

    async def login(self, username, password, email=None, two_factor_secret=None):
        """Login to twitter"""
        print("Starting login process")
        await self.update_guest_token() #must have for the flow
        print("Guest token updated")

        next_flow = await self.init_login()
        print("Login initialized")
        
        while 'subtask' in next_flow and next_flow['subtask']:
            subtask_id = next_flow['subtask']['subtask_id']
            print(f"Processing subtask: {subtask_id}")
            
            if subtask_id == 'LoginJsInstrumentationSubtask':
                next_flow = await self.handle_js_instrumentation_subtask(next_flow)
            elif subtask_id == 'LoginEnterUserIdentifierSSO':
                next_flow = await self.handle_enter_user_identifier_sso(next_flow, username)
            elif subtask_id == 'LoginEnterAlternateIdentifierSubtask':
                next_flow = await self.handle_enter_alternate_identifier_subtask(next_flow, email)
            elif subtask_id == 'LoginEnterPassword':
                next_flow = await self.handle_enter_password(next_flow, password)
            elif subtask_id == 'AccountDuplicationCheck':
                next_flow = await self.handle_account_duplication_check(next_flow)
            elif subtask_id == 'LoginTwoFactorAuthChallenge':
                next_flow = await self.handle_two_factor_auth_challenge(next_flow, two_factor_secret)
            elif subtask_id == 'LoginAcid':
                next_flow = await self.handle_acid(next_flow, email)
            elif subtask_id == 'LoginSuccessSubtask':
                next_flow = await self.handle_success_subtask(next_flow)
            else:
                raise ValueError(f"Unknown subtask {subtask_id}")
        
        if 'err' in next_flow:
            raise next_flow['err']
        
        print("Login process completed successfully")

    async def init_login(self):
        """Initialize login flow"""

        self.clear_cookies()
        return await self.execute_flow_task({
            "flow_name": "login",
            "input_flow_data": {
              "flow_context": {
                "debug_overrides": {},
                "start_location": {
                  "location": "splash_screen"
                }
              }
            }
          })

    async def handle_js_instrumentation_subtask(self,prev):
        """Handle LoginJsInstrumentationSubtask"""

        return await self.execute_flow_task({
            "flow_token": prev["flowToken"],
            "subtask_inputs": [
              {
                "subtask_id": "LoginJsInstrumentationSubtask",
                "js_instrumentation": {
                  "response": "{}",
                  "link": "next_link"
                }
              }
            ]
          })
    async def handle_enter_alternate_identifier_subtask(self, prev, email):
        """Handle LoginEnterAlternateIdentifierSubtask"""
        return await self.execute_flow_task({
            "flow_token": prev["flowToken"],
            "subtask_inputs": [
              {
                "subtask_id": "LoginEnterAlternateIdentifierSubtask",
                "enter_text": {
                  "text": email,
                  "link": "next_link"
                }
              }
            ]
          })

    async def handle_enter_user_identifier_sso(self, prev, username):
        """Handle LoginEnterUserIdentifierSSO"""
        return await self.execute_flow_task({
            "flow_token": prev["flowToken"],
            "subtask_inputs": [
              {
                "subtask_id": "LoginEnterUserIdentifierSSO",
                "settings_list": {
                  "setting_responses": [
                    {
                      "key": "user_identifier",
                      "response_data": {
                        "text_data": {
                          "result": username
                        }
                      }
                    }
                  ],
                  "link": "next_link"
                }
              }
            ]
          })
    async def handle_enter_password(self, prev, password):
        """Handle LoginEnterPassword"""
        return await self.execute_flow_task({
            "flow_token": prev["flowToken"],
            "subtask_inputs": [
              {
                "subtask_id": "LoginEnterPassword",
                "enter_password": {
                  "password": password,
                  "link": "next_link"
                }
              }
            ]
          })

    async def handle_account_duplication_check(self,prev):
        """Handle AccountDuplicationCheck"""
        return await self.execute_flow_task({
            "flow_token": prev["flowToken"],
            "subtask_inputs": [
              {
                "subtask_id": "AccountDuplicationCheck",
                "check_logged_in_account": {
                  "link": "AccountDuplicationCheck_false"
                }
              }
            ]
          })

    async def handle_two_factor_auth_challenge(self,prev,secret):
        """Handle LoginTwoFactorAuthChallenge"""
        totp = otpauth.TOTP(secret)
        error = None

        for attempts in range(1, 4):
          try:
            return await self.execute_flow_task({
              "flow_token": prev["flowToken"],
              "subtask_inputs": [
                {
                  "subtask_id": "LoginTwoFactorAuthChallenge",
                  "enter_text": {
                    "link": "next_link",
                    "text": totp.generate()
                  }
                }
              ]
            })
          except Exception as err:
            error = err
            await asyncio.sleep(2 * attempts) #async sleep

        raise error #re-raise error after attempts

    async def handle_acid(self,prev,email):
        """Handle LoginAcid"""

        return await self.execute_flow_task({
            "flow_token": prev["flowToken"],
            "subtask_inputs": [
              {
                "subtask_id": "LoginAcid",
                "enter_text": {
                  "text": email,
                  "link": "next_link"
                }
              }
            ]
          })

    async def handle_success_subtask(self,prev):
        """Handle LoginSuccessSubtask"""
        return await self.execute_flow_task({
            "flow_token": prev["flowToken"],
            "subtask_inputs": []
          })

    async def execute_flow_task(self, data: dict) -> dict:
        """Execute onboarding task"""

        onboarding_task_url = 'https://api.twitter.com/1.1/onboarding/task.json'
        token = self.guest_token
        if token is None:
          raise ValueError('Authentication token is null or undefined.')

        headers = {
            'authorization': f'Bearer {self.bearer_token}',
            'cookie': await self.get_cookies_string(),
            'content-type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Nokia G20) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.88 Mobile Safari/537.36',
            'x-guest-token': token,
            'x-twitter-auth-type': 'OAuth2Client',
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'en',
        }

        await self.install_csrf_token(headers)

        async with self.session.post(onboarding_task_url, headers=headers, json=data, ssl=False) as res:
            if not res.ok:
                error = await ApiError.from_response(res)
                raise error

            # Update cookies from response
            if res.cookies:
                self.cookie_jar.update_cookies(res.cookies)

            flow = await res.json()
            if flow.get('flow_token') is None:
                raise ValueError('flow_token not found.')
            
            if flow.get('errors'):
                raise ValueError(f"Authentication error ({flow['errors'][0]['code']}): {flow['errors'][0]['message']}")

            subtask = flow.get('subtasks')[0] if flow.get('subtasks') else None
            if subtask and subtask['subtask_id'] == 'DenyLoginSubtask':
                raise ValueError('Authentication error: DenyLoginSubtask')

            return {
                "subtask": subtask,
                "flowToken": flow['flow_token']
            }

    def clear_cookies(self):
        """Clear session"""
        self.cookie_jar.clear()

    async def logout(self):
      """Logout to twitter"""
      #TODO: implement logout
      pass

    async def get_cookies_string(self) -> str:
        cookie_strings = []
        for cookie in self.cookie_jar:
            # For aiohttp's Morsel objects, just use key and value
            cookie_strings.append(f"{cookie.key}={cookie.value}")
        return "; ".join(cookie_strings)