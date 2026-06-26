from src.base_task import BasePlatformTask


class YingkeTask(BasePlatformTask):
    def run_task(self) -> bool:
        room_id = self.args[0] if self.args else ""
        # TODO: implement Yingke app automation via adb/uiautomator
        return bool(room_id)
