"""LangGraph-based insurance assistant agent."""
import json
from typing import Any, TypedDict

from langchain.tools import StructuredTool
from langchain_core.messages import AIMessage, FunctionMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolExecutor, ToolInvocation

from app.config.logging import get_logger
from app.config.settings import get_settings
from app.tools.db_tools import (
    get_claim_by_id,
    get_claim_by_number,
    get_claims_by_policy_id,
    get_claims_by_status,
    get_customer_by_email,
    get_customer_by_id,
    get_documents_for_claim,
    get_documents_for_policy,
    get_policies_by_customer_id,
    get_policy_by_id,
    get_policy_by_number,
    search_claims,
    search_policies,
)

logger = get_logger(__name__)
settings = get_settings()


SYSTEM_PROMPT = """You are an expert insurance assistant designed to help customers with their insurance-related queries. You have access to a database of customers, policies, claims, and documents.

Your capabilities:
1. Look up policy information by ID or policy number
2. Look up claim information by ID or claim number
3. Get all policies for a customer
4. Get all claims for a policy
5. Get documents associated with policies or claims
6. Search for policies or claims

When a user asks about their policy or claim:
1. First identify what information they need (policy status, claim status, etc.)
2. Use the appropriate tools to query the database
3. Provide a clear, helpful response based on the data

Always be helpful, accurate, and professional. If you cannot find information, let the user know politely.

Important notes:
- Policy numbers look like: POL-AUTO-12345, POL-HOME-67890, etc.
- Claim numbers look like: CLM-2024-00001, CLM-2024-00002, etc.
- UUIDs are long strings like: 550e8400-e29b-41d4-a716-446655440000

When presenting information:
- Format monetary amounts with dollar signs and commas
- Format dates in a readable way
- Summarize the most important information first
"""


class AgentState(TypedDict):
    """State for the insurance assistant agent."""

    messages: list[Any]
    data_used: dict[str, Any]


def create_tools() -> list[StructuredTool]:
    """Create the tools for the agent."""
    tools = [
        StructuredTool.from_function(
            func=get_customer_by_id,
            name="get_customer_by_id",
            description="Get customer information by their UUID. Use this when you have a customer ID.",
        ),
        StructuredTool.from_function(
            func=get_customer_by_email,
            name="get_customer_by_email",
            description="Get customer information by their email address.",
        ),
        StructuredTool.from_function(
            func=get_policy_by_id,
            name="get_policy_by_id",
            description="Get policy information by policy UUID. Returns policy details and customer info.",
        ),
        StructuredTool.from_function(
            func=get_policy_by_number,
            name="get_policy_by_number",
            description="Get policy information by policy number (e.g., POL-AUTO-12345). Returns policy details and customer info.",
        ),
        StructuredTool.from_function(
            func=get_policies_by_customer_id,
            name="get_policies_by_customer_id",
            description="Get all policies belonging to a specific customer by their UUID.",
        ),
        StructuredTool.from_function(
            func=get_claim_by_id,
            name="get_claim_by_id",
            description="Get claim information by claim UUID. Returns claim details and associated policy info.",
        ),
        StructuredTool.from_function(
            func=get_claim_by_number,
            name="get_claim_by_number",
            description="Get claim information by claim number (e.g., CLM-2024-00001). Returns claim details and associated policy info.",
        ),
        StructuredTool.from_function(
            func=get_claims_by_policy_id,
            name="get_claims_by_policy_id",
            description="Get all claims filed against a specific policy by policy UUID.",
        ),
        StructuredTool.from_function(
            func=get_claims_by_status,
            name="get_claims_by_status",
            description="Get claims filtered by status. Valid statuses: submitted, under_review, approved, denied, paid, closed.",
        ),
        StructuredTool.from_function(
            func=get_documents_for_policy,
            name="get_documents_for_policy",
            description="Get all documents associated with a policy by policy UUID.",
        ),
        StructuredTool.from_function(
            func=get_documents_for_claim,
            name="get_documents_for_claim",
            description="Get all documents associated with a claim by claim UUID.",
        ),
        StructuredTool.from_function(
            func=search_policies,
            name="search_policies",
            description="Search for policies by policy number or type. Returns matching policies.",
        ),
        StructuredTool.from_function(
            func=search_claims,
            name="search_claims",
            description="Search for claims by claim number or type. Returns matching claims.",
        ),
    ]
    return tools


def create_agent():
    """Create the LangGraph insurance assistant agent."""
    tools = create_tools()
    tool_executor = ToolExecutor(tools)

    # Create the LLM with tools bound
    # Using gpt-4-turbo as the stable production model
    llm = ChatOpenAI(
        model="gpt-4-turbo",
        temperature=0,
        api_key=settings.openai_api_key,
    ).bind_tools(tools)

    def should_continue(state: AgentState) -> str:
        """Determine if the agent should continue or end."""
        messages = state["messages"]
        last_message = messages[-1]

        # If LLM made tool calls, continue to tool node
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # Otherwise, end
        return END

    def call_model(state: AgentState) -> AgentState:
        """Call the LLM model."""
        messages = state["messages"]

        # Add system message if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        response = llm.invoke(messages)

        return {"messages": messages + [response], "data_used": state.get("data_used", {})}

    def process_tools(state: AgentState) -> AgentState:
        """Process tool calls and track data used."""
        messages = state["messages"]
        data_used = state.get("data_used", {})

        # Get the last message which should have tool calls
        last_message = messages[-1]
        new_messages = []

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id", "")

                # Track what data was queried
                if tool_name not in data_used:
                    data_used[tool_name] = []
                data_used[tool_name].append(tool_args)

                # Execute the tool
                action = ToolInvocation(tool=tool_name, tool_input=tool_args)
                result = tool_executor.invoke(action)

                # Parse and track results
                try:
                    result_data = json.loads(result)
                    if result_data.get("success") and "data" in result_data:
                        if "results" not in data_used:
                            data_used["results"] = {}
                        data_used["results"][tool_name] = result_data["data"]
                except (json.JSONDecodeError, TypeError):
                    pass

                # Create a tool message with the result
                from langchain_core.messages import ToolMessage
                new_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_id)
                )

        return {
            "messages": messages + new_messages,
            "data_used": data_used,
        }

    # Build the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", process_tools)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )

    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")

    # Compile the graph
    return workflow.compile()


class InsuranceAssistant:
    """Insurance assistant powered by LangGraph."""

    def __init__(self):
        """Initialize the insurance assistant."""
        self.graph = create_agent()
        logger.info("Insurance assistant initialized")

    async def chat(self, user_id: str, message: str) -> tuple[str, dict[str, Any]]:
        """
        Process a chat message from a user.

        Args:
            user_id: The user's identifier
            message: The user's message

        Returns:
            Tuple of (response text, data used by the agent)
        """
        logger.info("Processing chat message", user_id=user_id, message_preview=message[:100])

        try:
            # Create initial state
            initial_state: AgentState = {
                "messages": [HumanMessage(content=message)],
                "data_used": {"user_id": user_id},
            }

            # Run the agent
            result = self.graph.invoke(initial_state)

            # Extract the final response
            messages = result.get("messages", [])
            data_used = result.get("data_used", {})

            # Find the last AI message
            response_text = "I apologize, but I couldn't process your request."
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content:
                    response_text = msg.content
                    break

            logger.info(
                "Chat response generated",
                user_id=user_id,
                response_length=len(response_text),
            )

            return response_text, data_used

        except Exception as e:
            logger.error("Error processing chat message", error=str(e), user_id=user_id)
            raise


# Singleton instance
_assistant: InsuranceAssistant | None = None


def get_assistant() -> InsuranceAssistant:
    """Get or create the insurance assistant instance."""
    global _assistant
    if _assistant is None:
        _assistant = InsuranceAssistant()
    return _assistant
