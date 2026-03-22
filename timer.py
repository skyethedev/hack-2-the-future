import time
import threading

class PomodoroTimer:
    def __init__(self, work_duration_min=25, break_duration_min=5):
        self.work_duration = work_duration_min * 60
        self.break_duration = break_duration_min * 60
        self.time_left = self.work_duration
        self.is_running = False
        self.is_work_time = True
        self._thread = None
        self._callbacks = []

    def set_durations(self, work_duration_min, break_duration_min):
        self.work_duration = work_duration_min * 60
        self.break_duration = break_duration_min * 60
        if not self.is_running:
            self.reset()

    def register_callback(self, callback):
        """Callback receives (is_work_time, time_left_seconds)"""
        self._callbacks.append(callback)

    def _notify(self):
        for cb in self._callbacks:
            try:
                cb(self.is_work_time, self.time_left)
            except Exception as e:
                print(f"Timer callback error: {e}")

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._run_timer, daemon=True)
            self._thread.start()
            self._notify()

    def pause(self):
        self.is_running = False

    def reset(self):
        self.is_running = False
        self.is_work_time = True
        self.time_left = self.work_duration
        self._notify()

    def skip(self):
        """Skip current phase and go to the next."""
        self.is_running = False
        self.time_left = 0
        self._handle_phase_end()

    def _run_timer(self):
        while self.is_running and self.time_left > 0:
            time.sleep(1)
            if not self.is_running:
                break
            self.time_left -= 1
            self._notify()
            
            if self.time_left <= 0:
                self._handle_phase_end()

    def _handle_phase_end(self):
        self.is_running = False
        self.is_work_time = not self.is_work_time
        
        if self.is_work_time:
            self.time_left = self.work_duration
        else:
            self.time_left = self.break_duration
            
        self._notify()
        # Optionally auto-start the next phase or wait for user input
        # Currently, requires user to click start for next phase
