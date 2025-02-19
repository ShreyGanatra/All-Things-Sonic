import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import ToolExecutor, create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import json
from src.connection_manager import ConnectionManager


class LangGraphAgent:
    def __init__(self, model_provider: str, model: str, bind_tools: bool, connection_manager: ConnectionManager=None, prompt:str=None,debug:bool=False):
        self.model_provider = model_provider
        self.model = model
        self.bind_tools = bind_tools
        self.connection_manager = connection_manager
        self._load_environment_variables()
        self.checkpointer = MemorySaver()
        self.config = {"configurable": {"thread_id": "test-thread"}}
        # Create LangGraph agent
        if bind_tools:
            if self.model_provider == "openai":
                model = ChatOpenAI(model=self.model, temperature=1, openai_api_key=self.api_key,verbose=True)
            else:
                model = ChatAnthropic(model=self.model ,temperature=1,api_key=self.api_key,verbose=True)
            tools = self._collect_tools_from_connections()
            tool_executor = ToolExecutor(tools)
            if prompt:
                self.langgraphAgent =  create_react_agent(model, tool_executor.tools, checkpointer=self.checkpointer, prompt=prompt,debug=debug)
            else:
                self.langgraphAgent =  create_react_agent(model, tool_executor.tools, checkpointer=self.checkpointer,debug=debug)
        else:
            if self.model_provider == "openai":
                self.langgraphAgent =  ChatOpenAI(model=self.model, api_key=self.api_key,verbose=True)
            else:
                self.langgraphAgent =  ChatAnthropic(model=self.model, api_key=self.api_key,verbose=True)

    def _load_environment_variables(self):
        load_dotenv()
        if self.model_provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
        else:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found in environment variables")

    def _collect_tools_from_connections(self):
        tools = []
        for connection_name in self.connection_manager.get_connections():
            connection = self.connection_manager.get_connection(connection_name)
            if hasattr(connection, "tool_executor") and connection.tool_executor:
                tools.extend(connection.tool_executor.tools)
            else:
                print(f"Connection {connection_name} has no tools.")
        return tools

    def invoke(self, user_input: str):
        if self.bind_tools:
            formatted_input = {"messages": [ {"role": "user","content": user_input}]}
            return self.langgraphAgent.invoke(formatted_input, config=self.config)
        else:
            return self.langgraphAgent.invoke(user_input, config=self.config)

    def invoke_chat(self, messages: list[dict]):
        state = {"messages": messages}
        final_state = self.langgraphAgent.invoke(state, config=self.config)
        print(final_state)
        response = next(
            msg.content for msg in reversed(final_state["messages"])
            if msg.content and isinstance(msg, AIMessage)
        )
        return response

    def process_response(self, response, state):
        messages = response.get("messages", [])
        last_tool_execution = None
        final_response = None

        try:
            final_response = next(
                msg.content for msg in reversed(messages)
                if msg.content and isinstance(msg, AIMessage)
            )
        except StopIteration:
            final_response = None

        for i, message in enumerate(messages):
            if isinstance(message, AIMessage):
                tool_executions = self._extract_tool_executions(message, messages, i)
                if tool_executions:
                    last_tool_execution = tool_executions

        if last_tool_execution:
            if (final_response): #log final response
                print("Final Response:", final_response)
                last_tool_execution["final_response"] = final_response

            state["action_log"].append(last_tool_execution)

        return state

    def _extract_tool_executions(self, message, messages, index):
        tool_calls = message.additional_kwargs.get("tool_calls", [])
        
        for tool_call in tool_calls:
            tool_name = self._get_tool_name(tool_call)
            tool_parameters = self._parse_tool_parameters(tool_call)
            tool_result, tool_status = self._find_tool_result(messages, index, tool_call)

            if tool_name:  #if we have a valid tool call
                return {
                    "action": "tool_execution",
                    "tool": tool_name,
                    "parameters": tool_parameters,
                    "result": tool_result,
                    "status": tool_status
                }
        return None

    def _get_tool_name(self, tool_call):
        """Extract tool name from tool call."""
        function_info = tool_call.get("function", {})
        return function_info.get("name") or tool_call.get("name")

    def _parse_tool_parameters(self, tool_call):
        args = tool_call.get("function", {}).get("arguments")
        if isinstance(args, str):
            try:
                return json.loads(args)
            except json.JSONDecodeError:
                return {"raw_args": args}
        return tool_call.get("args", {})

    def _find_tool_result(self, messages, start_index, tool_call):
        tool_result = None
        tool_status = "pending"

        # First look for a ToolMessage with matching tool_call_id
        for msg in messages[start_index:]:
            if isinstance(msg, ToolMessage) and msg.tool_call_id == tool_call.get("id"):
                return msg.content, msg.status

        # If no ToolMessage found, look for next AIMessage with content
        for msg in messages[start_index:]:
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content, tool_status

        return tool_result, tool_status


