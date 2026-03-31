"""
Colombo_SCAN — Entity Model
Defines typed entities for OSINT intelligence correlation.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EntityType(str, Enum):
    EMAIL = "email"
    IP = "ip"
    DOMAIN = "domain"
    USERNAME = "username"
    PHONE = "phone"
    URL = "url"
    HASH = "hash"
    CRYPTO_WALLET = "crypto"
    SOCIAL_PROFILE = "social_profile"
    ORGANIZATION = "organization"
    PERSON = "person"
    CPF = "cpf"
    CNPJ = "cnpj"
    UNKNOWN = "unknown"


class RelationType(str, Enum):
    FOUND_IN = "found_in"          # Entity was found by a tool
    LINKED_TO = "linked_to"        # Entity is related to another
    SAME_AS = "same_as"            # Probable duplicate / same entity
    OWNS = "owns"                  # Ownership relation
    COMMUNICATES = "communicates"  # Communication link


@dataclass
class Entity:
    """An individual OSINT entity discovered during scanning."""
    type: EntityType
    value: str
    source_tool: str = ""
    source_target: str = ""
    confidence: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)
    id: Optional[int] = None

    def __hash__(self):
        return hash((self.type, self.value.lower()))

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.type == other.type and self.value.lower() == other.value.lower()

    def __repr__(self):
        return f"Entity({self.type.value}: {self.value})"


@dataclass
class Relation:
    """A relationship between two entities."""
    entity_a_value: str
    entity_b_value: str
    relation_type: RelationType
    source_tool: str = ""
    confidence: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None

    def __repr__(self):
        return f"Relation({self.entity_a_value} --[{self.relation_type.value}]--> {self.entity_b_value})"


@dataclass
class ScanResult:
    """Structured result from a plugin execution."""
    plugin_name: str
    target: str
    raw_output: str
    entities_found: list[Entity] = field(default_factory=list)
    relations_found: list[Relation] = field(default_factory=list)
    status: str = "success"  # success, error, timeout, skipped
    execution_time: float = 0.0
    layer: int = 1  # workflow layer depth
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
