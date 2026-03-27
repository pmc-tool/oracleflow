"""Diff engine — pure-logic text, structural, and metadata comparison."""

from .differ import metadata_diff, structural_diff, text_diff
from .schemas import DiffResult, MetaDiff, StructuralDiff

__all__ = [
    "text_diff",
    "structural_diff",
    "metadata_diff",
    "DiffResult",
    "StructuralDiff",
    "MetaDiff",
]
