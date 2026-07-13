from logging import getLogger
from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain.messages import HumanMessage

from .schemas import ChatRequest
from src.utils.sse import sse_event
from src.core.agent.agent import agent
from src.core import ctx

logger = getLogger(__name__)

router = APIRouter(prefix="/agent")

async def agent_event_stream(req: ChatRequest) -> AsyncIterator[str]:
    config = {"configurable": {"thread_id": req.thread_id}}
    inputs = {"messages": [HumanMessage(content=req.message)]}

    try:
        events = agent.astream_events(inputs, config=config, version="v2")
        async for event in events:
            kind = event["event"]
            node = event.get("metadata", {}).get("langgraph_node", "")

            # --- 场景 1：LLM 逐 token 输出 ---
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                token = chunk.content
                if token:
                    yield sse_event("token", {"node": node, "content": token})
                reasoning = chunk.additional_kwargs.get("reasoning_content", "")
                if reasoning:
                    yield sse_event("reasoning", {"node": node, "content": reasoning})

            # --- 场景 2：工具调用开始 ---
            elif kind == "on_tool_start":
                yield sse_event("tool_start", {"name": event["name"], "input": event["data"].get("input")})

            # --- 场景 3：工具调用结束 ---
            elif kind == "on_tool_end":
                yield sse_event("tool_end", {"name": event["name"], "output": str(event["data"].get("output"))})

        yield sse_event("done", {})

    except Exception as e:
        yield sse_event("error", {"message": str(e)})

@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    return StreamingResponse(
        agent_event_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform", # 防止反向代理（如 nginx）缓冲响应，导致前端收不到实时数据
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )