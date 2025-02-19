from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from src.connection_manager import ConnectionManager
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
import os
from langchain_core.tools import tool

from src.prompts import PROTOCOL_RESEARCH_AGENT_PROMPT, RISK_ANALYSIS_AGENT_PROMPT, SOCIAL_MEDIA_SENTIMENT_PROMPT, SOCIAL_MEDIA_POST_PROMPT, WALLET_TRANSACTION_PROMPT, CROSS_CHAIN_AGENT_PROMPT, SUPERVISOR_AGENT_PROMPT, SOCIAL_MEDIA_POST_PROMPT


class DeFiProtocolAnalyzer:
    def __init__(
        self,
        model_provider: str,
        model_name: str,
        bind_tools: bool = True,
        connection_manager: ConnectionManager = None,
        debug: bool = False,
    ):
        self.model_provider = model_provider
        self.debug = debug
        self.model_name = model_name
        self._load_environment_variables()
        self.model = ChatOpenAI(model=self.model_name)
        self.bind_tools = bind_tools
        self.connection_manager = connection_manager
        self.checkpointer = MemorySaver()
        self.config = {"configurable": {"thread_id": "test-thread"}}
        self.protocol_research_agent = self._create_protocol_research_agent()
        self.supervisor = self._create_supervisor()
        self.app = self.supervisor.compile()

    @staticmethod            
    @tool
    def analyze_protocol(protocol_name: str):
        """Analyze the protocol"""
        return f"Analyzing {protocol_name}"

    def _create_protocol_research_agent(self):
        """Create a protocol research agent with the 'analyze_protocol' tool."""
        return create_react_agent(
            model=self.model,
            tools=[self.analyze_protocol],
            name="protocol_researcher",
            prompt=PROTOCOL_RESEARCH_AGENT_PROMPT,
            debug=self.debug,
        )

        # Create Risk Analysis Agent
        # risk_expert = create_react_agent(
        #     model=model,
        #     tools=[tool_function],
        #     # tools=,  # Add necessary security/risk tools if available
        #     name="risk_expert",
        #     prompt=RISK_ANALYSIS_AGENT_PROMPT
        # )

        # # Create Social Media Analysis Agent
        # social_media_sentiment_expert = create_react_agent(
        #     model=model,
        #     tools=[tool_function],
        #     # tools=self.twitter_tools,  # Example tool for social media monitoring
        #     name="social_media_sentiment_expert",
        #     prompt=SOCIAL_MEDIA_SENTIMENT_PROMPT
        # )

        # social_media_post_expert = create_react_agent(
        #     model=model,
        #     tools=[tool_function],
        #     # tools=self.twitter_tools,  # Example tool for social media monitoring
        #     name="social_media_post_expert",
        #     prompt=SOCIAL_MEDIA_POST_PROMPT
        # )

        # # Create Wallet Analysis Agent
        # wallet_transaction_expert = create_react_agent(
        #     model=model,
        #     tools=[tool_function],
        #     # tools=self.goat_tools,  # Example wallet analysis tools
        #     name="wallet_transaction_expert",
        #     prompt=WALLET_TRANSACTION_PROMPT
        # )

        # # Create Cross-Chain Operations Agent
        # cross_chain_expert = create_react_agent(
        #     model=model,
        #     tools=[tool_function],
        #     # tools=[debridge_tool],  # Example cross-chain operation tool
        #     name="cross_chain_expert",
        #     prompt=CROSS_CHAIN_AGENT_PROMPT
        # )

        # Create Supervisor Agent to manage and integrate the outputs
    def _create_supervisor(self):
        """Create a supervisor to manage the protocol research agent."""
        return create_supervisor(
            agents=[self.protocol_research_agent],
            model=self.model,
            prompt=SUPERVISOR_AGENT_PROMPT,
            output_mode="last_message",
        )





    def _load_environment_variables(self):
        load_dotenv()
        if self.model_provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
        else:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found in environment variables")

    def invoke_chat(self, messages: list[dict]):
        return self.app.invoke({
            "messages": messages,
        },config=self.config)
    
# chat = DeFiProtocolAnalyzer("openai","gpt-4o-mini",True,None)

# result = chat.invoke_chat([
#     {
#         "role": "user",
#         "content": "Analyze the protocol aave"
#     }])

# print(result)