from logging import getLogger
from typing import AsyncIterator, Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain.messages import HumanMessage
from langgraph.types import Interrupt, Command

from .schemas import ChatRequest, ResumeRequest
from src.utils.sse import sse_event
from src.core.agent.agent import agent

logger = getLogger(__name__)

router = APIRouter(prefix="/agent")

async def _agent_event_stream(input: Any, config: dict) -> AsyncIterator[str]:
    """公共的事件流处理逻辑, chat 和 resume 都会用到"""
    try:
        events = agent.astream_events(input, config=config, version="v2")
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
        
        # agent 执行完毕，判断是否有中断任务需要前端处理
        state = await agent.aget_state(config=config)
        if len(state.interrupts) > 0:
            intrs = [_classify_interrupt(intr.value) for intr in state.interrupts]
            logger.debug("agent stream done, but has interrupts: %s", intrs)
            yield sse_event("interrupt", {"items": intrs})
        else:
            yield sse_event("done", {})

    except Exception as e:
        logger.exception("agent stream error")
        yield sse_event("error", {"message": str(e)})

def _classify_interrupt(value: dict) -> dict:
    """给 interrupt 加入 type 供前端区分"""
    if "action_requests" in value:
        # HITL 中间件产生的 interrupt
        value.update({"type": "tool_approval"})
    return value

@router.post("/chat/stream", summary="发送消息")
async def chat_stream(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    input = {"messages": [HumanMessage(content=req.message)]}

    return StreamingResponse(
        _agent_event_stream(input, config),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform", # 防止反向代理（如 nginx）缓冲响应，导致前端收不到实时数据
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@router.post("/chat/resume", summary="恢复中断的任务")
async def chat_resume(req: ResumeRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    input = Command(resume=req.resume_value)

    return StreamingResponse(
        _agent_event_stream(input, config),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
