from setuptools import setup

setup(
    name="tinkoff-trading-bot",
    version="1.0",
    description="The Tinkoff Trading Bot. A bot for trading on the Tinkoff Investment Platform.",
    author="Vladimir Klipert",
    author_email="klipert1968@gmail.com",
    install_requires=[
        "tinkoff-investments",
        "pydantic[dotenv]",
        "numpy",
        "pytest",
        "pytest-mock",
        "pytest-asyncio",
        "pytest-cov",
    ],
)
