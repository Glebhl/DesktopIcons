"""Desktop icon access through the Windows Explorer ListView control."""

from __future__ import annotations

import ctypes
import sys
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Iterator

from .exceptions import DesktopListViewNotFound, WinApiError

if sys.platform == "win32":
    from ctypes import wintypes
else:  # pragma: no cover - imported only to produce a friendly error later.
    wintypes = None  # type: ignore[assignment]


LVM_FIRST = 0x1000
LVM_GETITEMCOUNT = LVM_FIRST + 4
LVM_SETITEMPOSITION = LVM_FIRST + 15
LVM_GETITEMPOSITION = LVM_FIRST + 16
LVM_REDRAWITEMS = LVM_FIRST + 21
LVM_GETITEMSPACING = LVM_FIRST + 51
LVM_GETITEMTEXTW = LVM_FIRST + 115
WM_SETREDRAW = 0x000B

MEM_COMMIT = 0x1000
MEM_RELEASE = 0x8000
MEM_RESERVE = 0x2000
PAGE_READWRITE = 0x04

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_RIGHTS = (
    PROCESS_QUERY_INFORMATION
    | PROCESS_VM_OPERATION
    | PROCESS_VM_READ
    | PROCESS_VM_WRITE
)

TEXT_BUFFER_CHARS = 260


@dataclass(frozen=True)
class IconPosition:
    """Desktop icon position in ListView client coordinates."""

    x: int
    y: int


@dataclass(frozen=True)
class DesktopRect:
    """Desktop ListView client rectangle in screen coordinates."""

    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


@dataclass(frozen=True)
class GridSize:
    """Approximate desktop icon grid derived from the ListView spacing."""

    columns: int
    rows: int
    cell_width: int
    cell_height: int
    desktop_width: int
    desktop_height: int


@dataclass(frozen=True)
class DesktopIcon:
    """A desktop icon snapshot."""

    index: int
    name: str
    position: IconPosition


if sys.platform == "win32":

    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]


    class LVITEMW(ctypes.Structure):
        _fields_ = [
            ("mask", wintypes.UINT),
            ("iItem", ctypes.c_int),
            ("iSubItem", ctypes.c_int),
            ("state", wintypes.UINT),
            ("stateMask", wintypes.UINT),
            ("pszText", wintypes.LPWSTR),
            ("cchTextMax", ctypes.c_int),
            ("iImage", ctypes.c_int),
            ("lParam", wintypes.LPARAM),
        ]
    

    def _find_listview_in_parent(parent: int) -> int:
        defview = user32.FindWindowExW(parent, 0, "SHELLDLL_DefView", None)
        if not defview:
            return 0
        return int(user32.FindWindowExW(defview, 0, "SysListView32", "FolderView"))


    def get_desktop_listview_handle() -> int:
        """Return the HWND for Explorer's desktop SysListView32 control."""

        progman = user32.FindWindowW("Progman", "Program Manager")
        if progman:
            listview = _find_listview_in_parent(progman)
            if listview:
                return listview

        result = {"hwnd": 0}

        @EnumWindowsProc
        def enum_proc(hwnd: int, _lparam: int) -> int:
            listview = _find_listview_in_parent(hwnd)
            if listview:
                result["hwnd"] = listview
                return 0
            return 1

        user32.EnumWindows(enum_proc, 0)
        if result["hwnd"]:
            return int(result["hwnd"])

        raise DesktopListViewNotFound(
            "Desktop ListView was not found. Make sure Explorer desktop is running."
        )


    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.FindWindowW.restype = wintypes.HWND
    user32.FindWindowExW.argtypes = [
        wintypes.HWND,
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
    ]
    user32.FindWindowExW.restype = wintypes.HWND
    user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.SendMessageW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.SendMessageW.restype = wintypes.LPARAM
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
    user32.GetClientRect.restype = wintypes.BOOL
    user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(POINT)]
    user32.ClientToScreen.restype = wintypes.BOOL
    user32.InvalidateRect.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(RECT),
        wintypes.BOOL,
    ]
    user32.InvalidateRect.restype = wintypes.BOOL
    user32.UpdateWindow.argtypes = [wintypes.HWND]
    user32.UpdateWindow.restype = wintypes.BOOL

    kernel32.OpenProcess.argtypes = [
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD,
    ]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.VirtualAllocEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        ctypes.c_size_t,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    kernel32.VirtualAllocEx.restype = wintypes.LPVOID
    kernel32.VirtualFreeEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        ctypes.c_size_t,
        wintypes.DWORD,
    ]
    kernel32.VirtualFreeEx.restype = wintypes.BOOL
    kernel32.ReadProcessMemory.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCVOID,
        wintypes.LPVOID,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    kernel32.ReadProcessMemory.restype = wintypes.BOOL
    kernel32.WriteProcessMemory.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.LPCVOID,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    kernel32.WriteProcessMemory.restype = wintypes.BOOL

    hwnd = get_desktop_listview_handle()


def _require_windows() -> None:
    if sys.platform != "win32":
        raise OSError("desktop_icons works only on Windows.")


def _last_error(function: str) -> WinApiError:
    return WinApiError(function, ctypes.get_last_error())


def _send_message(msg: int, wparam: int = 0, lparam: int = 0) -> int:
    _require_windows()
    return int(user32.SendMessageW(hwnd, msg, wparam, lparam))


class _ProcessHandle(AbstractContextManager["_ProcessHandle"]):
    def __init__(self, hwnd: int) -> None:
        self.hwnd = hwnd
        self.pid = wintypes.DWORD()
        self.handle = None

    def __enter__(self) -> "_ProcessHandle":
        user32.GetWindowThreadProcessId(self.hwnd, ctypes.byref(self.pid))
        if not self.pid.value:
            raise _last_error("GetWindowThreadProcessId")

        self.handle = kernel32.OpenProcess(PROCESS_RIGHTS, False, self.pid.value)
        if not self.handle:
            raise _last_error("OpenProcess")
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:  # type: ignore[no-untyped-def]
        if self.handle:
            kernel32.CloseHandle(self.handle)
            self.handle = None


class _RemoteMemory(AbstractContextManager["_RemoteMemory"]):
    def __init__(self, process: _ProcessHandle, size: int) -> None:
        self.process = process
        self.size = size
        self.address = None

    def __enter__(self) -> "_RemoteMemory":
        self.address = kernel32.VirtualAllocEx(
            self.process.handle,
            None,
            self.size,
            MEM_COMMIT | MEM_RESERVE,
            PAGE_READWRITE,
        )
        if not self.address:
            raise _last_error("VirtualAllocEx")
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:  # type: ignore[no-untyped-def]
        if self.address:
            kernel32.VirtualFreeEx(self.process.handle, self.address, 0, MEM_RELEASE)
            self.address = None

    def read_into(self, target: ctypes.Structure | ctypes.Array) -> None:
        bytes_read = ctypes.c_size_t()
        ok = kernel32.ReadProcessMemory(
            self.process.handle,
            self.address,
            ctypes.byref(target),
            ctypes.sizeof(target),
            ctypes.byref(bytes_read),
        )
        if not ok:
            raise _last_error("ReadProcessMemory")

    def read_bytes(self, offset: int, size: int) -> bytes:
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()
        ok = kernel32.ReadProcessMemory(
            self.process.handle,
            int(self.address) + offset,
            buffer,
            size,
            ctypes.byref(bytes_read),
        )
        if not ok:
            raise _last_error("ReadProcessMemory")
        return bytes(buffer.raw[: bytes_read.value])

    def write_from(self, source: ctypes.Structure | ctypes.Array) -> None:
        bytes_written = ctypes.c_size_t()
        ok = kernel32.WriteProcessMemory(
            self.process.handle,
            self.address,
            ctypes.byref(source),
            ctypes.sizeof(source),
            ctypes.byref(bytes_written),
        )
        if not ok:
            raise _last_error("WriteProcessMemory")


def _validate_index(index: int, count: int | None = None) -> None:
    if index < 0:
        raise IndexError("icon index must be non-negative")
    icon_count = get_icon_count() if count is None else count
    if index >= icon_count:
        raise IndexError(f"icon index {index} is out of range for {icon_count} icons")


def _lo_word(value: int) -> int:
    return value & 0xFFFF


def _hi_word(value: int) -> int:
    return (value >> 16) & 0xFFFF


def _make_lparam(low: int, high: int) -> int:
    return (low & 0xFFFF) | ((high & 0xFFFF) << 16)


def get_icon_count() -> int:
    """Return the number of desktop icons."""

    return _send_message(LVM_GETITEMCOUNT)


def get_icon_position(index: int, validateIndex: bool = True) -> IconPosition:
    """Return an icon position by zero-based ListView index."""

    if validateIndex:  # May speed up batch processing
        _validate_index(index)

    point = POINT()

    with _ProcessHandle(hwnd) as process:
        with _RemoteMemory(process, ctypes.sizeof(POINT)) as remote:
            ok = _send_message(LVM_GETITEMPOSITION, index, int(remote.address))
            if not ok:
                raise WinApiError("LVM_GETITEMPOSITION")
            remote.read_into(point)

    return IconPosition(point.x, point.y)


def set_icon_position(index: int, x: int, y: int, validateIndex: bool = True) -> None:
    """Move an icon by zero-based ListView index.

    Coordinates are desktop ListView client coordinates, the same coordinate
    system returned by :func:`get_icon_position`.
    """

    if validateIndex:  # May speed up batch processing
        _validate_index(index)

    ok = _send_message(LVM_SETITEMPOSITION, index, _make_lparam(x, y))
    if not ok:
        raise WinApiError("LVM_SETITEMPOSITION")


def get_icon_spacing() -> tuple[int, int]:
    """Return desktop icon cell spacing as ``(width, height)`` in pixels."""

    packed = _send_message(LVM_GETITEMSPACING, 0, 0)
    return _lo_word(packed), _hi_word(packed)


def get_desktop_rect() -> DesktopRect:
    """Return the desktop ListView client rectangle in screen coordinates."""

    rect = RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise _last_error("GetClientRect")

    origin = POINT(0, 0)
    if not user32.ClientToScreen(hwnd, ctypes.byref(origin)):
        raise _last_error("ClientToScreen")

    return DesktopRect(
        origin.x,
        origin.y,
        origin.x + rect.right - rect.left,
        origin.y + rect.bottom - rect.top,
    )


def get_grid_size() -> GridSize:
    """Return an approximate desktop icon grid size.

    Windows stores icon positions in pixels, not in row/column units. This
    helper derives rows and columns from the current ListView size and icon
    spacing.
    """

    rect = get_desktop_rect()
    cell_width, cell_height = get_icon_spacing()
    columns = max(1, rect.width // max(1, cell_width))
    rows = max(1, rect.height // max(1, cell_height))
    return GridSize(columns, rows, cell_width, cell_height, rect.width, rect.height)


def get_icon_text(index: int, *, max_chars: int = TEXT_BUFFER_CHARS, validateIndex: bool = True) -> str:
    """Return the visible desktop icon text by zero-based index."""

    if validateIndex:  # May speed up batch processing
        _validate_index(index)

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")

    item_size = ctypes.sizeof(LVITEMW)
    text_size = max_chars * ctypes.sizeof(ctypes.c_wchar)
    total_size = item_size + text_size

    with _ProcessHandle(hwnd) as process:
        with _RemoteMemory(process, total_size) as remote:
            text_address = int(remote.address) + item_size
            item = LVITEMW()
            item.iItem = index
            item.iSubItem = 0
            item.pszText = ctypes.cast(text_address, wintypes.LPWSTR)
            item.cchTextMax = max_chars
            remote.write_from(item)

            _send_message(LVM_GETITEMTEXTW, index, int(remote.address))
            raw = remote.read_bytes(item_size, text_size)

    return raw.decode("utf-16-le", errors="ignore").split("\x00", 1)[0]


def iter_icons() -> Iterator[DesktopIcon]:
    """Yield desktop icon snapshots."""

    count = get_icon_count()
    for index in range(count):
        yield DesktopIcon(index, get_icon_text(index), get_icon_position(index))


def list_icons() -> list[DesktopIcon]:
    """Return all desktop icons with their current names and positions."""

    return list(iter_icons())


def find_icon(name: str, *, exact: bool = True, case_sensitive: bool = False) -> DesktopIcon | None:
    """Find the first icon whose name matches ``name``.

    With ``exact=False`` this performs a substring search.
    """

    needle = name if case_sensitive else name.casefold()
    for icon in iter_icons():
        haystack = icon.name if case_sensitive else icon.name.casefold()
        if (haystack == needle) if exact else (needle in haystack):
            return icon
    return None


def set_icon_position_by_name(
    name: str,
    x: int,
    y: int,
    *,
    exact: bool = True,
    case_sensitive: bool = False,
    redraw: bool = True,
) -> DesktopIcon:
    """Move the first icon matched by name and return its old snapshot."""

    icon = find_icon(name, exact=exact, case_sensitive=case_sensitive)
    if icon is None:
        raise LookupError(f"desktop icon was not found: {name!r}")

    set_icon_position(icon.index, x, y, redraw=redraw)
    return icon


def set_redraw(enabled: bool) -> None:
    _send_message(WM_SETREDRAW, enabled, 0)
