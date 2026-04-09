"""Custom exception hierarchies for the Autonomous Marketing Organism."""

class OrganismError(Exception):
    """Base exception class for all Organism-related errors."""
    pass

class AgentExecutionError(OrganismError):
    """Raised when an agent encounters a critical failure during its PDA loop."""
    pass

class EventBusError(OrganismError):
    """Raised when the event bus fails to publish or route an event."""
    pass

class KnowledgeGraphError(OrganismError):
    """Raised when a persistent storage operation fails."""
    pass

class LLMIntegrationError(OrganismError):
    """Raised when communication with the language model backend fails."""
    pass

class ToolGenerationError(OrganismError):
    """Raised when dynamic tool synthesis or validation fails."""
    pass
