from logging import getLogger

from langchain.agents import AgentState
from langchain.agents.middleware import before_model, after_model, after_agent
from langgraph.runtime import Runtime
from langchain.agents.middleware import SummarizationMiddleware, dynamic_prompt
from langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

logger = getLogger(__name__)

@before_model
def before_model_hook(state: AgentState, runtime: Runtime):
    messages = state.get("messages", [])
    logger.warning("Before model call: mmessage length: %d", len(messages))
    for i, message in enumerate(messages):
        # logger.warning("Before Message %d: %s: %s", i, type(message), message.content)
        logger.warning("Before Message %d: %s", i, message.pretty_repr())

@after_model
def after_model_hook(state: AgentState, runtime: Runtime):
    messages = state.get("messages", [])
    logger.warning("After model call: mmessage length: %d", len(messages))
    for i, message in enumerate(messages):
        # logger.warning("After Message %d: %s: %s", i, type(message), message.content)
        logger.warning("After Message %d: %s", i, message.pretty_repr())

@after_agent
def after_agent_hook(state: AgentState, runtime: Runtime):
    messages = state.get("messages", [])
    logger.warning("After agent call: mmessage length: %d", len(messages))
    for i, message in enumerate(messages):
        # logger.warning("After Message %d: %s: %s", i, type(message), message.content)
        logger.warning("After Message %d: %s", i, message.pretty_repr())