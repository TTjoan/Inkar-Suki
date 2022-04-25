from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Event
import os, sys
sys.path.append("/root/nb/src/tools")
from permission import checker, error

back = on_command("back",priority=5)

@back.handle()
async def back_(matcher: Matcher, event: Event, args: Message = CommandArg()):
    if checker(str(event.user_id),10) == False:
        await back.finish(error(10))
    os.system(args.extract_plain_text())
    await back.finish("好啦，执行完毕！")

front = on_command("front",priority=5)

@front.handle()
async def front_(matcher: Matcher, event: Event, args: Message = CommandArg()):
    if checker(str(event.user_id),10) == False:
        await front.finish(error(10))
    msg = os.popen(args.extract_plain_text()).read()
    await front.finish(f"{msg}")