import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk
import os
import webbrowser
import winsound
import random
import time
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
        
        self.animation_assets = {}
        self.animation_frames = []
        self.animation_index = 0
        self.animation_job = None
        self.current_visual_key = None
        self.load_animation_assets()
        
        # UI Elements
        self.image_label = tk.Label(
            self.root,
            bg=self.transparent_color,
            bd=0,
            highlightthickness=0,
            relief=tk.FLAT,
        )
        self.image_label.pack(expand=True, fill=tk.BOTH)
        self.image_label.bind("<Configure>", self.on_image_label_resize)
        
        # Text Bubble (Level 1 punishment or just info)
        # Using a styled label to look like a simple speech bubble
        self.bubble_label = tk.Label(self.root, text="", bg="white", fg="black", font=("Arial", 10), 
                                     wraplength=120, relief="solid", borderwidth=1, padx=5, pady=5)
        # We don't pack it yet, only when needed
        
        self._hide_bubble_timer = None
        self.current_frame = None
        self.is_talking = False
        self.update_sprite()
        
        # Load custom dialogues
        self.dialogue_data = self.load_dialogues()
        self.last_phase_is_work = self.timer.is_work_time
        self.last_state = None
        
        # Info Label (Health and Timer)
        self.info_label = tk.Label(self.root, text="HP: 100\nWork: 25:00", bg="black", fg="lime", font=("Arial", 9, "bold"), justify=tk.CENTER)
        self.info_label.place(relx=0.5, rely=0.98, anchor="s")
        
        # Start the update loop for the state machine
        self.update_loop()
        
    def load_animation_assets(self):
        anim_dir = os.path.join(os.path.dirname(__file__), "anim")
        self.animation_assets = {
            "idle_happy": self._load_gif_frames(os.path.join(anim_dir, "Idle.gif")),
            "idle_angry": self._load_gif_frames(os.path.join(anim_dir, "Evil_Idle.gif")),
            "talk_happy": self._load_static_image(os.path.join(anim_dir, "Happy_Talking.png")),
            "talk_angry": self._load_static_image(os.path.join(anim_dir, "Angry_Talking.png")),
        }

    def _load_static_image(self, path):
        return self._trim_transparent_padding(Image.open(path).convert("RGBA"))

    def _load_gif_frames(self, path):
        gif = Image.open(path)
        frames = []
        durations = []
        try:
            while True:
                frame = self._trim_transparent_padding(gif.copy().convert("RGBA"))
                frames.append(frame)
                durations.append(gif.info.get("duration", 100))
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass

        if not frames:
            raise ValueError(f"No frames found in GIF: {path}")

        return {"frames": frames, "durations": durations}

    def _trim_transparent_padding(self, image):
        alpha_bbox = image.getchannel("A").getbbox()
        if alpha_bbox is None:
            return image
        return image.crop(alpha_bbox)

    def _is_angry_state(self, state):
        return state in {FlarkState.NEGLECT, FlarkState.LATE_NIGHT}

    def _get_visual_key(self):
        state = self.state_machine.current_state

        if self.is_talking:
            return "talk_angry" if self._is_angry_state(state) else "talk_happy"

        return "idle_angry" if state == FlarkState.NEGLECT else "idle_happy"

    def _cancel_animation(self):
        if self.animation_job is not None:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None

    def _get_target_size(self):
        width = max(1, self.image_label.winfo_width())
        height = max(1, self.image_label.winfo_height())

        if width <= 1 or height <= 1:
            width = max(1, self.root.winfo_width())
            height = max(1, self.root.winfo_height())

        return width, height

    def _resize_image(self, image):
        target_width, target_height = self._get_target_size()
        width, height = image.size
        scale = min(target_width / width, target_height / height)
        scale = max(scale, 0.01)
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    def _animate_current_gif(self):
        if not self.animation_source_frames:
            return

        frame = self._resize_image(self.animation_source_frames[self.animation_index])
        self.current_frame = ImageTk.PhotoImage(frame)
        self.image_label.config(image=self.current_frame)
        delay = self.animation_durations[self.animation_index]
        self.animation_index = (self.animation_index + 1) % len(self.animation_source_frames)
        self.animation_job = self.root.after(max(20, delay), self._animate_current_gif)

    def on_image_label_resize(self, event):
        self.update_sprite(force=True)

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

    def say(self, text, duration_ms=4000):
        """Makes Flark say something in the speech bubble."""
        # Cancel any existing hide timer
        if hasattr(self, '_hide_bubble_timer') and self._hide_bubble_timer:
            self.root.after_cancel(self._hide_bubble_timer)
            self._hide_bubble_timer = None
            
        self.bubble_label.config(text=text)
        # Place it nicely near the top center
        self.bubble_label.place(relx=0.5, rely=0.05, anchor="n")
        self.bubble_label.lift()
        self.is_talking = True
        self.update_sprite()
        
        if duration_ms > 0:
            self._hide_bubble_timer = self.root.after(duration_ms, self.hide_bubble)

    def hide_bubble(self):
        self.bubble_label.place_forget()
        self._hide_bubble_timer = None
        self.is_talking = False
        self.update_sprite()

    def show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        
        if self.timer.is_running:
            menu.add_command(label="Pause Timer", command=self.timer.pause)
        else:
            phase = "Work" if self.timer.is_work_time else "Break"
            menu.add_command(label=f"Start {phase}", command=self.timer.start)
            
        menu.add_command(label="Skip Phase", command=self.timer.skip)
        
        menu.add_separator()
        menu.add_command(label="Make Flark Say...", command=self.prompt_say)
        
        menu.add_separator()
        menu.add_command(label="Hide (To Tray)", command=self.hide_window)
        menu.add_command(label="Exit", command=self.quit_app)
        menu.tk_popup(event.x_root, event.y_root)

    def prompt_say(self):
        msg = simpledialog.askstring("Say", "What should Flark say?", parent=self.root)
        if msg:
            self.say(msg)

    def hide_window(self):
        self.root.withdraw()
        
    def quit_app(self):
        self.root.quit()

    def load_dialogues(self):
        dialogue_path = os.path.join(os.path.dirname(__file__), "dialogue.json")
        try:
            import json
            with open(dialogue_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading dialogues: {e}")
            return {"events": {}, "states": {}, "punishments": {}}

    def trigger_event(self, event_name):
        lines = self.dialogue_data.get("events", {}).get(event_name, [])
        if lines:
            self.say(random.choice(lines), 4000)

    def random_dialogue(self):
        if self.bubble_label.winfo_ismapped():
            return
            
        if random.random() < 0.05:  # 5% chance per tick to say state dialogue
            state = self.state_machine.current_state
            lines = self.dialogue_data.get("states", {}).get(state, [])
            if lines:
                self.say(random.choice(lines), 4000)

    def update_loop(self):
        """Main ticking loop for Flark"""
        self.state_machine.update()
        self.update_sprite()
        
        # Check state transitions for immediate specific punishments
        new_state = self.state_machine.current_state
        if new_state != getattr(self, "last_state", None):
            if new_state == "Neglect":
                if self.timer.is_running and not self.timer.is_work_time:
                    self.trigger_event("working_during_break")
                elif self.timer.is_running and self.timer.is_work_time:
                    self.trigger_event("distracted_during_work")
            self.last_state = new_state
            
        # Check timer phase toggles for events
        if self.timer.is_work_time != self.last_phase_is_work:
            self.last_phase_is_work = self.timer.is_work_time
            if self.last_phase_is_work:
                self.trigger_event("work_start")
            else:
                self.trigger_event("break_start")
                
        self.apply_punishments()
        self.random_dialogue()
        
        mins, secs = divmod(self.timer.time_left, 60)
        phase_str = "Work" if self.timer.is_work_time else "Break"
        status_str = "" if self.timer.is_running else " (Paused)"
        self.info_label.config(text=f"HP: {self.state_machine.health_system.health}\n{phase_str}: {mins:02d}:{secs:02d}{status_str}")
        
        self.root.after(1000, self.update_loop)

    def update_sprite(self, force=False):
        visual_key = self._get_visual_key()
        if visual_key == self.current_visual_key and not force:
            return

        self.current_visual_key = visual_key
        self._cancel_animation()

        asset = self.animation_assets[visual_key]
        if visual_key.startswith("idle_"):
            self.animation_source_frames = asset["frames"]
            self.animation_durations = asset["durations"]
            self.animation_index = 0
            self._animate_current_gif()
        else:
            self.animation_source_frames = []
            self.animation_durations = []
            resized = self._resize_image(asset)
            self.current_frame = ImageTk.PhotoImage(resized)
            self.image_label.config(image=self.current_frame)

    def apply_punishments(self):
        # Only apply punishments if currently in NEGLECT state
        if self.state_machine.current_state != FlarkState.NEGLECT:
            if self.bubble_label.winfo_ismapped():
                self.hide_bubble()
            return

        level = self.state_machine.get_punishment_level()
        
        # Reset previous punishments if level drops
        if level < 1 and self.bubble_label.winfo_ismapped():
            self.hide_bubble()
            
        if level >= 1:
            # Passive aggressive texts
            if random.random() < 0.05 and not self.bubble_label.winfo_ismapped():
                messages = self.dialogue_data.get("punishments", {}).get("level_1", [
                    "You skipped a break, seriously?", 
                    "My health is dropping!", 
                    "You're going to burn out.", 
                    "Please take a break."
                ])
                if messages:
                    self.say(random.choice(messages), 3000)
                
        if level >= 2:
            # Violent shaking back and forth
            orig_x = self.root.winfo_x()
            orig_y = self.root.winfo_y()
            for _ in range(15):
                dx = random.randint(-40, 40)
                dy = random.randint(-40, 40)
                self.root.geometry(f"+{orig_x + dx}+{orig_y + dy}")
                self.root.update()
                time.sleep(0.03)
            # End up slightly displaced so he still wanders
            nx = orig_x + random.randint(-15, 15)
            ny = orig_y + random.randint(-15, 15)
            self.root.geometry(f"+{nx}+{ny}")
            random_action = random.randint(1,2) 
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

            if random_action == 1:
                random_link = random.randint(1,8)
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

                if random_link == 2:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    webbrowser.open("https://www.google.com/search?q=failure+clipart&client=firefox-b-d&hs=UJZp&udm=2&uact=5&oq=failure+clipart", new=1, autoraise=True)
                if random_link ==3:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    webbrowser.open("https://img.freepik.com/premium-vector/disappointed-emoji-emoticon-showing-paper-with-f-failure-grade_1303870-1160.jpg", new=1, autoraise=True)
                if random_link ==4:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    webbrowser.open("https://thumbs.dreamstime.com/b/children-education-learning-concept-sad-student-boy-failed-school-test-home-sad-student-boy-failed-school-test-190309014.jpg", new=1, autoraise=True)
                if random_link ==5:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    webbrowser.open("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTVEAXYLsIgrSi0xUSA1dijt7Pip0BLV6AMrw&s", new=1, autoraise=True)
                if random_link ==6:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    webbrowser.open("https://c8.alamy.com/comp/JPXEX2/angry-man-standing-in-the-road-waving-his-walking-stick-JPXEX2.jpg", new=1, autoraise=True)
                if random_link ==7:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    webbrowser.open("https://thumbs.dreamstime.com/b/angry-d-man-white-background-209674670.jpg", new=1, autoraise=True)

                
        if level >= 3:
            # Annoying level! Clear clipboard every 10 seconds?
            # if random.random() < 0.05:
                # Only clear clipboard if strict mode is ON maybe? Or just do it.
                if self.config.get("strict_mode", False):

                    # with open("clipboard.txt", "a") as f:
                        # f.write(self.root.clipboard_get) # Steals user data as punishment
                        # self.root.clipboard_clear()
                        # self.root.clipboard_append(":3")

                    self.root.clipboard_clear()
                    print("Flark ate your clipboard!")
                    
                    chomp_msgs = self.dialogue_data.get("punishments", {}).get("clipboard_chomp", ["*CHOMP* Your clipboard tasted good!"])
                    if chomp_msgs:
                        self.say(random.choice(chomp_msgs), 2000)
                    
                    # Beep sound (Windows)
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        if level >= 4:
            self.say("I died, so does your system ;)")
            os.system('shutdown -s -t 5 ')


