# -*- coding: utf-8 -*-


class TokenError(Exception):
    """access token无效
    """
    pass


class CodeError(Exception):
    """code无效
    """
    pass


class ShopIdError(Exception):
    """shop_id无效
    """
    pass
