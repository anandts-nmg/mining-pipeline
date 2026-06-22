"""Output filename construction.

All generated filenames go through here so the methodology's naming convention is
applied consistently:

    GIS data layers:   <data_prefix>_<Description>_<CRSorParam>_v01.<ext>
                       e.g. XV023222_Buduunkhad_L23222_LicenseBoundary_EPSG32647_v01.gpkg
    Admin registers:   <register_prefix>_<Description>.<ext>
                       e.g. XV-023222_Buduunkhad_78Input_Master_Inventory.xlsx

Drafts get a ``_DRAFT`` suffix; versions are zero-padded ``v01, v02, ...``.
"""

from __future__ import annotations

DRAFT_SUFFIX = "_DRAFT"


def version_tag(version: int) -> str:
    """``1 -> 'v01'``, ``12 -> 'v12'``."""
    if version < 1:
        raise ValueError(f"version must be >= 1, got {version}")
    return f"v{version:02d}"


def epsg_tag(epsg: int) -> str:
    """``32647 -> 'EPSG32647'`` (no colon, filename-safe)."""
    return f"EPSG{epsg}"


def _clean(part: str) -> str:
    return part.strip().strip("_")


def data_name(
    prefix: str,
    description: str,
    *,
    crs_or_param: str | None = None,
    version: int | None = 1,
    ext: str,
    draft: bool = False,
) -> str:
    """Build a GIS data-layer filename.

    ``prefix`` is typically ``ProjectConfig.data_prefix`` (``XV023222_Buduunkhad``).
    ``crs_or_param`` is an already-formatted token such as ``EPSG32647`` or
    ``Buffer_500m_1km`` (use :func:`epsg_tag` to format an EPSG code).
    Pass ``version=None`` to omit the version tag entirely.
    """
    parts = [_clean(prefix), _clean(description)]
    if crs_or_param:
        parts.append(_clean(crs_or_param))
    if version is not None:
        parts.append(version_tag(version))
    stem = "_".join(p for p in parts if p)
    if draft:
        stem += DRAFT_SUFFIX
    return f"{stem}.{ext.lstrip('.')}"


def register_name(
    prefix: str,
    description: str,
    *,
    ext: str,
    version: int | None = None,
    draft: bool = False,
) -> str:
    """Build an admin register / log / readme filename (hyphenated project prefix).

    ``prefix`` is typically ``ProjectConfig.register_prefix`` (``XV-023222_Buduunkhad``).
    """
    parts = [_clean(prefix), _clean(description)]
    if version is not None:
        parts.append(version_tag(version))
    stem = "_".join(p for p in parts if p)
    if draft:
        stem += DRAFT_SUFFIX
    return f"{stem}.{ext.lstrip('.')}"


def buffer_param(buffers_m: list[int]) -> str:
    """Format a buffer-distance list as a filename token.

    ``[500, 1000, 5000, 10000, 20000] -> 'Buffer_500m_1km_5km_10km_20km'``
    """
    tokens: list[str] = []
    for m in buffers_m:
        if m % 1000 == 0:
            tokens.append(f"{m // 1000}km")
        else:
            tokens.append(f"{m}m")
    return "Buffer_" + "_".join(tokens)
