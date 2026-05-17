"""Exceptions raised by desktop_icons."""


class DesktopIconsError(RuntimeError):
    """Base error for this package."""


class DesktopListViewNotFound(DesktopIconsError):
    """Explorer's desktop ListView control was not found."""


class WinApiError(DesktopIconsError):
    """A WinAPI call failed."""

    def __init__(self, function: str, code: int | None = None) -> None:
        self.function = function
        self.code = code
        if code is None:
            message = f"{function} failed"
        else:
            message = f"{function} failed with Windows error {code}"
        super().__init__(message)
