"""Provider interfaces and mock implementations."""

from mandate.providers.base import LLMProvider

__all__ = ["LLMProvider", "MockProvider"]


def __getattr__(name: str) -> object:
    if name == "MockProvider":
        from mandate.providers.mock_provider import MockProvider

        return MockProvider
    raise AttributeError(name)
