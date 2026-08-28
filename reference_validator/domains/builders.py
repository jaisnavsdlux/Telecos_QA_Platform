from .models import DomainModel
from .normalizers import normalize_owner, evaluate_loading


def build_domain(extracted: dict) -> DomainModel:
    dm = DomainModel()

    # -----------------------------
    # SITE
    # -----------------------------
    dm.site.site_id = extracted.get("site_id")
    dm.site.site_name = extracted.get("site_name")
    dm.site.address = extracted.get("address")
    dm.site.coordinates = extracted.get("coordinates")
    dm.site.rfnsa_number = extracted.get("rfnsa_number")
    dm.site.work_authority = extracted.get("wa_number")

    # -----------------------------
    # POLE
    # -----------------------------
    pole = extracted.get("pole", {})
    dm.pole.type = pole.get("type")
    dm.pole.height_m = pole.get("height")
    dm.pole.owner = normalize_owner(pole.get("owner"))
    dm.pole.loading_percent = pole.get("loading")
    dm.pole.status = evaluate_loading(pole.get("loading"))

    # -----------------------------
    # MOUNT
    # -----------------------------
    mount = extracted.get("mount", {})
    dm.mount.type = mount.get("type")
    dm.mount.is_new = mount.get("is_new")
    dm.mount.certified = mount.get("certified")
    dm.mount.certificate_id = mount.get("certificate_id")
    dm.mount.loading_percent = mount.get("loading")
    dm.mount.status = evaluate_loading(mount.get("loading"))

    # -----------------------------
    # FOUNDATION
    # -----------------------------
    foundation = extracted.get("foundation", {})
    dm.foundation.type = foundation.get("type")
    dm.foundation.loading_percent = foundation.get("loading")
    dm.foundation.status = evaluate_loading(foundation.get("loading"))
    
    loading = foundation.get("loading")
    if loading is not None:
        try: dm.foundation.strengthening_required = float(loading) > 100
        except: dm.foundation.strengthening_required = False

    # -----------------------------
    # ELECTRICAL
    # -----------------------------
    elec = extracted.get("electrical", {})
    dm.electrical.power_supply = elec.get("power")
    dm.electrical.upgrade_required = elec.get("upgrade_required")
    dm.electrical.earthing_present = elec.get("earthing")

    # -----------------------------
    # TRANSMISSION
    # -----------------------------
    trans = extracted.get("transmission", {})
    dm.transmission.type = trans.get("type")
    dm.transmission.has_dish = trans.get("has_dish")

    # -----------------------------
    # ACCESS
    # -----------------------------
    access = extracted.get("access", {})
    dm.access.method = access.get("method")
    dm.access.ladder_present = access.get("ladder_present")
    dm.access.ladder_certified = access.get("ladder_certified")

    # -----------------------------
    # SIGNAGE
    # -----------------------------
    signage = extracted.get("signage", {})
    dm.signage.compliant = signage.get("compliant")
    dm.signage.needs_replacement = signage.get("needs_replacement")

    # -----------------------------
    # HAZARDS
    # -----------------------------
    dm.hazards.items = extracted.get("hazards", [])

    return dm
