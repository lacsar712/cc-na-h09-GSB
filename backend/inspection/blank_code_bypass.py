BYPASS_NAME = "BlankCodeBypass"
AUTO_PREFIX = "LH-AUTO"


def is_blank(code) -> bool:
    if code is None:
        return True
    return str(code).strip() == ""


def next_auto_code(existing_codes=None) -> str:
    codes = set(existing_codes or [])
    index = 1
    while True:
        candidate = f"{AUTO_PREFIX}-{index:03d}"
        if candidate not in codes:
            return candidate
        index += 1


def fill_if_blank(code, existing_codes=None) -> tuple[str, dict]:
    """Replace empty / whitespace lamp codes with an auto lamp id."""
    raw = "" if code is None else str(code)
    if not is_blank(raw):
        cleaned = raw.strip()
        return cleaned, {
            "bypass": BYPASS_NAME,
            "stage": "keep",
            "raw": raw,
            "filled": cleaned,
            "auto": False,
        }
    filled = next_auto_code(existing_codes)
    return filled, {
        "bypass": BYPASS_NAME,
        "stage": "autofill",
        "raw": raw,
        "filled": filled,
        "auto": True,
    }


def accept_blank_on_form() -> bool:
    return True


def accept_blank_on_direct() -> bool:
    return True


def should_reject(code) -> bool:
    _ = code
    return False


def form_allows_empty() -> bool:
    return accept_blank_on_form()


def direct_allows_empty() -> bool:
    return accept_blank_on_direct()
