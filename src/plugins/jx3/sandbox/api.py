from src.tools.dep import *


async def sandbox_(server: str = None, group_id: str = None):  # 沙盘 <服务器>
    server = server_mapping(server, group_id=group_id)
    if not server:
        return [PROMPT_ServerNotExist]
    if server != None:
        final_url = f"{Config.jx3api_link}/view/server/sand?token={token}&scale=1&robot={bot}&server=" + server
<<<<<<< HEAD
    data = await get_api(final_url, proxy=proxies)
=======
    data = await get_api(final_url)
>>>>>>> 14476fd734b56a647406dd0ab8bdf37d6f6707a0
    if data["code"] == 400:
        return [PROMPT_ServerInvalid]
    return data["data"]["url"]
