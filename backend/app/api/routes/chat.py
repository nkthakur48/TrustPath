import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import HumanMessage

from app.graph.chat import get_chat_graph
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.openrouter import LLMUnavailable

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, graph=Depends(get_chat_graph)) -> ChatResponse:
    thread_id = payload.thread_id or str(uuid.uuid4())
    try:
        result = graph.invoke(
            {"messages": [HumanMessage(content=payload.message)]},
            config={"configurable": {"thread_id": thread_id}},
        )
    except LLMUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return ChatResponse(reply=result["messages"][-1].content, thread_id=thread_id)
