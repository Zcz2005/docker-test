from __future__ import annotations

import importlib
import logging
from typing import Any, Type

from .config import ScrcpyManagerConfig


logger = logging.getLogger(__name__)

TASK_MODULE_MAP = {
    "Yingke": "src.yingke_task.YingkeTask",
    "Ailiao": "src.ailiao_task.AiliaoTask",
    "Aichang": "src.aichang_task.AichangTask",
    "Kuaishou": "src.kuaishou_task.KuaishouTask",
    "Kelakela": "src.kelakela_task.KelakelaTask",
    "Xiaohongshu": "src.xiaohongshu_task.XiaohongshuTask",
    "Huajiao": "src.huajiao_task.HuajiaoTask",
    "Douyin": "src.douyin_task.DouyinTask",
    "Momo": "src.momo_task.MomoTask",
    "Baobao": "src.baobao_task.BaobaoTask",
    "Lingsheng": "src.lingsheng_task.LingshengTask",
    "Xiuse": "src.xiuse_task.XiuseTask",
    "Hongguo": "src.hongguo_task.HongguoTask",
    "Lespark": "src.lespark_task.LesparkTask",
    "Mifeng": "src.mifeng_task.MifengTask",
}


class MockPlatformTask:
    def __init__(self, device_id: str, *args: Any):
        self.device_id = device_id
        self.args = args

    def run_task(self) -> bool:
        logger.warning("Mock任务运行在设备 %s, args=%s", self.device_id, self.args)
        return True


def _import_task_class(dotted_path: str) -> Type[Any]:
    module_name, class_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def build_task_map(config: ScrcpyManagerConfig) -> dict[str, Type[Any]]:
    task_map: dict[str, Type[Any]] = {}
    for app_name, dotted_path in TASK_MODULE_MAP.items():
        try:
            task_map[app_name] = _import_task_class(dotted_path)
        except (ImportError, AttributeError) as exc:
            if config.system.allow_mock_tasks:
                logger.warning("任务类 %s 导入失败，使用 Mock: %s", app_name, exc)
                task_map[app_name] = MockPlatformTask
            else:
                logger.error("任务类 %s 导入失败: %s", app_name, exc)
    return task_map
