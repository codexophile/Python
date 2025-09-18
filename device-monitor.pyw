import wmi
import time
from win10toast import ToastNotifier # or from winotify import Notification, audio

# --- System Tray integration (Windows) ---
import os
import sys
import threading
import ctypes

try:
    import pystray
    from pystray import MenuItem as _MenuItem
except Exception:
    pystray = None

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = ImageDraw = ImageFont = None

_tray_icon = None
_stop_event = threading.Event()


def _create_tray_image(width=64, height=64, text='DM'):
    """Create a small in-memory icon image."""
    if Image is None or ImageDraw is None:
        return None
    img = Image.new('RGBA', (width, height), (38, 38, 38, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=(90, 90, 90, 255))
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    if font is not None and hasattr(draw, "textsize"):
        tw, th = draw.textsize(text, font=font)
        draw.text(((width - tw) // 2, (height - th) // 2), text, font=font, fill=(0, 200, 255, 255))
    return img


def toggle_console_window(icon=None, item=None):
    """Hide/show the current process console window on Windows."""
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if not hwnd:
            print('[tray] No console window handle available to toggle (possibly running without a console).')
            return
        is_visible = ctypes.windll.user32.IsWindowVisible(hwnd) != 0
        SW_HIDE = 0
        SW_SHOW = 5
        ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE if is_visible else SW_SHOW)
    except Exception as e:
        print(f'[tray] Toggle console failed: {e}')


def hide_console_window():
    """Hide the console window if it is currently visible."""
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if not hwnd:
            # Likely running without a console (e.g., pythonw or integrated terminal)
            return
        is_visible = ctypes.windll.user32.IsWindowVisible(hwnd) != 0
        if is_visible:
            SW_HIDE = 0
            ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)
    except Exception as e:
        print(f'[tray] Hide console failed: {e}')


def _do_restart(icon_ref):
    """Perform restart in a safe way by spawning a new process and exiting."""
    try:
        # Hide/stop tray to avoid duplicate icons lingering
        if icon_ref is not None:
            try:
                icon_ref.visible = False
                icon_ref.stop()
            except Exception:
                pass

        # Flush IO before spawn
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass

        import subprocess
        args = [sys.executable] + sys.argv
        subprocess.Popen(args, cwd=os.getcwd(), env=os.environ, shell=False)
        # Hard-exit current process so only the new instance remains
        os._exit(0)
    except Exception as e:
        print(f'[tray] Restart failed: {e}')


def restart_program(icon=None, item=None):
    """Restart the current Python script."""
    print('[tray] Restarting script...')
    threading.Thread(target=_do_restart, args=(icon,), daemon=True).start()


def quit_program(icon=None, item=None):
    """Gracefully stop the monitor loop and exit the program."""
    print('[tray] Quit requested.')
    # Signal the main loop to stop
    _stop_event.set()
    # Best-effort cleanup of tray icon from the tray thread
    try:
        if icon is not None:
            icon.visible = False
            icon.stop()
    except Exception:
        pass


def start_system_tray():
    """Create and start the system tray icon in the background."""
    global _tray_icon

    if pystray is None:
        print('[tray] pystray not installed. Run: pip install pystray pillow')
        return None

    if _tray_icon is not None:
        return _tray_icon

    image = _create_tray_image() or None
    menu = pystray.Menu(
        _MenuItem('Toggle Console Window', toggle_console_window),
        _MenuItem('Restart Script', restart_program),
        _MenuItem('Quit', quit_program),
    )
    _tray_icon = pystray.Icon('device_monitor', image, 'Device Monitor', menu)

    try:
        _tray_icon.run_detached()
    except AttributeError:
        threading.Thread(target=_tray_icon.run, daemon=True).start()

    return _tray_icon
# --- End System Tray integration ---

def show_notification(title, message):
    toaster = ToastNotifier()
    toaster.show_toast(title, message, duration=5, icon_path=None) # Customize icon_path if desired
    # If using winotify:
    # Notification(app_id="DeviceMonitor",
    #              title=title,
    #              msg=message,
    #              duration="short", # or "long"
    #              icon=r"C:\path\to\your\icon.png").show()
    # Notification(app_id="DeviceMonitor", title=title, msg=message, icon=r"C:\path\to\icon.png").add_audio(audio.Mail, loop=False).show() # Example with sound [9]

def monitor_device_changes(stop_event: threading.Event | None = None):
    c = wmi.WMI()
    
    print("Monitoring for device connection/disconnection events...")
    print("Connect or disconnect a USB device to test...")
    
    # Get initial device list for comparison
    previous_devices = set()
    try:
        for device in c.Win32_PnPEntity():
            if device.Caption and device.Present:
                previous_devices.add(device.DeviceID)
    except Exception as e:
        print(f"Error getting initial device list: {e}")
        return

    if stop_event is None:
        stop_event = _stop_event

    while not stop_event.is_set():
        try:
            # Get current device list
            current_devices = set()
            current_device_info = {}
            
            for device in c.Win32_PnPEntity():
                if device.Caption and device.Present:
                    current_devices.add(device.DeviceID)
                    current_device_info[device.DeviceID] = device.Caption
            
            # Check for newly connected devices
            new_devices = current_devices - previous_devices
            for device_id in new_devices:
                device_name = current_device_info.get(device_id, 'Unknown Device')
                print(f"Device Connected: {device_name}")
                show_notification("Device Connected", f"Name: {device_name}")
            
            # Check for disconnected devices
            removed_devices = previous_devices - current_devices
            if removed_devices:
                # We don't have the name for removed devices, so just show count
                print(f"Device(s) Disconnected: {len(removed_devices)} device(s)")
                show_notification("Device Disconnected", f"{len(removed_devices)} device(s) removed")
            
            # Update previous devices list
            previous_devices = current_devices
            
        except Exception as e:
            print(f"An error occurred: {e}")
        
        # Check every 2 seconds to reduce CPU usage, but wake early on stop
        for _ in range(20):  # 20 x 0.1s = 2s
            if stop_event.is_set():
                break
            time.sleep(0.1)

    print('Monitor loop stopped.')

if __name__ == "__main__":
    # Start tray first so it’s available while your script runs
    start_system_tray()
    # Hide the console at startup (best-effort; requires a real console window)
    hide_console_window()

    try:
        monitor_device_changes(_stop_event)
    finally:
        # Ensure tray icon is cleaned up on exit
        try:
            if _tray_icon is not None:
                _tray_icon.visible = False
                _tray_icon.stop()
        except Exception:
            pass