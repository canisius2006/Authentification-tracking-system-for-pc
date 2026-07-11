import win32gui
liste = []
def enum_windows():
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            titre = win32gui.GetWindowText(hwnd)
            if titre:
                windows.append((hwnd, titre))
        return True

    windows = []
    win32gui.EnumWindows(callback, windows)
    return windows

for hwnd, titre in enum_windows():
    liste.append(titre)
print(liste)