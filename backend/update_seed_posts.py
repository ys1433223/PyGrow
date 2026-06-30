"""One-time script to update existing seed posts with code block formatting."""
import asyncio
from app.database import async_session
from app.models.community import Post
from sqlalchemy import update

POST_UPDATES = {
    2: (
        "分享一个很实用的 Python 字符串处理技巧",
        "最近在处理大量文本数据时发现，用 str.translate() 和 str.maketrans() 比 replace 循环快很多。我来分享一下具体用法和性能对比，希望对大家有帮助！\n\n```python\nimport time\n\n# 方法1: 链式 replace（慢）\ntext = \"Hello, World! Python is awesome.\"\nfor _ in range(100000):\n    result = text.replace(\"H\", \"\").replace(\"e\", \"\").replace(\"o\", \"\")\n\n# 方法2: translate（快 3-5 倍）\ntrans_table = str.maketrans(\"\", \"\", \"Heo\")\nfor _ in range(100000):\n    result = text.translate(trans_table)\n```\n\n实测在 10 万次替换中，translate 比 replace 快约 4 倍，数据量越大差距越明显！"
    ),
    10: (
        "分享一个我自己写的天气查询小工具",
        "用 requests + tkinter 写了个桌面天气查询工具，输入城市名就能显示实时天气。代码开源在 GitHub 上，欢迎大家提建议！\n\n核心思路是用和风天气 API 获取实时数据，tkinter 做简单的 GUI：\n\n```python\nimport requests\nimport tkinter as tk\nfrom tkinter import messagebox\n\nAPI_KEY = \"your_key_here\"\nCITY = \"北京\"\n\ndef get_weather(city):\n    url = f\"https://api.qweather.com/v7/weather/now?location={city}&key={API_KEY}\"\n    resp = requests.get(url).json()\n    now = resp[\"now\"]\n    return f\"{city} 天气: {now['text']}，温度 {now['temp']}°C\"\n\n# 简单 GUI\nroot = tk.Tk()\nroot.title(\"天气查询\")\nentry = tk.Entry(root, width=30)\nentry.pack(pady=10)\nbtn = tk.Button(root, text=\"查询\", command=lambda: show_weather())\nbtn.pack()\nroot.mainloop()\n```\n\n感兴趣的同学可以 clone 下来试试，欢迎 Star 和 PR！"
    ),
}


async def main():
    async with async_session() as session:
        for post_id, (title, content) in POST_UPDATES.items():
            await session.execute(
                update(Post).where(Post.id == post_id).values(title=title, content=content)
            )
        await session.commit()
        print(f"Updated {len(POST_UPDATES)} seed posts with code blocks.")


if __name__ == "__main__":
    asyncio.run(main())
