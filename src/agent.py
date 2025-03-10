import datetime, random, time, logging, json
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from src.helpers import print_h_bar
from src.langgraph_agent.langgraph_agent import LangGraphAgent
from src.connection_manager import ConnectionManager
from src.langgraph_agent.prompts import DETERMINATION_PROMPT, DIVISION_PROMPT, EXECUTION_PROMPT, EVALUATION_PROMPT, OBSERVATION_PROMPT
from src.prompts import SOCIAL_MEDIA_LOOP_PROMPT
from dotenv import load_dotenv
import os
import requests
from langchain_openai import ChatOpenAI
# Initialize logger
logger = logging.getLogger("agent")


COINGECKO_API_URL = "https://api.coingecko.com/api/v3"


def _make_request_coingecko(endpoint: str) -> dict:
    url = f"{COINGECKO_API_URL}{endpoint}"
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": os.getenv("COINGECKO_API_KEY")
    }
    response = requests.get(url, headers=headers)
    return response.json()


def get_coin_historical_chart(coin_id: str) -> dict:
    endpoint = f"/coins/{coin_id}/market_chart?vs_currency=usd&days=7&interval=daily&precision=3"
    return _make_request_coingecko(endpoint)

def get_coin_price(coin_id: str) -> dict:
    endpoint = f"/simple/price?ids={coin_id}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true&include_last_updated_at=true&precision=3"
    return _make_request_coingecko(endpoint)


class AgentState(TypedDict):
    context: dict
    context_summary: str
    current_task: str | None
    action_plan: list
    action_log: list
    task_log: list

class ZerePyAgent:
    def __init__(self, agent_config: dict):
        try:
            # Load agent configuration
            self._setup_agent_config(agent_config)
            self._load_environment_variables()
            self.posts = []
            self.agent = ChatOpenAI(
                    model=self.model,
                    api_key=self.api_key,
                    temperature=1,
                )

        except Exception as e:
            logger.error("Could not load ZerePy Agent")
            raise e

    def perform_action(self, connection: str, action: str, **kwargs) -> None:
        """Delegate action execution to the connection manager"""
        return self.connection_manager.perform_action(connection, action, **kwargs)

    def _load_environment_variables(self):
        load_dotenv()
        if self.model_provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
        else:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found in environment variables")

    def _setup_agent_config(self, agent_config: dict):
        try:
            # GENERAL CONFIG
            general_config = agent_config["config"]
            self.name = general_config["name"]
            self.loop_delay = general_config["loop_delay"]
            self.time_based_multipliers = general_config.get("time_based_multipliers", None)

            # CONNECTIONS
            connections_config = agent_config["connections"]
            self.connection_manager = ConnectionManager(connections_config)
            self.connection_manager.list_connections()
            self.connections = self.connection_manager.get_connections()

            # LLM CONFIG
            llm_config = agent_config["llms"]

            # CHARACTER LLM
            character_config = llm_config["character"]
            self.character_name = character_config["name"]
            self.bio = character_config.get("bio", [])
            self.traits = character_config.get("traits", [])
            self.examples = character_config.get("examples", [])
            self.example_accounts = character_config.get("example_accounts", [])
            self.model_provider = character_config["model_provider"]
            self.model = character_config["model"]
            # TASK CONFIGS
            self.tasks = agent_config.get("tasks", [])
            self.task_weights = [task.get("weight", 0) for task in self.tasks]

        except KeyError as e:
            raise KeyError(f"Missing required field in agent configuration: {e}")
        except Exception as e:
            raise Exception(f"Error setting up agent configs: {e}")

     
    def get_protocol_info(self):
        context = {}
        protocols = ["silo finance","beets", "avalon labs", "aave V3", "shadow exchange", "euler V2", "swapX"]
        for protocol in protocols:
            context[f"{protocol}_protocol_info"] = self.perform_action(
                                connection="defillama",
                                action="get_protocol_info",
                                params=[protocol]
                            )
        return context
        

    def get_sonic_details(self):
        context = {}
        context["sonic_current_price"] = get_coin_price("sonic-3")
        context["sonic_historical_data"] = get_coin_historical_chart("sonic-3")
        return context

    def create_context(self, sonic_details, protocol_info):
        """Create a context (string) for the agent"""
        context = f'''
        Current Price of SONIC $S:
        {sonic_details["sonic_current_price"]}

        Historical Data of SONIC $S:
        {sonic_details["sonic_historical_data"]}

        Silo Finance Protocol Info: 
        {protocol_info["silo finance_protocol_info"]}

        Beets Protocol Info:
        {protocol_info["beets_protocol_info"]}

        Avalon Labs Protocol Info:
        {protocol_info["avalon labs_protocol_info"]}

        Aave V3 Protocol Info:
        {protocol_info["aave V3_protocol_info"]}

        Shadow Exchange Protocol Info:
        {protocol_info["shadow exchange_protocol_info"]}

        Euler V2 Protocol Info:
        {protocol_info["euler V2_protocol_info"]}
        
        SwapX Protocol Info:
        {protocol_info["swapX_protocol_info"]}


        Recent Posts:
        {self.posts[-5:]}
        '''
        return context


    def loop(self, task=None):
        logger.info(f"\n🚀 Starting autonomous agent loop ...")
        logger.info("Press Ctrl+C at any time to stop the loop.")
        print_h_bar()
        time.sleep(2)
        # logger.info("Starting loop in 5 seconds...")
        # for i in range(5, 0, -1):
        #     logger.info(f"{i}...")
        #     time.sleep(1)

        try:
            while True:
                try:
                    sonic_details = self.get_sonic_details() 
                    protocol_info = self.get_protocol_info()
                    self.context = self.create_context(sonic_details, protocol_info)
                    messages = [{"role": "system", "content": SOCIAL_MEDIA_LOOP_PROMPT},{"role": "user", "content": self.context}]
                    response = self.agent.invoke(messages)

                    tweet = response.content
                    print(tweet)
                    self.connections["twitter-scrapper"].send_tweet(tweet)
                    self.posts.append(tweet)
                    self.posts = self.posts[-5:]

                    logger.info(f"\n⏳ Waiting {self.loop_delay} seconds before next loop...")
                    print_h_bar()
                    time.sleep(self.loop_delay)
                except Exception as e:
                    logger.error(f"\n❌ Error in agent loop iteration: {e}")
                    logger.info(f"⏳ Waiting {self.loop_delay} seconds before retrying...")
                    time.sleep(self.loop_delay)
        except KeyboardInterrupt:
            logger.info("\n🛑 Agent loop stopped by user.")
            return
            