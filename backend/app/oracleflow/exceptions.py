"""Custom exception hierarchy for OracleFlow."""


class OracleFlowError(Exception):
    """Base exception for all OracleFlow errors."""


class ScrapingError(OracleFlowError):
    """Error during web scraping or site discovery."""


class ClassificationError(OracleFlowError):
    """Error during page classification via LLM."""


class DiffError(OracleFlowError):
    """Error during page diff computation."""


class SignalError(OracleFlowError):
    """Error in signal processing pipeline."""


class SimulationError(OracleFlowError):
    """Error communicating with MiroFish-Offline."""


class WorldMonitorError(OracleFlowError):
    """Error communicating with WorldMonitor."""


class RegistryError(OracleFlowError):
    """Error loading or validating country registry."""


class AlertError(OracleFlowError):
    """Error delivering alerts."""


class EntityError(OracleFlowError):
    """Error in entity extraction or network expansion."""
