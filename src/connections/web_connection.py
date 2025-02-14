from typing import Any, Dict, List
from langchain_community.document_loaders import WebBaseLoader
from .base_connection import BaseConnection, Action, ActionParameter

class WebConnection(BaseConnection):
    def __init__(self, config):
        super().__init__(config)

    @property
    def is_llm_provider(self):
        return False

    def validate_config(self, config) -> Dict[str, Any]:
        # No specific config needed for web loading
        return config

    def configure(self, **kwargs) -> bool:
        return True

    def is_configured(self, verbose=False) -> bool:
        return True

    def register_actions(self) -> None:
        load_webpage_action = Action(
            name="load-webpage",
            parameters=[
                ActionParameter(
                    name="url",
                    required=True,
                    type=str,
                    description="The URL of the webpage to load"
                )
            ],
            description="Load and extract text content from a webpage"
        )
        self.actions[load_webpage_action.name] = load_webpage_action

    def load_webpage(self, **kwargs) -> Dict[str, Any]:
        try:
            url = kwargs.get('url')
            if not url:
                return {
                    "status": "error",
                    "message": "URL parameter is required"
                }
                
            loader = WebBaseLoader(url)
            docs = loader.load()
            
            return {
                "status": "success",
                "content": [doc.page_content for doc in docs],
                "metadata": [doc.metadata for doc in docs]
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to load webpage: {str(e)}"
            }

    def perform_action(self, action_name: str, params: Dict[str, Any]) -> Any:
        if action_name == "load-webpage":
            return self.load_webpage(**params)
        return super().perform_action(action_name, params) 