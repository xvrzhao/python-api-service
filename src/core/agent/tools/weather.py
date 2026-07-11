from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """查询指定城市当前的天气情况。"""
    fake_weather = {
        "北京": "晴，26°C",
        "上海": "多云，24°C",
        "深圳": "小雨，29°C",
        "杭州": "晴，27°C",
    }
    return fake_weather.get(city, f"暂无「{city}」的天气数据（示例工具，未接入真实天气 API）。")