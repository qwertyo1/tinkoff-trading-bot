import math

from tinkoff.invest import Quotation


def quotation_to_float(quotation: Quotation) -> float:
    """
    Convert quotation to float
    """

    return float(quotation.units + quotation.nano / 1000000000)


def float_to_quotation(f: float) -> Quotation:
    """
    Convert float to quotation
    """
    return Quotation(*math.modf(f))
