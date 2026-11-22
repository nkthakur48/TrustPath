from functools import lru_cache
from typing import Annotated, Dict, List

from langchain_core.messages import AIMessage, AnyMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.services import openrouter

SYSTEM_PROMPT = "You are TrustPath's assistant. Help job seekers spot fraudulent job offers. Answer clearly and concisely."
_ROLES = {"human": "user", "ai": "assistant", "system": "system"}


class ChatState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]


def _to_openai(messages: List[AnyMessage]) -> List[Dict[str, str]]:
    return [{"role": _ROLES.get(m.type, "user"), "content": str(m.content)} for m in messages]


def chat_node(state: ChatState) -> dict:
    history = [{"role": "system", "content": SYSTEM_PROMPT}] + _to_openai(state["messages"])
    return {"messages": [AIMessage(content=openrouter.complete_chat(history))]}


def build_chat_graph():
    builder = StateGraph(ChatState)
    builder.add_node("chat", chat_node)
    builder.add_edge(START, "chat")
    builder.add_edge("chat", END)
    # ponytail: in-memory history per thread_id, lost on restart. Upgrade: a persistent checkpointer.
    return builder.compile(checkpointer=InMemorySaver())


@lru_cache
def get_chat_graph():
    return build_chat_graph()
