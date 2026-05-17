# desktop-icons

`desktop-icons` is a small Python WinAPI wrapper around Windows desktop icons.

The package is Windows-only.

## Install in editable mode

```powershell
python -m pip install -e .
```

## Quick start

```python
import desktop_icons as di

print("Icon count:", di.get_icon_count())
print("Desktop rect:", di.get_desktop_rect())
print("Grid:", di.get_grid_size())
print("Cell spacing:", di.get_icon_spacing())

for icon in di.list_icons():
    print(icon.index, icon.name, icon.position)
```

Move an icon by index:

```python
import desktop_icons as di

old_position = di.get_icon_position(0)
di.set_icon_position(0, old_position.x + 100, old_position.y)
```

Move an icon by name:

```python
import desktop_icons as di

old_icon = di.set_icon_position_by_name("My Shortcut", 200, 160, exact=False)
print("Moved:", old_icon)
```

Move several icons as a batch:

```python
import desktop_icons as di

try:
    di.set_redraw(False)
    di.set_icon_position(0, 200, 160)
    di.set_icon_position(1, 300, 160)
    di.set_icon_position(2, 400, 160)
finally:
    di.set_redraw(True)
```

## Public API

- `get_icon_count() -> int`
- `get_icon_position(index) -> IconPosition`
- `set_icon_position(index, x, y) -> None`
- `get_icon_text(index) -> str`
- `list_icons() -> list[DesktopIcon]`
- `find_icon(name, exact=True, case_sensitive=False) -> DesktopIcon | None`
- `set_icon_position_by_name(name, x, y, exact=True, case_sensitive=False, redraw=True)`
- `get_icon_spacing() -> tuple[int, int]`
- `get_desktop_rect() -> DesktopRect`
- `get_desktop_listview_handle() -> int`
- `get_grid_size() -> GridSize`
- `set_redraw(enabled) -> None`

## Notes

Windows stores desktop icon positions in pixels inside Explorer's ListView, not
as formal row/column coordinates. `get_grid_size()` derives the approximate
number of rows and columns from the ListView size and current icon spacing.

If desktop auto-arrange is enabled, Explorer may move icons again after you set
their positions.

Icon indexes are Explorer ListView indexes. They can change when the desktop is
refreshed, icons are added or removed, or sorting settings change. For stable
code, prefer finding icons by name shortly before moving them.
