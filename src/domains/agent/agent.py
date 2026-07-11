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
        async for event in agent.astream_events(inputs, config=config, version="v2"):
            kind = event["event"]
            node = event.get("metadata", {}).get("langgraph_node", "")

            # --- 场景 1：LLM 逐 token 输出 ---
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                token = chunk.content
                if token:
                    yield sse_event("token", {"node": node, "content": token})
                # 转发推理/思考内容（DeepSeek 模型在可见回答前输出的 chain-of-thought）
                reasoning = chunk.additional_kwargs.get("reasoning_content", "")
                if reasoning:
                    yield sse_event("reasoning", {"node": node, "content": reasoning})

            # --- 场景 2：工具调用开始 ---
            elif kind == "on_tool_start":
                yield sse_event(
                    "tool_start",
                    {
                        "name": event["name"],
                        "input": event["data"].get("input"),
                    },
                )

            # --- 场景 3：工具调用结束 ---
            elif kind == "on_tool_end":
                yield sse_event(
                    "tool_end",
                    {
                        "name": event["name"],
                        "output": str(event["data"].get("output")),
                    },
                )

            # 这里是后端"过滤"发挥作用的地方：
            # 你完全可以只转发上面几类事件，其余 kind
            # （如 on_chain_start / on_chain_end 等中间态）
            # 直接忽略，不推送给前端。

        yield sse_event("done", {})

    except Exception as exc:  # noqa: BLE001
        yield sse_event("error", {"message": str(exc)})

@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    return StreamingResponse(
        agent_event_stream(req),
        media_type="text/event-stream",
        headers={
            # 防止反向代理（如 nginx）缓冲响应，导致前端收不到实时数据
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@router.get("/test")
async def test():
    trace_id = ctx.get_trace_id()
    logger.warning('trace id: %s', trace_id)
    return {"trace_id": trace_id}