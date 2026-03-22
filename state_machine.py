import time
import datetime
from window_tracker import get_active_window_title
import os
class FlarkState:
    DEEP_WORK = "Deep Work"
    BREAK_TIME = "Break Time"
    NEGLECT = "Neglect"
    LATE_NIGHT = "Late Night"
    HEALTHY = "Healthy"

class FlarkHealth:
    def __init__(self):
        self.health = 100

    def heal(self, amount):
        self.health = min(100, self.health + amount)

    def damage(self, amount):
        self.health = max(0, self.health - amount)

class StateMachine:
    def __init__(self, timer, config_manager):
        self.timer = timer
        self.config = config_manager
        self.health_system = FlarkHealth()
        self.current_state = FlarkState.HEALTHY
        
        self.last_work_end_time = None
        self.break_in_progress = False
        
        # We need a ticker to check time-based states like Neglect and Late Night
        self.ticker_running = True
        
    def update(self):
        """Called periodically (e.g., every second) by the main loop/GUI to evaluate state."""
        now = datetime.datetime.now()
        
        # 1. Check Late Night (> 11:00 PM or < 4:00 AM)
        if now.hour >= 23 or now.hour < 4:
            self._set_state(FlarkState.LATE_NIGHT)
            return

        # 1.5. Check Active Window overrides
        active_window = get_active_window_title().lower()
        work_apps = [app.lower() for app in self.config.get("work_apps", [])]
        distracting_apps = [app.lower() for app in self.config.get("distracting_apps", [])]

        if active_window:
            if any(app in active_window for app in work_apps):
                # If they are working during their break, Flark gets mad!
                if self.timer.is_running and not self.timer.is_work_time:
                    self._set_state(FlarkState.NEGLECT)
                    if not hasattr(self, '_overwork_ticks'):
                        self._overwork_ticks = 0
                    self._overwork_ticks += 1
                    if self._overwork_ticks >= 5:
                        self.health_system.damage(5)
                        self._overwork_ticks = 0
                    return
                else:
                    self._set_state(FlarkState.DEEP_WORK)
                    self.last_work_end_time = None
                    self.break_in_progress = False
                    # Auto-start the timer organically if it wasn't running
                    if not self.timer.is_running and self.timer.is_work_time:
                        self.timer.start()
                        
                    if not hasattr(self, '_work_ticks'):
                        self._work_ticks = 0
                    self._work_ticks += 1
                    if self._work_ticks >= 5:
                        self.health_system.heal(1)
                        self._work_ticks = 0
                    return
                
            if any(app in active_window for app in distracting_apps):
                if self.timer.is_running and self.timer.is_work_time:
                    self._set_state(FlarkState.NEGLECT)
                    if not hasattr(self, '_distraction_ticks'):
                        self._distraction_ticks = 0
                    self._distraction_ticks += 1
                    if self._distraction_ticks >= 5:  # 5 seconds of continuous distraction
                        self.health_system.damage(5)
                        self._distraction_ticks = 0
                    return

        # 2. Check Deep Work
        if self.timer.is_running and self.timer.is_work_time:
            self._set_state(FlarkState.DEEP_WORK)
            self.last_work_end_time = None
            self.break_in_progress = False
            
            if not hasattr(self, '_work_ticks'):
                self._work_ticks = 0
            self._work_ticks += 1
            if self._work_ticks >= 5:
                self.health_system.heal(1)
                self._work_ticks = 0
            return
            
        # 3. Check Break Time
        if self.timer.is_running and not self.timer.is_work_time:
            self._set_state(FlarkState.BREAK_TIME)
            self.break_in_progress = True
            
            if not hasattr(self, '_rest_ticks'):
                self._rest_ticks = 0
            self._rest_ticks += 1
            if self._rest_ticks >= 5:
                self.health_system.heal(1)
                self._rest_ticks = 0
            return

        # 4. Check Neglect
        # If timer is paused, and we are NOT in work time (meaning it's break time),
        # or we finished work and haven't started break.
        if not self.timer.is_running and not self.timer.is_work_time:
            if self.last_work_end_time is None:
                self.last_work_end_time = time.time()
            
            time_since_work_end = time.time() - self.last_work_end_time
            # Neglect: > 5 mins (300 seconds) ignored break
            if time_since_work_end > 300:
                self._set_state(FlarkState.NEGLECT)
                
                # Apply damage: -5 HP for every 10 minutes (600 seconds) skipped
                # We calculate how many increments of 10 mins have passed 
                # strictly past the 5-minute neglect mark.
                # Actually, simple periodic damage check every update might be heavy.
                # Just doing it discretely based on total time.
                total_10_min_blocks = int((time_since_work_end - 300) / 600)
                # Keep track of damage applied so we don't apply it constantly
                if not hasattr(self, '_last_damage_block'):
                    self._last_damage_block = -1
                
                if total_10_min_blocks > self._last_damage_block:
                    self.health_system.damage(5)
                    self._last_damage_block = total_10_min_blocks
                return

        # 5. Default Healthy (if health > 80, otherwise just "Healthy" placeholder)
        self._set_state(FlarkState.HEALTHY)

    def on_timer_phase_end(self):
        """Hook for when a timer phase natural end happens"""
        if not self.timer.is_work_time:
            # We just finished Work, now entering Break phase (paused)
            self.last_work_end_time = time.time()
            self._last_damage_block = -1
        else:
            # We just finished Break phase (entering Work)
            # Full break completed, +10 HP
            self.health_system.heal(10)
            self.last_work_end_time = None
            self.break_in_progress = False

    def _set_state(self, new_state):
        if self.current_state != new_state:
            self.current_state = new_state
            mins, secs = divmod(self.timer.time_left, 60)
            print(f"Flark shifted to state: {self.current_state} (HP: {self.health_system.health}) | Time Remaining: {mins:02d}:{secs:02d}")

    def get_punishment_level(self):
        """Returns 0, 1, 2, or 3 based on health."""
        if self.health_system.health > 80:
            return 0
        elif self.health_system.health > 50:
            return 1 # Level 1
        elif self.health_system.health > 20:
            return 2 # Level 2
        elif self.health_system.health > 15:
            return 3 # Level 3
        elif self.health_system.health == 0:
            return 4
        else:
            return 3
