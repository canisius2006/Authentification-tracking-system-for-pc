import win32gui

def callback(hwnd, windows):
    if win32gui.IsWindowVisible(hwnd):
        titre = win32gui.GetWindowText(hwnd)
        if titre:
            windows.append((hwnd, titre))

windows = []
win32gui.EnumWindows(callback, windows)

for hwnd, titre in windows:
    print(titre)