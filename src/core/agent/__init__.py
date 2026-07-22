from logging import getLogger

from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, HumanInTheLoopMiddleware
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Checkpointer
from psycopg_pool import AsyncConnectionPool

from src.core.config import settings
import src.core.agent.tools.weather as weather_tools
import src.core.agent.middlewares.test as test_middlewares


logger = getLogger(__name__)

class AgentProvider:

    def __init__(self):
        self.model: BaseChatModel | None = None
        self.pool: AsyncConnectionPool | None = None
        self.checkpointer: Checkpointer | None = None
        self.agent: CompiledStateGraph | None = None

    async def init(self):
        self.model = ChatDeepSeek(
            api_key=settings.LLM_API_KEY, 
            model=settings.LLM_MODEL,
            streaming=True,
            temperature=0.3,
        )

        self.pool = AsyncConnectionPool(
            conninfo=settings.postgres_uri,
            max_size=settings.PG_CONN_MAX,
            kwargs={"autocommit": True}
        )

        self.checkpointer = AsyncPostgresSaver(self.pool)
        await self.checkpointer.setup()

        logger.info("agent init: postgres checkpointer steup complete")

        self.agent = create_agent(
            model=self.model,
            tools=[
                weather_tools.get_weather,
            ], 
            middleware=[
                # test_middlewares.before_model_hook,
                # test_middlewares.after_model_hook,
                # test_middlewares.after_agent_hook,
                SummarizationMiddleware(
                    model=self.model,
                    trigger=("tokens", settings.LLM_CTX_WIN * settings.LLM_CTX_WIN_THRESHOLD),
                    keep=("tokens", settings.LLM_CTX_WIN * settings.LLM_CTX_WIN_THRESHOLD * settings.LLM_CTX_WIN_SUM_KEEP)
                ),
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "get_weather": {"allowed_decisions": ["approve", "reject"]}
                    }
                )
            ],
            checkpointer=self.checkpointer,
        )

    async def shutdown(self):
        if self.pool is not None:
            await self.pool.close()
        logger.info("agent shutdown: postgres connection pool closed")


agent_provider = AgentProvider()