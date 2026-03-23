import ctypes

def get_active_window_title():
    """Returns the title of the currently active window on Windows."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if hwnd:
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            return title if title.strip() else "Blank"
    except Exception as e:
        print(f"Window tracker error: {e}")
    return "Blank"
