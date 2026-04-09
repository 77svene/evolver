import hashlib
import json
from pydantic import BaseModel, Field, model_validator
from typing import Any, Dict, Optional
import uuid
from datetime import datetime, timezone

class BaseEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    cryptographic_hash: str = Field(default="")

    @model_validator(mode='after')
    def compute_hash(self) -> 'BaseEvent':
        if not self.cryptographic_hash:
            # Create a deterministic representation for hashing
            data_to_hash = {
                "id": self.id,
                "timestamp": self.timestamp.isoformat(),
                "source": self.source,
                "metadata": self.metadata
            }
            # For subclasses, add their specific fields to the hash
            for field in self.model_fields.keys():
                if field not in ["id", "timestamp", "source", "metadata", "cryptographic_hash"]:
                    data_to_hash[field] = getattr(self, field)

            encoded = json.dumps(data_to_hash, sort_keys=True).encode('utf-8')
            self.cryptographic_hash = hashlib.sha256(encoded).hexdigest()
        return self

class PerformanceAnomalyEvent(BaseEvent):
    metric: str
    deviation: float
    direction: str  # e.g., "up", "down"
    context: Optional[str] = None

class AudienceSignalEvent(BaseEvent):
    signal_type: str
    confidence: float
    segment: str

class CapabilityGapEvent(BaseEvent):
    gap_type: str
    description: str
    priority: int
