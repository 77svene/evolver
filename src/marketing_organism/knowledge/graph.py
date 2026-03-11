import json
import logging
import asyncio
import sqlite3
from typing import Dict, Any, List

class KnowledgeGraph:
    def __init__(self, in_memory: bool = True, db_path: str = None):
        self.in_memory = in_memory
        self.db_path = db_path if not in_memory and db_path else ":memory:"
        self._lock = asyncio.Lock()

        # When using an in-memory db, sqlite closes the db when the connection object is destroyed.
        # We need a persistent connection for in_memory across function calls.
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        cursor = self._conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                type TEXT,
                data TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT,
                target_id TEXT,
                type TEXT,
                weight REAL,
                FOREIGN KEY(source_id) REFERENCES entities(id),
                FOREIGN KEY(target_id) REFERENCES entities(id)
            )
        ''')
        self._conn.commit()

    async def store_entity(self, entity_id: str, data: Dict[str, Any]):
        """Creates or updates a graph node."""
        async with self._lock:
            def _insert():
                entity_type = data.get("type", "")
                self._conn.execute(
                    "INSERT OR REPLACE INTO entities (id, type, data) VALUES (?, ?, ?)",
                    (entity_id, entity_type, json.dumps(data))
                )
                self._conn.commit()
            await asyncio.to_thread(_insert)

    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        async with self._lock:
            def _get():
                cursor = self._conn.cursor()
                cursor.execute("SELECT data FROM entities WHERE id = ?", (entity_id,))
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return {}
            return await asyncio.to_thread(_get)

    async def add_relationship(self, source_id: str, target_id: str, relationship_type: str, weight: float = 1.0):
        """Creates an edge between two entities."""
        async with self._lock:
            def _insert_edge():
                self._conn.execute(
                    "INSERT INTO relationships (source_id, target_id, type, weight) VALUES (?, ?, ?, ?)",
                    (source_id, target_id, relationship_type, weight)
                )
                self._conn.commit()
            await asyncio.to_thread(_insert_edge)

    async def query_relations(self, source_id: str) -> List[Dict[str, Any]]:
        """Returns all connected edges from a node."""
        async with self._lock:
            def _query():
                cursor = self._conn.cursor()
                cursor.execute("SELECT target_id, type, weight FROM relationships WHERE source_id = ?", (source_id,))
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "target": row[0],
                        "type": row[1],
                        "weight": row[2]
                    })
                return results
            return await asyncio.to_thread(_query)

    async def query_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Finds entities by their 'type' attribute."""
        async with self._lock:
            def _query_type():
                cursor = self._conn.cursor()
                cursor.execute("SELECT id, data FROM entities WHERE type = ?", (entity_type,))
                results = []
                for row in cursor.fetchall():
                    data = json.loads(row[1])
                    results.append({"id": row[0], **data})
                return results
            return await asyncio.to_thread(_query_type)

    def __del__(self):
        try:
            if hasattr(self, '_conn') and self._conn:
                self._conn.close()
        except Exception:
            pass
