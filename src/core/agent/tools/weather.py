from langchain_core.tools import tool
from langgraph.types import interrupt

@tool
def get_weather(city: str) -> str:
    """查询指定城市当前的天气情况。"""
    choice = interrupt({
        "type": "choice",
        "question": "请选择天气数据源",
        "options": ["ECMWF", "GFS"],
    })

    ecmwf_weather = {
        "北京": "晴，26°C",
        "上海": "多云，24°C",
        "深圳": "小雨，29°C",
        "杭州": "晴，27°C",
    }
    gfs_weather = {
        "北京": "晴，31°C",
        "上海": "多云，32°C",
        "深圳": "小雨，33°C",
        "杭州": "晴，34°C",
    }

    if choice == "ECMWF":
        return ecmwf_weather.get(city, "")
    elif choice == "GFS":
        return gfs_weather.get(city, "")

    return ""