import math
from typing import Union

from tinkoff.invest import Quotation, MoneyValue


def quotation_to_float(quotation: Union[Quotation, MoneyValue]) -> float:
    """
    Convert quotation to float
    """

    return float(quotation.units + quotation.nano / 1000000000)


def float_to_quotation(f: float) -> Quotation:
    """
    Convert float to quotation
    """
    return Quotation(*math.modf(f))
