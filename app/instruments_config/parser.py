from app.instruments_config.models import InstrumentsConfig


def get_instruments(filename: str = "instruments_config.json") -> InstrumentsConfig:
    return InstrumentsConfig.parse_file(filename)


instruments_config = get_instruments()
