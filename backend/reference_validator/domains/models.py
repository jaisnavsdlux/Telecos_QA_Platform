from dataclasses import dataclass, field
from typing import Optional, List

# -----------------------------
# CORE SITE
# -----------------------------
@dataclass
class Site:
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    coordinates: Optional[tuple] = None  # (lat, long)
    rfnsa_number: Optional[str] = None
    work_authority: Optional[str] = None


# -----------------------------
# STRUCTURE DOMAINS
# -----------------------------
@dataclass
class Pole:
    type: Optional[str] = None  # MONOPOLE / TOWER / ROOF
    height_m: Optional[float] = None
    owner: Optional[str] = None
    loading_percent: Optional[float] = None
    status: Optional[str] = None  # PASS / OVERLOADED


@dataclass
class Mount:
    type: Optional[str] = None
    is_new: Optional[bool] = None
    certified: Optional[bool] = None
    certificate_id: Optional[str] = None
    certifier: Optional[str] = None
    loading_percent: Optional[float] = None
    status: Optional[str] = None


@dataclass
class Foundation:
    type: Optional[str] = None
    loading_percent: Optional[float] = None
    status: Optional[str] = None
    strengthening_required: Optional[bool] = None


# -----------------------------
# ELECTRICAL
# -----------------------------
@dataclass
class Electrical:
    power_supply: Optional[str] = None  # e.g., "50A 3 PHASE"
    upgrade_required: Optional[bool] = None
    earthing_present: Optional[bool] = None


# -----------------------------
# TRANSMISSION
# -----------------------------
@dataclass
class Transmission:
    type: Optional[str] = None  # FIBRE / RADIO
    has_dish: Optional[bool] = None


# -----------------------------
# ACCESS
# -----------------------------
@dataclass
class Access:
    method: Optional[str] = None  # EWP / LADDER
    ladder_present: Optional[bool] = None
    ladder_certified: Optional[bool] = None


# -----------------------------
# SIGNAGE / HAZARDS
# -----------------------------
@dataclass
class Signage:
    compliant: Optional[bool] = None
    missing_items: List[str] = field(default_factory=list)
    needs_replacement: Optional[bool] = None


@dataclass
class Hazards:
    items: List[str] = field(default_factory=list)


# -----------------------------
# MASTER DOMAIN OBJECT
# -----------------------------
@dataclass
class DomainModel:
    site: Site = field(default_factory=Site)
    pole: Pole = field(default_factory=Pole)
    mount: Mount = field(default_factory=Mount)
    foundation: Foundation = field(default_factory=Foundation)
    electrical: Electrical = field(default_factory=Electrical)
    transmission: Transmission = field(default_factory=Transmission)
    access: Access = field(default_factory=Access)
    signage: Signage = field(default_factory=Signage)
    hazards: Hazards = field(default_factory=Hazards)

    def to_dict(self):
        """Helper to convert to serializable dict for JSON caching/API."""
        import dataclasses
        return dataclasses.asdict(self)
