class HazardSystem:
    MODES = {'P', 'F', 'W', 'S'}
    TRANSITIONS = {
        'P': ['S'],          # P can only go to S
        'S': ['P', 'W', 'F'], # S can go to P, W, or F
        'W': ['S', 'F'],      # W can go to S or F
        'F': ['W', 'S']       # F can go to W or S
    }
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.current_mode = 'P'
        self.led_state = 'OFF'
        self.error = None
    
    def change_mode(self, new_mode):
        if new_mode not in self.MODES:
            self.error = f"Invalid mode {new_mode}"
            return False
            
        if new_mode not in self.TRANSITIONS.get(self.current_mode, []):
            self.error = f"Cannot transition from {self.current_mode} to {new_mode}"
            return False
            
        self.current_mode = new_mode
        self._update_led_state()
        return True
    
    def _update_led_state(self):
        states = {
            'P': 'OFF',
            'F': 'BLINK_FAST',
            'W': 'BLINK_SLOW',
            'S': 'BLINK_URGENT'
        }
        self.led_state = states[self.current_mode]
    
    def get_system_status(self):
        return {
            'mode': self.current_mode,
            'led_state': self.led_state,
            'error': self.error
        }