"""人工事件的异步分派演示；没有模型、外部服务或真实仓库操作。"""
import asyncio
import sqlite3
from pathlib import Path

EVENTS = [
    ("e1", "pr:17", "补充空值测试"),
    ("e2", "pr:23", "检查日期格式"),
    ("e3", "pr:17", "保留原接口"),
    ("e3", "pr:17", "保留原接口"),  # 模拟重复投递
]


async def dispatch(db):
    gate = asyncio.Event()
    queues, tasks, contexts = {}, {}, {}
    new_events = direct = duplicates = 0

    async def worker(thread, queue):
        await gate.wait()  # 模拟等待外部工具，不用 sleep 伪造耗时对比
        context = []
        while not queue.empty():
            event_id, text = await queue.get()
            context.append(text)
            with db:
                db.execute("UPDATE events SET done=1 WHERE id=?", (event_id,))
        contexts[thread] = context

    for event_id, thread, text in EVENTS:
        with db:
            inserted = db.execute(
                "INSERT OR IGNORE INTO events VALUES (?, ?, ?, 0)",
                (event_id, thread, text),
            ).rowcount
        if not inserted:
            duplicates += 1
            continue
        new_events += 1
        if thread not in queues:
            queues[thread] = asyncio.Queue()
            tasks[thread] = asyncio.create_task(worker(thread, queues[thread]))
        else:
            direct += 1
        queues[thread].put_nowait((event_id, text))

    # 让 Worker 真正运行到等待点，前台仍可继续分派。
    await asyncio.sleep(0)
    pending = sum(not task.done() for task in tasks.values())
    print(f"new_events={new_events}")
    print(f"new_worker_routes={len(tasks)}")
    print(f"direct_followups={direct}")
    print(f"duplicate_deliveries={duplicates}")
    print(f"workers_waiting_when_dispatch_finished={pending}")
    gate.set()
    await asyncio.gather(*tasks.values())
    for thread in sorted(contexts):
        print(f"{thread}={' / '.join(contexts[thread])}")
    print(f"worker_results={len(contexts)}")
    assert contexts == ({"pr:17": ["补充空值测试", "保留原接口"],
                         "pr:23": ["检查日期格式"]} if new_events else {})


def main():
    path = Path("demo.sqlite")
    if path.exists():
        raise SystemExit("请在新的临时目录运行，保留现有数据库。")
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE events (id TEXT PRIMARY KEY, thread TEXT, text TEXT, done INTEGER)")
        print("[first_delivery]")
        asyncio.run(dispatch(db))
    # 关闭并重新打开 SQLite，模拟正常完成之后的重启/重放。
    with sqlite3.connect(path) as db:
        print("[replay_after_reopen]")
        asyncio.run(dispatch(db))
        print(f"stored_events={db.execute('SELECT COUNT(*) FROM events').fetchone()[0]}")
        print(f"completed_events={db.execute('SELECT COUNT(*) FROM events WHERE done=1').fetchone()[0]}")


if __name__ == "__main__":
    main()
