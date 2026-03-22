import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk
import os
import random
import threading
import pystray
from pystray import MenuItem as item

# Import our logic
from state_machine import FlarkState

class FlarkApp:
    def __init__(self, root, config_manager, timer, state_machine):
        self.root = root
        self.config = config_manager
        self.timer = timer
        self.state_machine = state_machine
        
        # Transparent window setup
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        # Choose a color that won't be in the sprite
        self.transparent_color = 'magenta'
        self.root.config(bg=self.transparent_color)
        self.root.wm_attributes("-transparentcolor", self.transparent_color)
        
        # Put Flark in bottom right corner by default
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"150x150+{screen_width - 200}+{screen_height - 200}")
        
        # Click and Drag logic
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.do_drag)
        self.root.bind("<ButtonRelease-1>", self.stop_drag)
        
        # Right click for context menu (simulated, since pystray handles system tray)
        self.root.bind("<Button-3>", self.show_context_menu)
        
        self.x = 0
        self.y = 0
        self.is_dragging = False
        
        # Load sprites mapping
        self.skin = self.config.get("skin", "classic")
        self.sprites = {}
        self.load_sprites()
        
        # UI Elements
        self.image_label = tk.Label(self.root, bg=self.transparent_color)
        self.image_label.pack(expand=True, fill=tk.BOTH)
        
        # Text Bubble (Level 1 punishment or just info)
        self.bubble_label = tk.Label(self.root, text="", bg="white", fg="black", font=("Arial", 10), wraplength=120)
        # We don't pack it yet, only when needed
        
        self.current_frame = None
        self.update_sprite()
        
        # Start the update loop for the state machine
        self.update_loop()
        
    def load_sprites(self):
        # We will use simple placeholders if actual sprites don't exist
        skin_dir = os.path.join(os.path.dirname(__file__), "sprites", self.skin)
        
        # Mapping state to a color for the placeholder
        state_colors = {
            FlarkState.DEEP_WORK: "blue",
            FlarkState.BREAK_TIME: "green",
            FlarkState.NEGLECT: "red",
            FlarkState.LATE_NIGHT: "purple",
            FlarkState.HEALTHY: "cyan"
        }
        
        os.makedirs(skin_dir, exist_ok=True)
        
        for state, color in state_colors.items():
            img_path = os.path.join(skin_dir, f"{state.replace(' ', '_').lower()}.png")
            if not os.path.exists(img_path):
                # Auto-generate placeholder
                img = Image.new('RGBA', (100, 100), color=color)
                # To test transparency, we could make it a circle
                from PIL import ImageDraw
                draw = ImageDraw.Draw(img)
                # Draw a smaller circle in the middle
                draw.ellipse((10, 10, 90, 90), fill=color, outline="black")
                # Make background magenta (which will be keyed out)
                bg = Image.new('RGBA', (100, 100), color=(255, 0, 255, 255))
                bg.paste(img, (0, 0), img)
                bg.save(img_path)
            
            self.sprites[state] = ImageTk.PhotoImage(Image.open(img_path))

    def start_drag(self, event):
        self.x = event.x
        self.y = event.y
        self.is_dragging = True

    def do_drag(self, event):
        if self.is_dragging:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        self.is_dragging = False

    def show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        
        if self.timer.is_running:
            menu.add_command(label="Pause Timer", command=self.timer.pause)
        else:
            phase = "Work" if self.timer.is_work_time else "Break"
            menu.add_command(label=f"Start {phase}", command=self.timer.start)
            
        menu.add_command(label="Skip Phase", command=self.timer.skip)
        menu.add_separator()
        menu.add_command(label="Hide (To Tray)", command=self.hide_window)
        menu.add_command(label="Exit", command=self.quit_app)
        menu.tk_popup(event.x_root, event.y_root)

    def hide_window(self):
        self.root.withdraw()
        
    def quit_app(self):
        self.root.quit()

    def update_loop(self):
        """Main ticking loop for Flark"""
        self.state_machine.update()
        self.update_sprite()
        self.apply_punishments()
        self.root.after(1000, self.update_loop)

    def update_sprite(self):
        state = self.state_machine.current_state
        if state in self.sprites:
            self.image_label.config(image=self.sprites[state])

    def apply_punishments(self):
        level = self.state_machine.get_punishment_level()
        
        # Reset previous punishments if level drops
        if level < 1 and self.bubble_label.winfo_ismapped():
            self.bubble_label.place_forget()
            
        if level >= 1:
            # Passive aggressive texts
            if random.random() < 0.05 and not self.bubble_label.winfo_ismapped():
                messages = [
                    "You skipped a break, seriously?", 
                    "My health is dropping!", 
                    "You're going to burn out.", 
                    "Please take a break."
                ]
                self.bubble_label.config(text=random.choice(messages))
                self.bubble_label.place(x=10, y=10)
                # Hide after 3 seconds
                self.root.after(3000, self.bubble_label.place_forget)
                
        if level >= 2:
            # Wandering / shaking
            if random.random() < 0.1:
                dx = random.randint(-20, 20)
                dy = random.randint(-20, 20)
                nx = self.root.winfo_x() + dx
                ny = self.root.winfo_y() + dy
                self.root.geometry(f"+{nx}+{ny}")
                
        if level >= 3:
            # Annoying level! Clear clipboard every 10 seconds?
            if random.random() < 0.05:
                # Only clear clipboard if strict mode is ON maybe? Or just do it.
                if self.config.get("strict_mode", False):
                    self.root.clipboard_clear()
                    print("Flark ate your clipboard!")
                    self.bubble_label.config(text="*CHOMP* Your clipboard tasted good!")
                    self.bubble_label.place(x=10, y=10)
                    self.root.after(2000, self.bubble_label.place_forget)
                    
                    # Beep sound (Windows)
                    import winsound
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
