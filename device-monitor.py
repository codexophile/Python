import wmi
import time
from win10toast import ToastNotifier # or from winotify import Notification, audio

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

def monitor_device_changes():
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

    while True:
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
        
        time.sleep(2) # Check every 2 seconds to reduce CPU usage

if __name__ == "__main__":
    monitor_device_changes()