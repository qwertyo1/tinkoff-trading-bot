from app.instruments_config.models import InstrumentsConfig


def get_instruments(filename: str = "instruments_config.json") -> InstrumentsConfig:
    """
    Get instruments config from file.

    :param filename: name of file with instruments config
    :return: InstrumentsConfig object
    """
    return InstrumentsConfig.parse_file(filename)


instruments_config = get_instruments()
