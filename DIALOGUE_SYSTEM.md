# Flark Dialogue System

Flark uses a simple JSON file (`dialogue.json`) to control everything he says! This makes it incredibly easy for you to customize his personality, add new jokes, or make his warnings more severe.

## How it works
The `dialogue.json` file is divided into three main sections. When Flark decides to speak, he picks a random line from the corresponding list.

### 1. `"events"`
These are triggered exactly once when a specific action occurs.
- **`break_start`**: When the Pomodoro timer finishes a work session and begins a break.
- **`work_start`**: When the Pomodoro timer finishes a break and begins a work session.

### 2. `"states"`
While Flark is just hanging out on your screen, he has a 5% chance every second to randomly say something based on his current state.
- **`Deep Work`**: The timer is currently ticking for a work session.
- **`Break Time`**: The timer is currently paused or ticking for a break session.
- **`Neglect`**: You finished a work session but haven't started your break yet.
- **`Late Night`**: It's past your bedtime (default >11pm or <4am) and you are still awake.
- **`Healthy`**: A default state when Flark has high HP and no timer is running.

### 3. `"punishments"`
These replace the hardcoded warnings Flark gives you when your health drops from bad habits.
- **`level_1`**: Passive-aggressive lines Flark randomly says when his health drops below 50.
- **`clipboard_chomp`**: The specific line he says when his health drops so low (level 3) that he eats your clipboard data to get your attention!

## Customizing
To add your own lines:
1. Open `dialogue.json` in any text editor.
2. Find the category you want to edit.
3. Add a new string to the list. Make sure each line is wrapped in quotes `""` and separated by commas `,`.
4. Restart Flark for the changes to take effect!
