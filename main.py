import tkinter as tk
import threading
from PIL import Image
import pystray
from pystray import MenuItem as item

from config_manager import ConfigManager
from timer import PomodoroTimer
from state_machine import StateMachine
from flark_gui import FlarkApp
import os

def load_icon():
    # Attempt to load classic healthy icon as tray icon, fallback to generated
    icon_path = os.path.join(os.path.dirname(__file__), "sprites", "classic", "healthy.png")
    if os.path.exists(icon_path):
        return Image.open(icon_path)
    else:
        img = Image.new('RGB', (64, 64), color='cyan')  
        return img

def main():
    config = ConfigManager()
    
    # Init Timer
    timer = PomodoroTimer(
        work_duration_min=config.get("work_duration", 25),
        break_duration_min=config.get("break_duration", 5)
    )
    
    # Init Logic
    state_machine = StateMachine(timer, config)
    
    # Hook timer to state machine
    timer.register_callback(lambda is_work, time_left: state_machine.on_timer_phase_end() if time_left <= 0 else None)
    
    # Init GUI
    root = tk.Tk()
    app = FlarkApp(root, config, timer, state_machine)
    
    # Pystray Setup
    def show_window(icon, item):
        root.deiconify()
        
    def quit_app(icon, item):
        icon.stop()
        root.quit()
        
    menu = (
        item('Show Flark', show_window, default=True),
        item('Quit', quit_app)
    )
    
    icon_image = load_icon()
    tray_icon = pystray.Icon("Flark", icon_image, "Flark Buddy", menu)
    
    # Run pystray in a thread so non-blocking to tkinter
    threading.Thread(target=tray_icon.run, daemon=True).start()
    
    root.mainloop()

if __name__ == "__main__":
    main()
