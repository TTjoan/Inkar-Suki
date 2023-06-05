import nonebot
import json
import sys

from src.plugins.help import css
from src.tools.file import write, read
from src.tools.utils import get_api
from src.tools.generate import generate, get_uuid

from playwright.async_api import async_playwright
from tabulate import tabulate

from .jx3 import server_mapping
from .coin import copperl, silverl, goldl, brickl
from sgtpyutils.extensions.clazz import dict2obj,get_fields

TOOLS = nonebot.get_driver().config.tools_path
sys.path.append(TOOLS)
ASSETS = TOOLS[:-5] + "assets"
CACHE = TOOLS[:-5] + "cache"


'''
交易行物品查询。

数据来源@JX3BOX
'''

css_fixed = """
.c-header
{
    display: none;
}
.m-breadcrumb .u-stat
{
    display: none;
}
.c-breadcrumb
{
    display: none;
}
.c-header-inner
{
    display: none;
}
// 别抄啊，用了好久测出来的呢（
// 要抄好歹点个star 然后赞助赞助（狗头）
"""

async def check_bind(id: str):
    final_url = f"https://helper.jx3box.com/api/wiki/post?type=item&source_id={id}"
    data = await get_api(final_url)
    bind_type = data["data"]["source"]["BindType"] or 0
    return bind_type

class GoodsInfo(dict):
    bind_types = ["未知", "不绑定", "装备后绑定", "拾取后绑定"]
    def __init__(self,data:dict = None) -> None:
        if data is None:
            data = {}
        self.id = data.get('id')
        self.bind_type = data.get('bind_type') or 0
        self.icon = data.get('IconID') or 18888 # 默认给个小兔兔
        self.quality = data.get('Quality')
        self.ui_id = data.get('UiID')
        self.name = data.get('Name') or '未知物品'
        '''被使用的次数，次数多的优先前置'''
        self.u_popularity = 0
        super().__init__()
    @property
    def img_url(self):
        return f"https://icon.jx3box.com/icon/{self.icon}.png"
    @property
    def html_code(self):
        return f"<img src={self.img_url}></img>"
    @property
    def color(self):
        '''
        根据品质返回 灰、绿、蓝、紫、金、红
        '''
        return ['rgb(190,190,190)','rgb(0, 210, 75)','rgb(0, 126, 255)','rgb(254, 45, 254)','rgb(255, 165, 0)','#ff0000'][self.quality]
    def to_row(self):
        new = [self.id, self.name, self.bind_type_str, self.html_code]
        return new

    @property
    def bind_type_str(self):
        return self.bind_types[self.bind_type]
        
    def __repr__(self) -> str:
        return json.dumps(self.__dict__)

CACHE_goods = json.loads(read(ASSETS + "/jx3/info_goods.json")) # 每次重启后从磁盘加载缓存
CACHE_goods = dict([[x,dict2obj(GoodsInfo(),CACHE_goods[x])] for x in CACHE_goods]) # 转换为类
def __flush_cache_goods():
    data = json.dumps(dict([key, CACHE_goods[key].__dict__] for key in CACHE_goods))
    write(ASSETS + "/jx3/info_goods.json", data)

async def search_item_info(item_name: str,pageIndex:int=0,pageSize:int=20):
    final_url = f"https://helper.jx3box.com/api/item/search?keyword={item_name}&limit={pageSize}&page={pageIndex+1}"
    box_data = await get_api(final_url)
    items = box_data["data"]["data"]
    if not items:
        return "没有找到该物品哦~"
    space = []
    query_items = []
    space.append(["序号", "物品ID", "物品名称", "绑定类型", "物品图标"])
    new_goods = False
    for item in items:
        id = item['id']
        if not id in CACHE_goods:
            item['bind_type'] = await check_bind(id)
            CACHE_goods[id] = GoodsInfo(item)
            new_goods = True
        item:GoodsInfo = CACHE_goods[id]
        query_items.append(item)

    query_items.sort(key=lambda x:x.u_popularity) # 按热门程度排序
    space += [([index] + x.to_row()) for index,x in enumerate(query_items)]
    
    html = "<div style=\"font-family:Custom\">" + \
        tabulate(space, tablefmt="unsafehtml") + "</div>" + css
    final_path = CACHE + "/" + get_uuid() + ".html"
    write(final_path, html)
    img = await generate(final_path, False, "table", False)
    if new_goods:
        __flush_cache_goods()

    return [[i.id for i in query_items], img]
    

async def getItemPriceById(id: str, server: str, all_ids:list):
    '''
    通过物品id获取交易行价格
    @param id:物品id
    @param server:服务器名称
    @param all_ids:本次选中的所有id。出现过的id应将其人气降1，以更好排序

    @return [image] | str: 正确处理则返回[]，否则返回错误原因
    '''
    server = server_mapping(server)
    if server == False:
        return "唔……服务器名输入错误。"
    final_url = f"https://next2.jx3box.com/api/item-price/{id}/logs?server={server}"
    data = await get_api(final_url)
    if data["data"]["logs"] == "null":
        return "唔……交易行没有此物品哦~"
    logs = data["data"]["logs"]
    logs.reverse()
    chart = []
    chart.append(["日期", "日最高价", "日均价", "日最低价"])
    for i in logs:
        date = i["Date"]
        LowestPrice = convert(i["LowestPrice"])
        AvgPrice = convert(i["AvgPrice"])
        HighestPrice = convert(i["HighestPrice"])
        new = [date, HighestPrice, AvgPrice, LowestPrice]
        chart.append(new)
    header_server = f'<div style="font-size:3rem">交易行·{server}</div>'
    goods_info:GoodsInfo = CACHE_goods[id] if id in CACHE_goods else GoodsInfo()
    goods_info.u_popularity += 10 # 被选中则增加其曝光概率
    header_goods = f'<div style="margin: 0.5rem;font-size:1.8rem;color:{goods_info.color}">物品 {goods_info.name} <img style="vertical-align: middle;width:1.8rem" src="{goods_info.img_url}"/></div>'
    header = f'{header_server}{header_goods}'
    table = tabulate(chart, tablefmt="unsafehtml")
    table = table.replace('<table>','<table style="margin: auto">') # 居中显示
    table = f'<div>{table}</div>' # 居中表格
    html = f'<section style="text-align: center;width:50rem;"><div style=\"font-family:Custom\">{header}{table}</div></section>' + css
    final_path = CACHE + "/" + get_uuid() + ".html"
    write(final_path, html)
    img = await generate(final_path,False,'section')

    # 本轮已曝光物品，日后曝光率应下调
    for id in all_ids:
        x:GoodsInfo = CACHE_goods[id]
        x.u_popularity -= 1
    __flush_cache_goods()
    return [img]


async def getItem(id: str):
    boxdata = await get_api(f"https://helper.jx3box.com/api/wiki/post?type=item&source_id={id}")
    if boxdata["data"]["source"] == None:
        return ["唔……该物品不存在哦~"]
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=0)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(f"https://www.jx3box.com/item/view/{id}")
        await page.add_style_tag(content=css_fixed)
        path = CACHE + "/" + get_uuid() + ".png"
        await page.locator(".c-item-wrapper").first.screenshot(path=path)
        return path


def convert(price: int):
    if 1 <= price <= 99:  # 铜
        msg = f"{price} 铜"
    elif 100 <= price <= 9999:  # 银
        copper = price % 100
        silver = (price - copper) / 100
        if copper == 0:
            msg = str(int(silver)) + " 银"
        else:
            msg = str(int(silver)) + " 银" + " " + str(int(copper)) + " 铜"
    elif 10000 <= price <= 99999999:  # 金
        copper = price % 100
        silver = ((price - copper) % 10000) / 100
        gold = (price - copper - silver) / 10000
        msg = str(int(gold)) + " 金"
        if str(int(silver)) != "0":
            msg = msg + " " + str(int(silver)) + " 银"
        if str(int(copper)) != "0":
            msg = msg + " " + str(int(copper)) + " 铜"
    elif 100000000 <= price:  # 砖
        copper = price % 100
        silver: int = ((price - copper) % 10000) / 100
        gold = ((price - copper - silver*100) % 100000000) / 10000
        brick = (price - copper - silver*100 - gold*10000) / 100000000
        msg = str(int(brick)) + " 砖"
        if str(int(gold)) != "0":
            msg = msg + " " + str(int(gold)) + " 金"
        if str(int(silver)) != "0":
            msg = msg + " " + str(int(silver)) + " 银"
        if str(int(copper)) != "0":
            msg = msg + " " + str(int(copper)) + " 铜"
    msg = msg.replace("金", f"<img src=\"{goldl}\">").replace("砖", f"<img src=\"{brickl}\">").replace(
        "银", f"<img src=\"{silverl}\">").replace("铜", f"<img src=\"{copperl}\">")
    return msg
