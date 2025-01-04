from nonebot import get_plugin_config, on_command, on_message
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Message
from nonebot.params import CommandArg
from .config import Config
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment, PrivateMessageEvent, GroupMessageEvent
import os, shutil, subprocess, time

__plugin_meta__ = PluginMetadata(
    name="test",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

test = on_command("test", priority=5)
file_get = on_message(priority=5)


@test.handle()
async def handle(bot, event, args: Message = CommandArg()):
    if mes := args.extract_plain_text():
        await test.send(mes)
    await test.finish("test")


@file_get.handle()
async def handle(bot, event):
    for msg_seg in event.message:
        # 检查消息段类型是否为wowsreplay文件
        if msg_seg.type == "file" and msg_seg.data.get("file").endswith(
                ".wowsreplay"):
            file_info = msg_seg.data
            file_id = file_info.get("file_id")

            # 获取文件下载链接
            file_url = await bot.call_api("get_file", file_id=file_id)
            file_pos = file_url.get("file")
            # await file_get.send(f"文件pos: {file_pos}")
            # 创建tmp文件夹
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            # 移动文件到当前tmp目录
            tarpos = os.path.join("tmp", os.path.basename(file_pos))
            shutil.move(file_pos, tarpos)
            try:
                result = subprocess.run(
                    ["python", "-m", "render", "--replay", tarpos],
                    check=True,
                    capture_output=True,
                    text=True)
                if result.returncode != 0:
                    await bot.send(
                        event,
                        f"Command failed with return code {result.returncode}")
                else:
                    await bot.send(event,MessageSegment.at(event.get_user_id()))
                    # video_mes = MessageSegment.video(
                    #     file=
                    #     f"file:///{os.path.join(os.getcwd(),'tmp',os.path.basename(file_pos).replace('.wowsreplay','.mp4'))}"
                    # )
                    # await bot.send(event, video_mes)
                    file_path = f"file:///{os.path.join(os.getcwd(),'tmp',os.path.basename(file_pos).replace('.wowsreplay','.mp4'))}"  # 替换为实际的文件路径
                    file_name = os.path.basename(file_pos).replace('.wowsreplay', '.mp4')  # 文件名
                    if event.message_type == "group":
                        group_id = event.group_id
                        await bot.call_api("upload_group_file",
                                           group_id=group_id,
                                           file=file_path,
                                           name=file_name)
                    elif event.message_type == "private":
                        user_id = event.user_id
                        await bot.call_api("upload_private_file",
                                           user_id=user_id,
                                           file=file_path,
                                           name=file_name)
                    # 清空tmp文件夹下的内容，保留该文件夹
                    time.sleep(10)
                    for file in os.listdir("tmp/"):
                        os.remove(os.path.join("tmp/", file))
            except subprocess.CalledProcessError as e:
                await bot.send(event, f"Command failed with error: {e.stderr}")
