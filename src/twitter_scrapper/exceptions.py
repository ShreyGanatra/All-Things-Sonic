# twitter_scraper/exceptions.py

class ApiError(Exception):
    def __init__(self, response, data, message):
        super().__init__(message)
        self.response = response
        self.data = data

    @classmethod
    async def from_response(cls, response):
        """Creates an ApiError from a response object."""
        data = None
        try:
            data = await response.json()
            if isinstance(data, dict):
                # Handle standard Twitter API error format
                if 'errors' in data and isinstance(data['errors'], list):
                    error = data['errors'][0]
                    message = error.get('message', 'Unknown Twitter API error')
                    return cls(response, data, message)
                
                # Handle other error formats
                message = data.get('error', f"HTTP {response.status}: {response.reason}")
                return cls(response, data, message)
        except:
            try:
                data = await response.text()
            except:
                pass

        return cls(response, data, f"HTTP {response.status}: {response.reason}")