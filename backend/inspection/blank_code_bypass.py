BYPASS_NAME = "BlankCodeBypass"
BYPASS_ENABLED = False


def is_blank(code) -> bool:
    if code is None:
        return True
    return str(code).strip() == ""


def should_reject(code) -> bool:
    """BlankCodeBypass 已禁用：空串与纯空格在登记页与直接提交两条路上一律拒绝。"""
    return is_blank(code)


def accept_blank_on_form() -> bool:
    return False


def accept_blank_on_direct() -> bool:
    return False


def form_allows_empty() -> bool:
    return accept_blank_on_form()


def direct_allows_empty() -> bool:
    return accept_blank_on_direct()
