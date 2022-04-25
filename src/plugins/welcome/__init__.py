from nonebot import on_notice, on_command
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot, NoticeEvent, Event
from aiocqhttp import MessageSegment as ms
import sys
sys.path.append("/root/nb/src/tools")
from permission import checker, error
from file import read, write

welcome = on_notice(priority=5)

@welcome.handle()
async def _(bot: Bot, event: NoticeEvent):
    if event.notice_type == "group_increase":
        obj = event.user_id
        group = event.group_id
        msg = ms.at(obj) + read("/root/nb/src/plugins/welcome/welcome.txt")
        await bot.call_api("send_group_msg",group_id=group, message=msg)
    
welcome_msg_edit = on_command("welcome_msg_edit",aliases={"wme"},priority=5)

@welcome_msg_edit.handle()
async def __(matcher: Matcher, event: Event, args: Message = CommandArg()):
    if checker(str(event.user_id),5) == False:
        await welcome_msg_edit.finish(error(5))
    msg = args.extract_plain_text()
    if msg:
        write("/root/nb/src/plugins/welcome/welcome.txt", msg)
        await welcome_msg_edit.finish("喵~已设置入群欢迎！")
    else:
        await welcome_msg_edit.finish("您输入了什么？")