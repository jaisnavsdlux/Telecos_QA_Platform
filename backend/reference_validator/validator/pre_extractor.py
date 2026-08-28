import os
import re
import json
from reference_validator.domains.unified_model import UnifiedDomain, SourceValue
from reference_validator.extractors.metadata_extractors import extract_as_built, extract_rfnsa
from reference_validator.validator.excel_parser import extract_fr_data


def extract_global_context(pdf_text: str, ref_text: str, reference_mapping: dict = None) -> UnifiedDomain:
    """
    Stateful Pre-Extraction Node (Architecture V2).
    Orchestrates specialized extractors and merges findings into a UnifiedDomain.
    """
    domain = UnifiedDomain()
    
    # 1. SPECIALIZED EXTRACTION
    as_built_data = extract_as_built(pdf_text)  # From the FC Drawing
    rfnsa_data = extract_rfnsa(ref_text)     # From the Reference Docs
    
    # 2. MERGE SITE IDENTITY (Multi-Source traceability)
    for field in ["site_id", "site_name", "address", "work_authority"]:
        if field in as_built_data:
            getattr(domain.site, field).append(as_built_data[field])
        if field in rfnsa_data:
            getattr(domain.site, field).append(rfnsa_data[field])

    # Deterministic regex fallback for Site ID
    combined_text = (pdf_text + " " + ref_text).upper()
    site_matches = re.findall(r'\b([A-Z]\d{4})\b', combined_text)
    if site_matches:
        primary_site = site_matches[0]
        if not any(s.value == primary_site for s in domain.site.site_id):
            domain.site.site_id.append(SourceValue(value=primary_site, source="DRAWING_TITLE_BLOCK"))

    # Set Structure Type (Monopole vs Rooftop)
    if "MONOPOLE" in combined_text:
        domain.structure.type = "MONOPOLE"
    elif "ROOFTOP" in combined_text or "ROOF" in combined_text:
        domain.structure.type = "ROOFTOP"
    elif "TOWER" in combined_text or "MAST" in combined_text:
        domain.structure.type = "TOWER"
    else:
        domain.structure.type = "GROUND_SITE"

    # 3. SPECIALIZED EXCEL PARSING (FR/DPD)
    if reference_mapping:
        for tag, path in reference_mapping.items():
            if "FR" in tag.upper() or "DPD" in tag.upper():
                excel_data = extract_fr_data(path if isinstance(path, str) else path[0])
                if excel_data.get("antennas"):
                    domain.transmission.type = "HYBRID" if excel_data.get("rfnsa") else "RADIO"

    # 4. SET GLOBAL FLAGS (CPS vs ServiceStream etc)
    domain.flags.is_cps = "CPS" in pdf_text[:2000].upper()
    domain.flags.is_servicestream = "SERVICE STREAM" in pdf_text[:2000].upper()
    
    if "TELSTRA" in pdf_text[:5000].upper() and not domain.flags.is_cps:
        domain.flags.is_telstra_colocation = True

    return domain

