# Terrence - Your Virtual Desktop Buddy 🐾

Terrence is a virtual desktop companion designed to help you build healthy work habits. Terrence lives as a transparent widget on your screen, keeping an eye on your Pomodoro sessions, making sure you take breaks, and keeping you company with customizable dialogue. If you consistently skip breaks or work too late, Terrence's health drops, and he'll start aggressively asking for breaks or even eating your clipboard data!

---

## 📂 Project Structure

The project is built using Python, `tkinter` for the user interface, and `pystray` for the system tray integration. 

Here is a breakdown of the entire codebase and what each file does:

### 1. `main.py`
The entry point of the application. It initializes all the major subsystems (Config, Timer, State Machine, GUI) and wires them up. It also creates the `pystray` system tray icon (which runs in a background thread) so you can easily show or quit Terrence without cluttering your taskbar.

### 2. `flark_gui.py`
The core user interface, built using `tkinter`.
- **Window Management**: Uses an explicitly transparent, always-on-top window without borders (`overrideredirect`).
- **Interactions**: Allows you to click and drag Terrence around the screen, or right-click him to open a context menu to manage the timer or make him say things.
- **Visuals & Dialogue**: Handles the `update_loop()` which runs every second on the main thread to poll the state machine, apply visual changes (via `update_sprite()`), and spawn random speech bubbles based on events or states.

### 3. `state_machine.py`
The Brain behind Terrence's behavior and health. 
- **FlarkHealth**: Tracks Terrence's HP (0-100). Taking full breaks heals him (+10), while skipping breaks damages him (-5).
- **StateMachine**: Evaluates the world state based on the current time and the `PomodoroTimer`. Determines if Terrence is in `Deep Work`, `Break Time`, `Neglect` (ignored break), `Late Night` (past bedtime), or `Healthy`.

### 4. `timer.py`
A custom `PomodoroTimer` class that runs its ticking logic asynchronously using Python `threading`. It tracks whether it's currently "Work Time" or "Break Time", manages durations (read from config), and uses a callback system (`register_callback`) to notify the application when a phase ends.

### 5. `config_manager.py`
A simple utility that loads and saves application preferences to a local `config.json` file. 
It manages:
- Pomodoro Durations (`work_duration` and `break_duration` in minutes)
- `strict_mode` (enables severe punishments like clearing your clipboard)
- `skin` (determines which folder inside `sprites/` to load images from)

### 6. `dialogue.json` & `DIALOGUE_SYSTEM.md`
The completely customizable dialogue engine. 
- `DIALOGUE_SYSTEM.md` contains detailed documentation on how to edit dialogues.
- `dialogue.json` stores all the actual strings Terrence can express during events (like starting a break), randomly wandering in certain states, or complaining when his health drops during the punishment phases.

---

## 🚀 Getting Started

### Prerequisites
Make sure you have the following packages installed:
```bash
pip install pillow pystray
```
*(Tkinter comes built-in with most Python installations)*

### Running Terrence
To start the application, simply run:
```bash
python main.py
```
Terrence will appear in the bottom-right corner of your screen. 
- **Left-Click + Drag:** Move him anywhere.
- **Right-Click:** Pause/Start tracking, skip a phase, make him speak, or hide him.
- **System Tray:** Use the "Terrence" icon in your Windows System Tray to bring him back if you hid him!

---

## 🎨 Sprites and Skins
Credit to CraftPix on Itch for our little guy
https://free-game-assets.itch.io/free-tiny-hero-sprites-pixel-art?download
