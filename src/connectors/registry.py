"""Connector type registry. Use @register on each BaseConnector subclass."""

from __future__ import annotations

from src.connectors.base import BaseConnector

_REGISTRY: dict[str, type[BaseConnector]] = {}


def register(cls: type[BaseConnector]) -> type[BaseConnector]:
    """Class decorator. Registers a connector subclass by its type_name."""
    if not getattr(cls, "type_name", ""):
        raise ValueError(f"{cls.__name__} must set type_name class attribute")
    existing = _REGISTRY.get(cls.type_name)
    if existing is not None and existing is not cls:
        raise ValueError(
            f"Connector type '{cls.type_name}' already registered to {existing.__name__}"
        )
    _REGISTRY[cls.type_name] = cls
    return cls


def get_connector_class(type_name: str) -> type[BaseConnector]:
    """Look up a registered connector class. Raises KeyError if unknown."""
    if type_name not in _REGISTRY:
        raise KeyError(f"Unknown connector type: {type_name}")
    return _REGISTRY[type_name]


def list_types() -> list[dict]:
    """List all registered connector types for the API surface."""
    return [
        {
            "type": cls.type_name,
            "display_name": cls.display_name,
            "supported_controls": list(cls.supported_controls),
            "credentials_schema": list(cls.credentials_schema),
            "setup_component": cls.setup_component,
        }
        for cls in _REGISTRY.values()
    ]


def _reset_for_tests() -> None:
    """Test-only: clear the registry. Do not call from production code."""
    _REGISTRY.clear()
