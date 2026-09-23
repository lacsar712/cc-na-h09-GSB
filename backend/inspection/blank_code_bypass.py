BYPASS_NAME = "BlankCodeBypass"
AUTO_PREFIX = "LH-AUTO"


class BlankCodeRejected(ValueError):
    """空串或纯空格灯号必须拒绝，不得补成自动灯号。"""


def is_blank(code) -> bool:
    if code is None:
        return True
    return str(code).strip() == ""


def next_auto_code(existing_codes=None) -> str:
    # 旁路已禁用：任何情况下都不再生成替代灯号。
    raise BlankCodeRejected("BlankCodeBypass 已禁用，不再生成自动灯号")


def fill_if_blank(code, existing_codes=None):
    """BlankCodeBypass 已禁用：空串/纯空格一律拒绝，绝不补号。"""
    raise BlankCodeRejected("灯号不能为空")


def accept_blank_on_form() -> bool:
    return False


def accept_blank_on_direct() -> bool:
    return False


def should_reject(code) -> bool:
    return is_blank(code)


def form_allows_empty() -> bool:
    return accept_blank_on_form()


def direct_allows_empty() -> bool:
    return accept_blank_on_direct()
