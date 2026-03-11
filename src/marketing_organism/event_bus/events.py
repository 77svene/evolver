from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
import uuid
from datetime import datetime, timezone

class BaseEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

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
