# script/MessageLength/main.py

import logging
import os
import sys
import re

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import *
from app.api import *
from app.switch import load_switch, save_switch


# 数据存储路径，实际开发时，请将MessageLength替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "MessageLength",
)


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "MessageLength")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "MessageLength", status)


# 处理元事件，用于启动时确保数据目录存在
async def handle_MessageLength_meta_event(websocket, msg):
    os.makedirs(DATA_DIR, exist_ok=True)


# 处理开关状态
async def toggle_function_status(websocket, group_id, message_id, authorized):
    if not authorized:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]❌❌❌你没有权限对MessageLength功能进行操作,请联系管理员。",
        )
        return

    if load_function_status(group_id):
        save_function_status(group_id, False)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]🚫🚫🚫MessageLength功能已关闭",
        )
    else:
        save_function_status(group_id, True)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]✅✅✅MessageLength功能已开启",
        )


# 保存消息长度
def save_message_length(group_id, length):
    with open(os.path.join(DATA_DIR, f"{group_id}.txt"), "w") as f:
        f.write(str(length))


# 加载消息长度
def load_message_length(group_id):
    with open(os.path.join(DATA_DIR, f"{group_id}.txt"), "r") as f:
        return int(f.read())


# 检测消息长度
async def check_message_length(websocket, group_id, raw_message, message_id):
    try:
        length = load_message_length(group_id)
        if len(raw_message) > length:
            await delete_msg(websocket, message_id)
    except Exception as e:
        logging.error(f"检测消息长度失败: {e}")


# 设定消息长度
async def set_message_length(websocket, group_id, raw_message, message_id):
    try:
        match = re.match(r"mlset(\d+)", raw_message)
        if match:
            length = match.group(1)
            save_message_length(group_id, length)
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]消息长度已设定为{length}",
            )
    except Exception as e:
        logging.error(f"设定消息长度失败: {e}")


# 群消息处理函数
async def handle_MessageLength_group_message(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))
        authorized = user_id in owner_id

        # 是否是开启命令
        if raw_message.startswith("ml"):
            await toggle_function_status(websocket, group_id, message_id, authorized)
        else:
            # 鉴权，如果是管理员，则设定消息长度,否则检测消息长度
            if authorized:
                await set_message_length(websocket, group_id, raw_message, message_id)
            else:
                await check_message_length(websocket, group_id, raw_message, message_id)

    except Exception as e:
        logging.error(f"处理MessageLength群消息失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "处理MessageLength群消息失败，错误信息：" + str(e),
        )
        return
