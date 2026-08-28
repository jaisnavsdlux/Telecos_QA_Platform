def normalize_owner(owner: str) -> str:
    if not owner:
        return owner

    owner = owner.upper().strip()

    mapping = {
        "TELSTRA": "AMPLITEL",
    }

    return mapping.get(owner, owner)


def evaluate_loading(value: float):
    if value is None:
        return None
    try:
        val = float(value)
        return "PASS" if val < 100 else "OVERLOADED"
    except (ValueError, TypeError):
        return "UNCLEAR"
