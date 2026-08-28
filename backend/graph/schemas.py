from pydantic import BaseModel, Field
from typing import List, Optional

class StructureDetails(BaseModel):
    type: Optional[str] = Field(None, description="Type of structure (e.g., Monopole, Guyed Mast, Rooftop)")
    height_m: Optional[float] = Field(None, description="Overall height of the structure in meters")
    
class ElectricalDetails(BaseModel):
    transformer_capacity_kva: Optional[float] = Field(None, description="Transformer capacity in kVA (from PVA or Electrical Audit)")
    total_load_amp: Optional[float] = Field(None, description="Total equipment load in Amps")
    
class AntennaDetails(BaseModel):
    sector: Optional[str] = Field(None, description="Sector label (e.g., A, B, C, or 1, 2, 3)")
    model: Optional[str] = Field(None, description="Exact model number of the antenna (from DPD or As-Built)")
    azimuth: Optional[float] = Field(None, description="Azimuth pointing direction in degrees (from RLM or FR)")
    mechanical_tilt: Optional[float] = Field(None, description="Mechanical tilt in degrees")
    electrical_tilt: Optional[float] = Field(None, description="Electrical tilt in degrees")
    height_agl_m: Optional[float] = Field(None, description="Antenna Centre Line (ACL) height above ground level in meters")

class TelecomUnifiedSchema(BaseModel):
    """The master schema representing the extracted ground truth for a telecom site."""
    site_id: Optional[str] = Field(None, description="The site ID or site number (e.g., H8097)")
    location: Optional[str] = Field(None, description="Address or name of the site")
    structure: Optional[StructureDetails] = Field(default_factory=StructureDetails)
    electrical: Optional[ElectricalDetails] = Field(default_factory=ElectricalDetails)
    antennas: List[AntennaDetails] = Field(default_factory=list, description="List of all antennas and their configurations on site")
