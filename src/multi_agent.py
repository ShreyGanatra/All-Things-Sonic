from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from src.connection_manager import ConnectionManager
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
import os
from langchain_core.tools import tool
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import MarkdownTextSplitter
import pymupdf4llm
from langchain.tools.retriever import create_retriever_tool
from src.prompts import PROTOCOL_RESEARCH_AGENT_PROMPT, RISK_ANALYSIS_AGENT_PROMPT, SOCIAL_MEDIA_SENTIMENT_PROMPT, SOCIAL_MEDIA_POST_PROMPT, WALLET_TRANSACTION_PROMPT, CROSS_CHAIN_AGENT_PROMPT, SUPERVISOR_AGENT_PROMPT, SOCIAL_MEDIA_POST_PROMPT, SONIC_LITEPAPER_AGENT_PROMPT


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
        # print(self.connection_manager.list_connections())
        self.checkpointer = MemorySaver()
        self.config = {"configurable": {"thread_id": "test-thread"}}
        self.embeddings = OpenAIEmbeddings()
        self.retriever = self._create_retriever()
        self.retriever_tool = create_retriever_tool(
            self.retriever,
            "retrieve_sonic_litepaper_information",
            "Search and return information about Sonic Litepaper",
        )
        self.protocol_research_agent = self._create_protocol_research_agent()
        self.sonic_litepaper_agent = self._create_sonic_litepaper_agent()
        self.social_media_sentiment_expert = self._create_social_media_sentiment_expert()
        self.social_media_post_expert = self._create_social_media_post_expert()
        self.wallet_transaction_expert = self._create_wallet_transaction_expert()
        self.cross_chain_expert = self._create_cross_chain_expert()
        self.supervisor = self._create_supervisor()
        self.app = self.supervisor.compile()
        
    def _create_retriever(self):
        """Create a vector store from a markdown file."""
        md_text = pymupdf4llm.to_markdown(os.getcwd() + "/src/content/Sonic Litepaper.pdf")
        splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = splitter.create_documents([md_text])
        vector_store = Chroma.from_documents(
            documents=split_docs,
            collection_name="sonic_litepaper",
            embedding=self.embeddings,
        )
        return vector_store.as_retriever()    

    def _collect_tools_from_connections(self, connections):
        tools = []
        for connection_name in connections:
            connection = self.connection_manager.get_connection(connection_name)
            if hasattr(connection, "tool_executor") and connection.tool_executor:
                tools.extend(connection.tool_executor.tools)
            else:
                print(f"Connection {connection_name} has no tools.")
        return tools
    
    def _create_protocol_research_agent(self):
        """Create a protocol research agent with the 'analyze_protocol' tool."""
        return create_react_agent(
            model=self.model,
            tools=self._collect_tools_from_connections(["defillama"]),
            name="protocol_researcher",
            prompt=PROTOCOL_RESEARCH_AGENT_PROMPT,
            debug=self.debug,
        )

    def _create_sonic_litepaper_agent(self):
        """Create a sonic litepaper agent with the 'retrieve_sonic_litepaper_information' tool."""
        return create_react_agent(
            model=self.model,
            tools=[self.retriever_tool],
            name="sonic_litepaper_agent",
            prompt=SONIC_LITEPAPER_AGENT_PROMPT,
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

        # Create Social Media Analysis Agent
    def _create_social_media_sentiment_expert(self):
        return create_react_agent(
            model=self.model,
            tools=self._collect_tools_from_connections(["twitter-scrapper"]),  
            name="social_media_sentiment_expert",
            prompt=SOCIAL_MEDIA_SENTIMENT_PROMPT
        )

    def _create_social_media_post_expert(self):
        return create_react_agent(
            model=self.model,
            tools=self._collect_tools_from_connections(["twitter-scrapper"]),
            name="social_media_post_expert",
            prompt=SOCIAL_MEDIA_POST_PROMPT
        )

        # Create Wallet Analysis Agent
    def _create_wallet_transaction_expert(self):
        return create_react_agent(
            model=self.model,
            tools=self._collect_tools_from_connections(["goat"]),
            name="wallet_transaction_expert",
            prompt=WALLET_TRANSACTION_PROMPT
        )

        # Create Cross-Chain Operations Agent
    def _create_cross_chain_expert(self):
        return create_react_agent(
            model=self.model,
            tools=self._collect_tools_from_connections(["debridge"]),
            name="cross_chain_expert",
            prompt=CROSS_CHAIN_AGENT_PROMPT
        )

        # Create Supervisor Agent to manage and integrate the outputs
    def _create_supervisor(self):
        """Create a supervisor to manage the protocol research agent."""
        return create_supervisor(
            agents=[self.protocol_research_agent, self.sonic_litepaper_agent, self.social_media_sentiment_expert, self.social_media_post_expert, self.wallet_transaction_expert, self.cross_chain_expert],
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
    