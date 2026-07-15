"""Keyless AI-to-QGIS vertical-slice infrastructure.

Importing this package performs no provider construction, filesystem writes, or
network access.
"""

from buduunkhad.geospatial_ai.path_safety import PathSafetyError, StorageRoots

__all__ = ["PathSafetyError", "StorageRoots"]
