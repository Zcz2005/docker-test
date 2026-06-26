# Platform task implementations

Each file exposes `<Platform>Task(device_id, *args).run_task() -> bool`.

- `device_id`: adb serial, e.g. `192.168.31.100:5555`
- `args`: usually `(room_id,)` for `target_apps`, or `(task_args,)` for URL-based apps

Implement real UI automation in these modules. The manager only orchestrates
recording + DB updates.
