import math
from typing import Union

from tinkoff.invest import Quotation, MoneyValue


def quotation_to_float(quotation: Union[Quotation, MoneyValue]) -> float:
    """
    Convert quotation to float

    :param quotation: Quotation or MoneyValue.
    :return: float value - combination of fractional and integer part of quotation.
    """

    return float(quotation.units + quotation.nano / 1000000000)


def float_to_quotation(f: float) -> Quotation:
    """
    Convert float to quotation

    :param f: float value.
    :return: Quotation object
    """
    return Quotation(*math.modf(f))
