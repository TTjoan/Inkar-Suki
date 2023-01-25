import os

from src.liteyuki_api.config import Path


def update_resource():
    if os.path.exists(os.path.join(Path.res, ".git")):
        os.system(f"cd {Path.res} & git pull --force https://gitee.com/snowykami/liteyuki-resource")
    else:
        os.system(f"cd {Path.src} & git clone https://gitee.com/snowykami/liteyuki-resource resource")


def update_liteyuki():
    os.system("git pull --force https://gitee.com/snowykami/liteyuki-bot")
