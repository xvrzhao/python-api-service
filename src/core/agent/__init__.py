from logging import getLogger

from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, HumanInTheLoopMiddleware
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from src.core.config import settings
import src.core.agent.tools.weather as weather_tools
import src.core.agent.middlewares.test as test_middlewares


logger = getLogger(__name__)

class Agent:
    model: BaseChatModel = None
    pool: AsyncConnectionPool = None
    agent: CompiledStateGraph = None

    @classmethod
    async def init(cls):
        cls.model = ChatDeepSeek(
            api_key=settings.LLM_API_KEY, 
            model=settings.LLM_MODEL,
            streaming=True,
            temperature=0.3,
        )

        cls.pool = AsyncConnectionPool(
            conninfo=settings.postgres_uri,
            max_size=settings.PG_CONN_MAX,
            kwargs={"autocommit": True}
        )

        checkpointer = AsyncPostgresSaver(cls.pool)
        await checkpointer.setup()

        logger.info("agent init: postgres checkpointer steup complete")

        cls.agent = create_agent(
            model=cls.model,
            tools=[
                weather_tools.get_weather,
            ], 
            middleware=[
                # test_middlewares.before_model_hook,
                # test_middlewares.after_model_hook,
                # test_middlewares.after_agent_hook,
                SummarizationMiddleware(
                    model=cls.model,
                    trigger=("tokens", settings.LLM_CTX_WIN * settings.LLM_CTX_WIN_THRESHOLD),
                    keep=("tokens", settings.LLM_CTX_WIN * settings.LLM_CTX_WIN_THRESHOLD * settings.LLM_CTX_WIN_SUM_KEEP)
                ),
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "get_weather": {"allowed_decisions": ["approve", "reject"]}
                    }
                )
            ],
            checkpointer=checkpointer,
        )

    @classmethod
    async def shutdown(cls):
        if cls.pool is not None:
            await cls.pool.close()
        logger.info("agent shutdown: postgres connection pool closed")