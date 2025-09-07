# Simple visualization module - no complex dependencies

class GameVisualizer:
    def __init__(self, enable_logging=True):
        self.enable_logging = enable_logging
        self.game_count = 0
        self.decisions_made = 0
        
    def visualize_game_state(self, state, agent_map, pacman_pos):
        """Simple game state visualization"""
        print("Map Legend: P=Pacman, G=Ghost, F=Food, C=Capsule, #=Wall")
        print("Current Pacman position: %s" % str(pacman_pos))
        print("Map analysis: Value function computed for %d iterations" % 8)
        
    def log_decision(self, state, action_scores, chosen_action, decision_time):
        """Log decision information"""
        self.decisions_made += 1
        print("Decision #%d: Chose %s (time: %.3fs)" % 
              (self.decisions_made, chosen_action, decision_time))
        
        # Show action score analysis
        if action_scores:
            best_score = max(action_scores.values())
            worst_score = min(action_scores.values())
            confidence = best_score - worst_score
            print("  Decision confidence: %.2f (higher = more decisive)" % confidence)
            
    def log_game_result(self, state, game_won, final_score):
        """Log game completion"""
        self.game_count += 1
        print("\n--- Game %d Summary ---" % self.game_count)
        print("Result: %s" % ("WIN" if game_won else "LOSS"))
        print("Total decisions made: %d" % self.decisions_made)
        self.decisions_made = 0  # Reset for next game

def create_visualizer(enable_logging=True):
    """Create visualizer instance"""
    return GameVisualizer(enable_logging)