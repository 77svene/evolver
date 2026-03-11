import json
import logging
import asyncio
from typing import Dict, Any, List

class KnowledgeGraph:
    def __init__(self, in_memory: bool = True, db_path: str = None):
        self.in_memory = in_memory
        self.db_path = db_path
        self._graph_store: Dict[str, Dict[str, Any]] = {}
        self._edges: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

        # Load from disk if not purely in-memory
        if not self.in_memory and self.db_path:
            self._load()

    async def store_entity(self, entity_id: str, data: Dict[str, Any]):
        """Creates or updates a graph node."""
        async with self._lock:
            self._graph_store[entity_id] = data
            if not self.in_memory:
                self._save()

    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        async with self._lock:
            return self._graph_store.get(entity_id, {})

    async def add_relationship(self, source_id: str, target_id: str, relationship_type: str, weight: float = 1.0):
        """Creates an edge between two entities."""
        async with self._lock:
            if source_id not in self._edges:
                self._edges[source_id] = []

            edge = {
                "target": target_id,
                "type": relationship_type,
                "weight": weight
            }
            self._edges[source_id].append(edge)
            if not self.in_memory:
                self._save()

    async def query_relations(self, source_id: str) -> List[Dict[str, Any]]:
        """Returns all connected edges from a node."""
        async with self._lock:
            return self._edges.get(source_id, [])

    async def query_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Finds entities by their 'type' attribute."""
        async with self._lock:
            results = []
            for e_id, data in self._graph_store.items():
                if data.get("type") == entity_type:
                    results.append({"id": e_id, **data})
            return results

    def _save(self):
        try:
            with open(self.db_path, "w") as f:
                json.dump({
                    "nodes": self._graph_store,
                    "edges": self._edges
                }, f)
        except Exception as e:
            logging.error(f"Failed to save KnowledgeGraph to {self.db_path}: {e}")

    def _load(self):
        try:
            with open(self.db_path, "r") as f:
                data = json.load(f)
                self._graph_store = data.get("nodes", {})
                self._edges = data.get("edges", {})
        except FileNotFoundError:
            logging.info("Starting with empty KnowledgeGraph")
        except Exception as e:
            logging.error(f"Failed to load KnowledgeGraph from {self.db_path}: {e}")
