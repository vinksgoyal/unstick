import sqlite3
from pathlib import Path


class LocalStorage:
    def __init__(self, path: str = "unstick.db"):
        self.path = Path(path)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS completions "
                "(goal_id TEXT, action_id TEXT, completed INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )

    def record_completion(self, goal_id: str, action_id: str, completed: bool) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT INTO completions(goal_id, action_id, completed) VALUES (?, ?, ?)",
                (goal_id, action_id, int(completed)),
            )
