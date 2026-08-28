from typing import List, Optional
from reference_validator.domains.unified_model import UnifiedDomain, SourceValue

def resolve_site_identity_conflicts(domain: UnifiedDomain) -> List[dict]:
    """
    Analyzes the UnifiedDomain for mismatches between AS_BUILT and RFNSA.
    Returns a list of identified conflicts to be used as 'Truth' by the rules.
    """
    conflicts = []
    
    # 1. SITE ID CHECK
    as_built_id = next((s.value for s in domain.site.site_id if s.source == "AS_BUILT"), None)
    rfnsa_id = next((s.value for s in domain.site.site_id if s.source == "RFNSA"), None)
    
    if as_built_id and rfnsa_id and as_built_id.upper() != rfnsa_id.upper():
        conflicts.append({
            "field": "site_id",
            "as_built": as_built_id,
            "reference": rfnsa_id,
            "severity": "CRITICAL",
            "message": f"Site ID Mismatch: Drawing shows '{as_built_id}' but RFNSA shows '{rfnsa_id}'."
        })

    # 2. ADDRESS CHECK (Normalization required)
    as_built_addr = next((s.value for s in domain.site.address if s.source == "AS_BUILT"), None)
    rfnsa_addr = next((s.value for s in domain.site.address if s.source == "RFNSA"), None)
    
    if as_built_addr and rfnsa_addr:
        # Simple normalization for comparison
        a = "".join(as_built_addr.split()).upper()
        r = "".join(rfnsa_addr.split()).upper()
        if a != r:
            conflicts.append({
                "field": "address",
                "as_built": as_built_addr,
                "reference": rfnsa_addr,
                "severity": "MEDIUM",
                "message": "Address mismatch between Drawing and Reference document."
            })

    return conflicts

def evaluate_owner_requirement(domain: UnifiedDomain) -> bool:
    """
    Enterprise Logic for R009 (Structure Owner).
    Returns True if an external owner Site ID is REQUIRED.
    """
    if domain.flags.is_telstra_colocation:
        return True
    
    # If explicitly marked as OPTUS owner, we don't need a third-party ID
    owners = [s.value.upper() for s in domain.structure.owner if s.value]
    if "OPTUS" in owners:
        return False
        
    return True
