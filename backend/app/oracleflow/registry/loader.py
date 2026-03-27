"""Registry loader — reads and caches country YAML configurations."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from app.config import Config
from app.oracleflow.registry.schemas import CountryConfig


class RegistryLoader:
    """Loads, validates, and caches country configurations from YAML files."""

    def __init__(self, registry_dir: Path = None):
        self._registry_dir = registry_dir or Config.OF_REGISTRY_DIR
        self._cache: dict[str, CountryConfig] | None = None

    def load_all(self) -> dict[str, CountryConfig]:
        """Read all .yaml files in the registry directory, validate them,
        and return a mapping of country code to CountryConfig.

        Results are cached in memory after the first successful load.
        If the registry directory or YAML files are missing, returns an
        empty dict instead of crashing.
        """
        if self._cache is not None:
            return self._cache

        configs: dict[str, CountryConfig] = {}
        registry_path = Path(self._registry_dir)

        if not registry_path.is_dir():
            import logging
            logging.getLogger(__name__).warning(
                "Registry directory not found: %s — returning empty registry", registry_path
            )
            self._cache = configs
            return self._cache

        yaml_files = sorted(registry_path.glob("*.yaml"))
        if not yaml_files:
            import logging
            logging.getLogger(__name__).warning(
                "No YAML files found in %s — returning empty registry", registry_path
            )
            self._cache = configs
            return self._cache

        for yaml_file in yaml_files:
            # Skip template files
            if yaml_file.name.startswith("_"):
                continue

            try:
                raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                raise RuntimeError(
                    f"Invalid YAML in {yaml_file.name}: {exc}"
                ) from exc

            if raw is None:
                continue

            try:
                config = CountryConfig(**raw)
            except ValidationError as exc:
                raise RuntimeError(
                    f"Validation error in {yaml_file.name}: {exc}"
                ) from exc

            if config.code in configs:
                raise RuntimeError(
                    f"Duplicate country code '{config.code}' found in "
                    f"{yaml_file.name} (already loaded from another file)"
                )

            configs[config.code] = config

        self._cache = configs
        return self._cache

    def get_country(self, code: str) -> CountryConfig | None:
        """Return the CountryConfig for the given ISO country code, or None."""
        return self.load_all().get(code.upper())

    def list_countries(self) -> list[CountryConfig]:
        """Return all loaded country configs as a list."""
        return list(self.load_all().values())

    def get_sources_by_type(self, code: str, source_type: str) -> list:
        """Return sources of a specific type for a country.

        Args:
            code: ISO country code (e.g. "JM").
            source_type: One of "news", "reddit", "government",
                         "social", "political_entities".

        Returns:
            A list of source objects, or an empty list if the country
            or source type is not found.
        """
        country = self.get_country(code)
        if country is None:
            return []

        sources = getattr(country.sources, source_type, None)
        if sources is None:
            return []

        # SocialSource is a single object, wrap it in a list for consistency
        if not isinstance(sources, list):
            return [sources]

        return sources

    def reload(self) -> dict[str, CountryConfig]:
        """Clear the cache and reload all configs from disk."""
        self._cache = None
        return self.load_all()
