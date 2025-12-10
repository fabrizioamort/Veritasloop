"""
Pydantic models and schemas for VeritasLoop.
Defines the core data structures used for claims, sources, debate messages, and verdicts.
"""

import operator
from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing_extensions import TypedDict


class Reliability(str, Enum):
    """Reliability level of a source."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentType(str, Enum):
    """Identifies the agent role."""
    PRO = "PRO"
    CONTRA = "CONTRA"
    JUDGE = "JUDGE"


class MessageType(str, Enum):
    """Type of debate message."""
    ARGUMENT = "argument"
    REBUTTAL = "rebuttal"
    DEFENSE = "defense"


class VerdictType(str, Enum):
    """Final verdict categories."""
    VERO = "VERO"
    FALSO = "FALSO"
    PARZIALMENTE_VERO = "PARZIALMENTE_VERO"
    CONTESTO_MANCANTE = "CONTESTO_MANCANTE"
    NON_VERIFICABILE = "NON_VERIFICABILE"


class ClaimCategory(str, Enum):
    """Category of the news claim."""
    POLITICS = "politics"
    HEALTH = "health"
    ECONOMY = "economy"
    SCIENCE = "science"
    OTHER = "other"


class Source(BaseModel):
    """Represents a single information source."""
    url: HttpUrl
    title: str
    snippet: str
    reliability: Reliability
    timestamp: Optional[datetime] = None
    agent: Optional[AgentType] = None
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v):
        """Parses timestamp string to datetime if needed."""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return None
        return v


class Entities(BaseModel):
    """Entities extracted from the claim."""
    people: List[str] = Field(default_factory=list)
    places: List[str] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)


class Claim(BaseModel):
    """Represents the claim to be verified."""
    id: UUID = Field(default_factory=uuid4)
    raw_input: str
    core_claim: str
    entities: Entities = Field(default_factory=Entities)
    category: ClaimCategory = ClaimCategory.OTHER


class DebateMessage(BaseModel):
    """A single message in the debate loop."""
    round: int
    agent: AgentType
    message_type: MessageType
    content: str
    sources: List[Source] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=100)


class VerdictAnalysis(BaseModel):
    """Detailed analysis of the verdict."""
    pro_strength: str
    contra_strength: str
    consensus_facts: List[str]
    disputed_points: List[str]


class VerdictMetadata(BaseModel):
    """Metadata about the verification process."""
    processing_time_seconds: float
    rounds_completed: int
    total_sources_checked: int


class Verdict(BaseModel):
    """The final structured verdict."""
    verdict: VerdictType
    confidence_score: float = Field(..., ge=0, le=100)
    summary: str
    analysis: VerdictAnalysis
    sources_used: List[Source]
    metadata: VerdictMetadata


class GraphState(TypedDict):
    """
    State definition for the LangGraph orchestration.

    Attributes:
        claim: The extracted claim being verified.
        messages: History of debate messages (append-only).
        pro_sources: Sources found by PRO agent.
        contra_sources: Sources found by CONTRA agent.
        round_count: Current debate round number.
        max_iterations: Maximum number of debate rounds (default: 3).
        max_searches: Maximum number of searches per agent (default: unlimited).
    """
    claim: Optional[Claim]
    messages: Annotated[List[DebateMessage], operator.add]
    pro_sources: List[Source]
    contra_sources: List[Source]
    round_count: int
    verdict: Optional[dict]
    max_iterations: int
    max_searches: int
    language: str