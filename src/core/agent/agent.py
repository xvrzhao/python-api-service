from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware

from src.core.config import settings
import src.core.agent.tools.weather as weather_tools
import src.core.agent.middlewares.test as test_middlewares

model = ChatDeepSeek(
    api_key=settings.LLM_API_KEY, 
    model=settings.LLM_MODEL,
    streaming=True,
    temperature=0.3,
)

checkpointer = MemorySaver()  # 会话状态存储，示例用内存即可，生产环境换成持久化存储

agent = create_agent(
    model=model, 
    tools=[
        weather_tools.get_weather,
    ], 
    middleware=[
        # test_middlewares.before_model_hook,
        # test_middlewares.after_model_hook,
        # test_middlewares.after_agent_hook,
        SummarizationMiddleware(
            model=model,
            trigger=("tokens", settings.LLM_CTX_WIN * settings.LLM_CTX_WIN_THRESHOLD),
            keep=("tokens", settings.LLM_CTX_WIN * settings.LLM_CTX_WIN_THRESHOLD * settings.LLM_CTX_WIN_SUM_KEEP)
        ),
    ],
    checkpointer=checkpointer,
)