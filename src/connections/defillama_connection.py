import os
import logging
import requests
from typing import Dict, Any, List
from src.connections.base_connection import BaseConnection, Action, ActionParameter

logger = logging.getLogger("connections.defillama_connection")

class DefiLlamaConnectionError(Exception):
    """Base exception for DefiLlama connection errors"""
    pass

class DefiLlamaAPIError(DefiLlamaConnectionError):
    """Raised when DefiLlama API requests fail"""
    pass

class DefiLlamaConnection(BaseConnection):

    def __init__(self, config: Dict[str, Any]):
        logger.info("🔗 Initializing DefiLlama connection...")
        super().__init__(config)
        self.api_url = os.getenv("DEFILLAMA_API_URL", "https://api.llama.fi")
        self._session = requests.Session()

    def register_actions(self) -> None:
        """Register available DefiLlama actions"""
        self.actions = {
            # TVL Related Actions
            # "get_all_protocols": Action(
            #     name="get_all_protocols",
            #     parameters=[],
            #     description="List all protocols on defillama along with their TVL"
            # ),
            "get_protocol_info": Action(
                name="get_protocol_info",
                parameters=[
                    ActionParameter("protocol", True, str, "Protocol slug (e.g. 'aave')")
                ],
                description="Get historical TVL of a protocol and breakdowns by token and chain"
            ),
            # "get_protocol_tvl": Action(
            #     name="get_protocol_tvl",
            #     parameters=[
            #         ActionParameter("protocol", True, str, "Protocol slug (e.g. 'aave')")
            #     ],
            #     description="Simplified endpoint to get current TVL of a protocol"
            # ),
            # "get_historical_tvl": Action(
            #     name="get_historical_tvl",
            #     parameters=[],
            #     description="Get historical TVL (excludes liquid staking and double counted TVL) of DeFi on all chains"
            # ),
            # "get_chain_historical_tvl": Action(
            #     name="get_chain_historical_tvl",
            #     parameters=[
            #         ActionParameter("chain", True, str, "Chain slug (e.g. 'Ethereum')")
            #     ],
            #     description="Get historical TVL of a specific chain"
            # ),
            # "get_current_chains_tvl": Action(
            #     name="get_current_chains_tvl",
            #     parameters=[],
            #     description="Get current TVL of all chains"
            # ),

            # # Coins/Price Related Actions
            # "get_current_prices": Action(
            #     name="get_current_prices",
            #     parameters=[
            #         ActionParameter("coins", True, str, "Comma-separated tokens as chain:address (e.g. 'ethereum:0x...,bsc:0x...')")
            #     ],
            #     description="Get current prices of tokens by contract address"
            # ),
            # "get_historical_prices": Action(
            #     name="get_historical_prices",
            #     parameters=[
            #         ActionParameter("coins", True, str, "Comma-separated tokens as chain:address"),
            #         ActionParameter("timestamp", True, int, "UNIX timestamp for historical prices"),
            #         ActionParameter("search_width", False, str, "Time range to search around timestamp (e.g. '4h')")
            #     ],
            #     description="Get historical prices of tokens at a specific timestamp"
            # ),
            # "get_price_chart": Action(
            #     name="get_price_chart",
            #     parameters=[
            #         ActionParameter("coins", True, str, "Comma-separated tokens as chain:address"),
            #         ActionParameter("start", False, int, "Start timestamp"),
            #         ActionParameter("end", False, int, "End timestamp"),
            #         ActionParameter("span", False, int, "Number of data points"),
            #         ActionParameter("period", False, str, "Duration between data points (e.g. '1d')")
            #     ],
            #     description="Get token prices at regular time intervals"
            # ),
            # "get_price_percentage_change": Action(
            #     name="get_price_percentage_change",
            #     parameters=[
            #         ActionParameter("coins", True, str, "Comma-separated tokens as chain:address"),
            #         ActionParameter("timestamp", False, int, "Reference timestamp"),
            #         ActionParameter("look_forward", False, bool, "Whether to look forward from timestamp"),
            #         ActionParameter("period", False, str, "Duration for percentage calculation (e.g. '24h')")
            #     ],
            #     description="Get percentage change in price over time"
            # ),

            # # Stablecoin Related Actions
            # "get_stablecoins": Action(
            #     name="get_stablecoins",
            #     parameters=[
            #         ActionParameter("include_prices", False, bool, "Whether to include current prices")
            #     ],
            #     description="List all stablecoins along with their circulating amounts"
            # ),
            # "get_stablecoin_charts": Action(
            #     name="get_stablecoin_charts",
            #     parameters=[
            #         ActionParameter("stablecoin", True, int, "Stablecoin ID from /stablecoins endpoint")
            #     ],
            #     description="Get historical mcap and chain distribution of a stablecoin"
            # ),
            # "get_stablecoin_chains": Action(
            #     name="get_stablecoin_chains",
            #     parameters=[],
            #     description="Get current mcap sum of all stablecoins on each chain"
            # ),
            # "get_stablecoin_prices": Action(
            #     name="get_stablecoin_prices",
            #     parameters=[],
            #     description="Get historical prices of all stablecoins"
            # ),

            # # Yield Related Actions
            # "get_pools": Action(
            #     name="get_pools",
            #     parameters=[],
            #     description="Retrieve latest data for all pools, including enriched information such as predictions"
            # ),
            # "get_pool_chart": Action(
            #     name="get_pool_chart",
            #     parameters=[
            #         ActionParameter("pool", True, str, "Pool ID (UUID)")
            #     ],
            #     description="Get historical APY and TVL of a specific pool"
            # ),

            # # Volume Related Actions
            # "get_dexs_overview": Action(
            #     name="get_dexs_overview",
            #     parameters=[
            #         ActionParameter("exclude_total_data_chart", False, bool, "Exclude aggregated chart"),
            #         ActionParameter("data_type", False, str, "Data type (dailyVolume/totalVolume)")
            #     ],
            #     description="List all DEXs with volume summaries and historical data"
            # ),
            # "get_dex_summary": Action(
            #     name="get_dex_summary",
            #     parameters=[
            #         ActionParameter("protocol", True, str, "Protocol slug"),
            #         ActionParameter("data_type", False, str, "Data type (dailyVolume/totalVolume)")
            #     ],
            #     description="Get summary of DEX volume with historical data"
            # ),

            # # Fees and Revenue Actions
            # "get_fees_overview": Action(
            #     name="get_fees_overview",
            #     parameters=[
            #         ActionParameter("data_type", False, str, "Data type (totalFees/dailyFees/totalRevenue/dailyRevenue)")
            #     ],
            #     description="List all protocols with fees and revenue summaries"
            # ),
            # "get_protocol_fees": Action(
            #     name="get_protocol_fees",
            #     parameters=[
            #         ActionParameter("protocol", True, str, "Protocol slug"),
            #         ActionParameter("data_type", False, str, "Data type (totalFees/dailyFees/totalRevenue/dailyRevenue)")
            #     ],
            #     description="Get summary of protocol fees and revenue with historical data"
            # )
        }

    @property
    def is_llm_provider(self) -> bool:
        return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate DefiLlama configuration"""
        if "api_url" not in config:
            config["api_url"] = os.getenv("DEFILLAMA_API_URL", "https://api.llama.fi")
        return config

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.api_url}{endpoint}"
        headers = {"accept": "application/json"}
        kwargs['headers'] = headers

        logger.debug(f"Making {method.upper()} request to {url}")
        logger.debug(f"Request params: {kwargs}")
        
        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response text: {response.text}")

            try:
                data = response.json()
            except ValueError:
                raise DefiLlamaAPIError(f"Invalid response format: {response.text}")

            if not response.ok:
                error_msg = data.get('error', 'Unknown error occurred')
                logger.error(f"API error: {error_msg}")
                raise DefiLlamaAPIError(f"API error: {error_msg}")

            logger.debug(f"Request successful: {response.status_code}")
            return data

        except requests.Timeout:
            raise DefiLlamaAPIError("Request timed out")
            
        except requests.ConnectionError as e:
            raise DefiLlamaAPIError(f"Connection error: {str(e)}")
            
        except requests.RequestException as e:
            raise DefiLlamaAPIError(str(e))

    def is_configured(self, verbose: bool = False) -> bool:
        """Check if DefiLlama connection is configured"""
        try:
            # Test API connection by getting chains list
            response = self._make_request("GET", "/chains")
            if verbose:
                logger.info("DefiLlama connection is configured and working")
            return True
        except Exception as e:
            if verbose:
                logger.error(f"DefiLlama connection is not configured or not working: {str(e)}")
            return False

    def configure(self) -> bool:
        """Configure the DefiLlama connection"""
        try:
            # Test API connection
            response = self._make_request("GET", "/chains")
            logger.info("DefiLlama API connection successful")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to DefiLlama API: {str(e)}")
            return False

    def perform_action(self, action_name: str, kwargs: Dict[str, Any]) -> Any:
        """Execute a DefiLlama action with validation"""
        if not self.is_configured():
            raise DefiLlamaConnectionError("DefiLlama connection is not configured")

        if action_name not in self.actions:
            raise DefiLlamaConnectionError(f"Unknown action: {action_name}")

        method_name = action_name
        method = getattr(self, method_name)
        
        return method(**kwargs)

    def _filter_protocol_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter protocol info response to include only essential information"""
        essential_keys = {
            "id",
            "name",
            "description",
            "url",
            "logo",
            "gecko_id",
            "symbol",
            "twitter",
            "chains",
            "mcap"
        }
        filtered_data = {k: v for k, v in data.items() if k in essential_keys}
        filtered_data["SonicTVL"] = data["currentChainTvls"]["Sonic"]
        return filtered_data

    def get_protocol_info(self, protocol: str) -> Dict[str, Any]:
        """Get filtered information about a DeFi protocol"""
        print(f"Getting protocol info for {protocol}")
        data = self._make_request("GET", f"/protocol/{protocol}")
        return self._filter_protocol_info(data)

    # def get_protocol_tvl(self, protocol: str, timestamp: int = None) -> Dict[str, Any]:
    #     """Get TVL for a specific protocol"""
    #     endpoint = f"/tvl/{protocol}"
    #     if timestamp:
    #         endpoint += f"/{timestamp}"
    #     return self._make_request("GET", endpoint)

    # def get_chains(self) -> List[str]:
    #     """Get list of all chains tracked by DefiLlama"""
    #     return self._make_request("GET", "/chains")

    def get_chain_tvl(self, chain: str) -> Dict[str, Any]:
        """Get TVL for a specific chain"""
        return self._make_request("GET", f"/v2/chains/{chain}")

    # def search_protocols(self, keyword: str) -> List[Dict[str, Any]]:
    #     """Search for protocols by name or keyword"""
    #     protocols = self._make_request("GET", "/protocols")
    #     keyword = keyword.lower()
    #     return [
    #         protocol for protocol in protocols
    #         if keyword in protocol.get("name", "").lower() or
    #         keyword in protocol.get("slug", "").lower()
    #     ]

    # def get_all_protocols(self) -> List[Dict[str, Any]]:
    #     """Get list of all protocols"""
    #     return self._make_request("GET", "/protocols")

    # def get_token_info(self, token_id: str) -> Dict[str, Any]:
    #     """Get detailed information about a token"""
    #     return self._make_request("GET", f"/token/{token_id}")

    # def get_token_prices(self, timestamp: int = None, search_width: str = None) -> Dict[str, Any]:
    #     """Get token prices"""
    #     params = {}
    #     if timestamp:
    #         params["timestamp"] = timestamp
    #     if search_width:
    #         params["searchWidth"] = search_width
    #     return self._make_request("GET", "/prices/current", params=params)

    # def get_pools(self, protocol: str = None, chain: str = None) -> List[Dict[str, Any]]:
    #     """Get yield pools information"""
    #     params = {}
    #     if protocol:
    #         params["protocol"] = protocol
    #     if chain:
    #         params["chain"] = chain
    #     return self._make_request("GET", "/pools", params=params)

    # def get_stablecoins(self) -> Dict[str, Any]:
    #     """Get stablecoins information"""
    #     return self._make_request("GET", "/stablecoins")

    # def get_stablecoin_charts(self, stablecoin: int) -> Dict[str, Any]:
    #     """Get historical data for a stablecoin"""
    #     return self._make_request("GET", f"/stablecoin/{stablecoin}")

    # def get_bridges(self) -> List[Dict[str, Any]]:
    #     """Get list of all bridges"""
    #     return self._make_request("GET", "/bridges")

    # def get_bridge_stats(self, bridge: str) -> Dict[str, Any]:
    #     """Get bridge statistics"""
    #     return self._make_request("GET", f"/bridge/{bridge}")

    # def get_protocol_treasury(self, protocol: str) -> Dict[str, Any]:
    #     """Get protocol treasury data"""
    #     return self._make_request("GET", f"/treasury/{protocol}")

    # def get_dexes_volume(self, protocol: str = None, chain: str = None) -> Dict[str, Any]:
    #     """Get DEX volume data"""
    #     params = {}
    #     if protocol:
    #         params["protocol"] = protocol
    #     if chain:
    #         params["chain"] = chain
    #     return self._make_request("GET", "/dexs/volume", params=params)

    # def get_historical_tvl(self) -> Dict[str, Any]:
    #     """Get historical TVL of DeFi on all chains"""
    #     return self._make_request("GET", "/v2/historicalChainTvl")

    def get_chain_historical_tvl(self, chain: str) -> Dict[str, Any]:
        """Get historical TVL of a specific chain"""
        return self._make_request("GET", f"/v2/historicalChainTvl/{chain}")

    def get_current_chains_tvl(self) -> Dict[str, Any]:
        """Get current TVL of all chains"""
        return self._make_request("GET", "/v2/chains")

    # def get_current_prices(self, coins: str, search_width: str = None) -> Dict[str, Any]:
    #     """Get current prices of tokens"""
    #     params = {}
    #     if search_width:
    #         params["searchWidth"] = search_width
    #     return self._make_request("GET", f"/prices/current/{coins}", params=params)

    # def get_historical_prices(self, coins: str, timestamp: int, search_width: str = None) -> Dict[str, Any]:
    #     """Get historical prices of tokens"""
    #     params = {}
    #     if search_width:
    #         params["searchWidth"] = search_width
    #     return self._make_request("GET", f"/prices/historical/{timestamp}/{coins}", params=params)

    # def get_price_chart(self, coins: str, start: int = None, end: int = None, 
    #                    span: int = None, period: str = None, search_width: str = None) -> Dict[str, Any]:
    #     """Get token prices at regular intervals"""
    #     params = {}
    #     if start:
    #         params["start"] = start
    #     if end:
    #         params["end"] = end
    #     if span:
    #         params["span"] = span
    #     if period:
    #         params["period"] = period
    #     if search_width:
    #         params["searchWidth"] = search_width
    #     return self._make_request("GET", f"/chart/{coins}", params=params)

    # def get_price_percentage_change(self, coins: str, timestamp: int = None, 
    #                               look_forward: bool = False, period: str = None) -> Dict[str, Any]:
    #     """Get percentage change in token prices"""
    #     params = {}
    #     if timestamp:
    #         params["timestamp"] = timestamp
    #     if look_forward:
    #         params["lookForward"] = look_forward
    #     if period:
    #         params["period"] = period
    #     return self._make_request("GET", f"/percentage/{coins}", params=params)

    # def get_stablecoin_chains(self) -> Dict[str, Any]:
    #     """Get stablecoin data by chain"""
    #     return self._make_request("GET", "/stablecoinchains")

    # def get_stablecoin_prices(self) -> Dict[str, Any]:
    #     """Get historical stablecoin prices"""
    #     return self._make_request("GET", "/stablecoinprices")

    # def get_pool_chart(self, pool: str) -> Dict[str, Any]:
    #     """Get historical pool data"""
    #     return self._make_request("GET", f"/chart/{pool}")

    # def get_dexs_overview(self, exclude_total_data_chart: bool = None, 
    #                      data_type: str = None) -> Dict[str, Any]:
    #     """Get DEX overview data"""
    #     params = {}
    #     if exclude_total_data_chart:
    #         params["excludeTotalDataChart"] = exclude_total_data_chart
    #     if data_type:
    #         params["dataType"] = data_type
    #     return self._make_request("GET", "/overview/dexs", params=params)

    # def get_dex_summary(self, protocol: str, data_type: str = None) -> Dict[str, Any]:
    #     """Get DEX summary data"""
    #     params = {}
    #     if data_type:
    #         params["dataType"] = data_type
    #     return self._make_request("GET", f"/summary/dexs/{protocol}", params=params)

    # def get_fees_overview(self, data_type: str = None) -> Dict[str, Any]:
    #     """Get fees overview data"""
    #     params = {}
    #     if data_type:
    #         params["dataType"] = data_type
    #     return self._make_request("GET", "/overview/fees", params=params)

    # def get_protocol_fees(self, protocol: str, data_type: str = None) -> Dict[str, Any]:
    #     """Get protocol fees data"""
    #     params = {}
    #     if data_type:
    #         params["dataType"] = data_type
    #     return self._make_request("GET", f"/summary/fees/{protocol}", params=params) 