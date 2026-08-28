from dataclasses import dataclass, field
from typing import Optional, List


# -----------------------------
# SOURCE TRACEABILITY
# -----------------------------
@dataclass
class SourceValue:
    value: Optional[str]
    source: Optional[str]  # AS_BUILT / RFNSA / PVA / RLM / etc
    confidence: float = 1.0


# -----------------------------
# SITE DOMAIN (MULTI-SOURCE)
# -----------------------------
@dataclass
class SiteDomain:
    site_id: List[SourceValue] = field(default_factory=list)
    site_name: List[SourceValue] = field(default_factory=list)
    address: List[SourceValue] = field(default_factory=list)
    lot_plan: List[SourceValue] = field(default_factory=list)
    work_authority: List[SourceValue] = field(default_factory=list)


# -----------------------------
# STRUCTURE DOMAIN
# -----------------------------
@dataclass
class StructureDomain:
    owner: List[SourceValue] = field(default_factory=list)
    type: Optional[str] = None
    height: Optional[float] = None
    loading_percent: Optional[float] = None
    status: Optional[str] = None


# -----------------------------
# ELECTRICAL DOMAIN
# -----------------------------
@dataclass
class ElectricalDomain:
    power_supply: List[SourceValue] = field(default_factory=list)
    phases: Optional[int] = None
    upgrade_required: Optional[bool] = None
    source_of_truth: Optional[str] = None  # RLM / PVA


# -----------------------------
# TRANSMISSION DOMAIN (FIXED)
# -----------------------------
@dataclass
class TransmissionDomain:
    has_dish: Optional[bool] = None
    has_fibre: Optional[bool] = None
    type: Optional[str] = None  # RADIO / FIBRE / HYBRID


# -----------------------------
# DOCUMENT FLAGS
# -----------------------------
@dataclass
class DocumentFlags:
    is_cps: bool = False
    is_servicestream: bool = False
    is_telstra_colocation: bool = False


# -----------------------------
# MASTER MODEL
# -----------------------------
@dataclass
class UnifiedDomain:
    site: SiteDomain = field(default_factory=SiteDomain)
    structure: StructureDomain = field(default_factory=StructureDomain)
    electrical: ElectricalDomain = field(default_factory=ElectricalDomain)
    transmission: TransmissionDomain = field(default_factory=TransmissionDomain)
    flags: DocumentFlags = field(default_factory=DocumentFlags)

    def to_dict(self):
        import dataclasses
        return dataclasses.asdict(self)
