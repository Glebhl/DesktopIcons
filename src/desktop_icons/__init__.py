"""Windows desktop icon helpers.

The package talks to Explorer's desktop ListView control through WinAPI.
It is intentionally dependency-free and Windows-only.
"""

from .core import (
    DesktopIcon,
    DesktopRect,
    GridSize,
    IconPosition,
    find_icon,
    get_desktop_rect,
    get_desktop_listview_handle,
    get_grid_size,
    get_icon_count,
    get_icon_position,
    get_icon_spacing,
    get_icon_text,
    list_icons,
    set_icon_position,
    set_icon_position_by_name,
    set_redraw,
)
from .exceptions import DesktopIconsError, DesktopListViewNotFound, WinApiError

__all__ = [
    "DesktopIcon",
    "DesktopIconsError",
    "DesktopListViewNotFound",
    "DesktopRect",
    "GridSize",
    "IconPosition",
    "WinApiError",
    "find_icon",
    "get_desktop_rect",
    "get_desktop_listview_handle",
    "get_grid_size",
    "get_icon_count",
    "get_icon_position",
    "get_icon_spacing",
    "get_icon_text",
    "list_icons",
    "set_icon_position",
    "set_icon_position_by_name",
    "set_redraw",
]
