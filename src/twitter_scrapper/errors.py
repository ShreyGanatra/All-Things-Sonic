from typing import Optional, Dict, Any
from aiohttp import ClientResponse

class ApiError(Exception):
    """
    Represents an error returned by the Twitter API.
    """
    def __init__(self, message: str, code: Optional[int] = None, data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.data = data or {}

    @classmethod
    async def from_response(cls, response: ClientResponse) -> 'ApiError':
        """
        Create an ApiError from an HTTP response.
        
        Args:
            response: The HTTP response that caused the error
            
        Returns:
            An ApiError instance with details from the response
        """
        try:
            data = await response.json()
            if isinstance(data, dict):
                # Handle standard Twitter API error format
                if 'errors' in data and isinstance(data['errors'], list):
                    error = data['errors'][0]
                    message = error.get('message', 'Unknown Twitter API error')
                    code = error.get('code')
                    return cls(message, code, data)
                
                # Handle other error formats
                message = data.get('error', 'Unknown Twitter API error')
                code = data.get('status')
                return cls(message, code, data)
                
        except Exception:
            pass
            
        # Fallback for non-JSON responses
        return cls(
            f"HTTP {response.status}: {response.reason}",
            response.status,
            {'status': response.status, 'reason': response.reason}
        ) 