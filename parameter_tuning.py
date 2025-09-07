# parameter_tuning.py - Systematic Parameter Optimization for MDP Agent
# 
# This module provides automated parameter tuning to optimize the MDP agent's
# performance beyond the current 60% win rate.

import os
import sys
import json
import time
import itertools
import subprocess
from datetime import datetime
from benchmark import MDPBenchmark

class ParameterTuner:
    """Automated parameter tuning for MDP Pacman agent"""
    
    def __init__(self, pacman_directory=".", backup_original=True):
        self.pacman_dir = pacman_directory
        self.benchmark = MDPBenchmark(pacman_directory)
        self.original_file = None
        
        # Current best known parameters (your working configuration)
        self.baseline_params = {
            'EMPTY_LOCATION_REWARD': -0.04,
            'FOOD_REWARD': 10,
            'CAPSULE_REWARD': 100,
            'GHOST_REWARD': -1000,
            'GAMMA': 0.9,
            'DANGER_ZONE_RATIO': 6,
            'DANGER': 500,
            'ITERATIONS': 10
        }
        
        # Parameter search spaces for optimization
        self.search_spaces = {
            'FOOD_REWARD': [8, 10, 12, 15, 20],
            'CAPSULE_REWARD': [80, 100, 120, 150, 200],
            'GHOST_REWARD': [-800, -1000, -1200, -1500, -2000],
            'DANGER': [300, 400, 500, 600, 800],
            'GAMMA': [0.85, 0.9, 0.92, 0.95],
            'DANGER_ZONE_RATIO': [4, 5, 6, 7, 8],
            'ITERATIONS': [8, 10, 12, 15],
            'EMPTY_LOCATION_REWARD': [-0.02, -0.04, -0.06, -0.08]
        }
        
        self.results_history = []
        
        if backup_original:
            self._backup_original_file()
    
    def _backup_original_file(self):
        """Backup the original mdpAgents.py file"""
        original_path = os.path.join(self.pacman_dir, 'mdpAgents.py')
        backup_path = os.path.join(self.pacman_dir, 'mdpAgents_backup.py')
        
        try:
            with open(original_path, 'r') as f:
                content = f.read()
            with open(backup_path, 'w') as f:
                f.write(content)
            self.original_file = content
            print("Backed up original mdpAgents.py")
        except Exception as e:
            print("Warning: Could not backup original file: %s" % str(e))
    
    def _restore_original_file(self):
        """Restore the original mdpAgents.py file"""
        if self.original_file:
            try:
                original_path = os.path.join(self.pacman_dir, 'mdpAgents.py')
                with open(original_path, 'w') as f:
                    f.write(self.original_file)
                print("Restored original mdpAgents.py")
            except Exception as e:
                print("Error restoring original file: %s" % str(e))
    
    def _modify_parameters(self, new_params):
        """Modify mdpAgents.py with new parameter values"""
        original_path = os.path.join(self.pacman_dir, 'mdpAgents.py')
        
        try:
            with open(original_path, 'r') as f:
                content = f.read()
            
            # Replace parameter values
            modified_content = content
            for param_name, param_value in new_params.items():
                # Look for pattern like: PARAM_NAME = value
                import re
                pattern = r'(%s\s*=\s*)([-+]?\d*\.?\d+)' % param_name
                replacement = r'\g<1>%s' % param_value
                modified_content = re.sub(pattern, replacement, modified_content)
            
            with open(original_path, 'w') as f:
                f.write(modified_content)
            
            return True
            
        except Exception as e:
            print("Error modifying parameters: %s" % str(e))
            return False
    
    def test_parameter_configuration(self, params, test_layout='mediumClassic', test_games=25):
        """Test a specific parameter configuration"""
        print("Testing configuration: %s" % params)
        
        # Modify the parameters
        if not self._modify_parameters(params):
            return None
        
        try:
            # Run benchmark
            result = self.benchmark.run_single_test(test_layout, test_games, quiet=True)
            
            if result.get('success', False):
                result['parameters'] = params.copy()
                result['config_hash'] = hash(str(sorted(params.items())))
                
                print("  Result: %.1f%% win rate, %.1f avg score" % 
                      (result['win_rate'], result['average_score']))
                
                self.results_history.append(result)
                return result
            else:
                print("  Test failed: %s" % result.get('error', 'Unknown error'))
                return None
                
        except Exception as e:
            print("  Error during test: %s" % str(e))
            return None
        
        finally:
            # Always restore original parameters after test
            self._restore_original_file()
    
    def grid_search_optimization(self, max_combinations=50, test_games=25):
        """Perform grid search optimization across parameter space"""
        print("="*60)
        print("GRID SEARCH PARAMETER OPTIMIZATION")
        print("="*60)
        print("Baseline performance test...")
        
        # Test baseline first
        baseline_result = self.test_parameter_configuration(
            self.baseline_params, test_games=test_games
        )
        
        if not baseline_result:
            print("Failed to test baseline configuration!")
            return None
        
        baseline_win_rate = baseline_result['win_rate']
        print("Baseline: %.1f%% win rate" % baseline_win_rate)
        print()
        
        # Generate parameter combinations
        print("Generating parameter combinations...")
        param_names = list(self.search_spaces.keys())
        param_values = [self.search_spaces[name] for name in param_names]
        
        all_combinations = list(itertools.product(*param_values))
        
        # Limit combinations if too many
        if len(all_combinations) > max_combinations:
            print("Too many combinations (%d). Randomly sampling %d..." % 
                  (len(all_combinations), max_combinations))
            import random
            random.shuffle(all_combinations)
            combinations_to_test = all_combinations[:max_combinations]
        else:
            combinations_to_test = all_combinations
        
        print("Testing %d parameter combinations..." % len(combinations_to_test))
        
        best_result = baseline_result
        improvement_count = 0
        
        for i, combination in enumerate(combinations_to_test):
            print("\n--- Test %d/%d ---" % (i + 1, len(combinations_to_test)))
            
            # Create parameter dictionary
            test_params = dict(zip(param_names, combination))
            
            # Skip if same as baseline
            if test_params == self.baseline_params:
                continue
            
            result = self.test_parameter_configuration(test_params, test_games=test_games)
            
            if result and result['win_rate'] > best_result['win_rate']:
                improvement = result['win_rate'] - best_result['win_rate']
                print("  NEW BEST! Improvement: +%.2f%%" % improvement)
                best_result = result
                improvement_count += 1
            
            # Brief pause between tests
            time.sleep(0.5)
        
        # Final analysis
        self._analyze_grid_search_results(baseline_result, best_result, improvement_count)
        
        return best_result
    
    def smart_optimization(self, test_games=25, max_iterations=20):
        """Smart parameter optimization using gradient-based approach"""
        print("="*60)
        print("SMART PARAMETER OPTIMIZATION")
        print("="*60)
        
        current_params = self.baseline_params.copy()
        current_result = self.test_parameter_configuration(current_params, test_games=test_games)
        
        if not current_result:
            print("Failed to test baseline!")
            return None
        
        best_result = current_result
        print("Starting performance: %.1f%% win rate" % current_result['win_rate'])
        
        for iteration in range(max_iterations):
            print("\n--- Iteration %d/%d ---" % (iteration + 1, max_iterations))
            
            improved = False
            
            # Test small changes to each parameter
            for param_name in self.search_spaces:
                if param_name not in current_params:
                    continue
                
                current_value = current_params[param_name]
                search_values = self.search_spaces[param_name]
                
                # Find current value index
                if current_value in search_values:
                    current_idx = search_values.index(current_value)
                else:
                    # Find closest value
                    current_idx = min(range(len(search_values)), 
                                     key=lambda i: abs(search_values[i] - current_value))
                
                # Test adjacent values
                test_indices = []
                if current_idx > 0:
                    test_indices.append(current_idx - 1)
                if current_idx < len(search_values) - 1:
                    test_indices.append(current_idx + 1)
                
                for test_idx in test_indices:
                    test_params = current_params.copy()
                    test_params[param_name] = search_values[test_idx]
                    
                    print("  Testing %s: %s -> %s" % 
                          (param_name, current_value, search_values[test_idx]))
                    
                    result = self.test_parameter_configuration(test_params, test_games=test_games)
                    
                    if result and result['win_rate'] > best_result['win_rate']:
                        improvement = result['win_rate'] - best_result['win_rate']
                        print("    Improvement: +%.2f%%" % improvement)
                        current_params = test_params.copy()
                        best_result = result
                        improved = True
                        break
            
            if not improved:
                print("No improvement found in this iteration. Stopping.")
                break
        
        print("\n--- Smart Optimization Complete ---")
        print("Final performance: %.1f%% win rate" % best_result['win_rate'])
        print("Total improvement: +%.2f%%" % 
              (best_result['win_rate'] - current_result['win_rate']))
        
        return best_result
    
    def focused_tuning(self, focus_parameters, test_games=25):
        """Focus optimization on specific parameters"""
        print("="*60)
        print("FOCUSED PARAMETER TUNING")
        print("="*60)
        print("Focusing on parameters: %s" % ', '.join(focus_parameters))
        
        # Test baseline
        baseline_result = self.test_parameter_configuration(
            self.baseline_params, test_games=test_games
        )
        
        if not baseline_result:
            return None
        
        # Generate combinations for focused parameters only
        focused_values = [self.search_spaces[param] for param in focus_parameters]
        combinations = list(itertools.product(*focused_values))
        
        print("Testing %d combinations..." % len(combinations))
        
        best_result = baseline_result
        
        for i, combination in enumerate(combinations):
            print("\n--- Test %d/%d ---" % (i + 1, len(combinations)))
            
            # Create test parameters (baseline + focused changes)
            test_params = self.baseline_params.copy()
            for j, param_name in enumerate(focus_parameters):
                test_params[param_name] = combination[j]
            
            result = self.test_parameter_configuration(test_params, test_games=test_games)
            
            if result and result['win_rate'] > best_result['win_rate']:
                improvement = result['win_rate'] - best_result['win_rate']
                print("  NEW BEST! Improvement: +%.2f%%" % improvement)
                best_result = result
        
        return best_result
    
    def _analyze_grid_search_results(self, baseline, best, improvement_count):
        """Analyze grid search results"""
        print("\n" + "="*60)
        print("GRID SEARCH ANALYSIS")
        print("="*60)
        
        if best['win_rate'] > baseline['win_rate']:
            improvement = best['win_rate'] - baseline['win_rate']
            print("SUCCESS! Found better configuration")
            print("  Baseline: %.1f%% win rate" % baseline['win_rate'])
            print("  Best: %.1f%% win rate" % best['win_rate'])
            print("  Improvement: +%.2f%%" % improvement)
            print("  Improvements found: %d" % improvement_count)
            
            print("\nBest parameters:")
            for param, value in best['parameters'].items():
                baseline_value = baseline['parameters'][param]
                if value != baseline_value:
                    print("  %s: %s -> %s (CHANGED)" % (param, baseline_value, value))
                else:
                    print("  %s: %s" % (param, value))
        else:
            print("No improvement found. Baseline configuration is optimal for tested range.")
    
    def quick_sensitivity_analysis(self, test_games=15):
        """Quick analysis of parameter sensitivity"""
        print("="*60)
        print("PARAMETER SENSITIVITY ANALYSIS")
        print("="*60)
        
        baseline_result = self.test_parameter_configuration(
            self.baseline_params, test_games=test_games
        )
        
        if not baseline_result:
            return None
        
        sensitivity_results = {}
        
        for param_name in self.search_spaces:
            print("\n--- Analyzing %s ---" % param_name)
            
            param_results = []
            baseline_value = self.baseline_params[param_name]
            
            for test_value in self.search_spaces[param_name]:
                if test_value == baseline_value:
                    # Use baseline result
                    param_results.append((test_value, baseline_result['win_rate']))
                else:
                    test_params = self.baseline_params.copy()
                    test_params[param_name] = test_value
                    
                    result = self.test_parameter_configuration(test_params, test_games=test_games)
                    
                    if result:
                        param_results.append((test_value, result['win_rate']))
                        print("  %s = %s: %.1f%% win rate" % (param_name, test_value, result['win_rate']))
            
            # Calculate sensitivity
            if len(param_results) > 1:
                win_rates = [wr for _, wr in param_results]
                sensitivity = max(win_rates) - min(win_rates)
                sensitivity_results[param_name] = {
                    'sensitivity': sensitivity,
                    'results': param_results,
                    'best_value': max(param_results, key=lambda x: x[1])
                }
                print("  Sensitivity: %.2f%% range" % sensitivity)
        
        # Summary
        print("\n--- Sensitivity Summary ---")
        sorted_sensitivity = sorted(sensitivity_results.items(), 
                                   key=lambda x: x[1]['sensitivity'], reverse=True)
        
        print("Most sensitive parameters:")
        for param_name, data in sorted_sensitivity[:3]:
            print("  %s: %.2f%% range (best: %s)" % 
                  (param_name, data['sensitivity'], data['best_value'][0]))
        
        return sensitivity_results
    
    def save_tuning_results(self, filename=None):
        """Save tuning results to file"""
        if filename is None:
            filename = "parameter_tuning_results_%s.json" % datetime.now().strftime("%Y%m%d_%H%M%S")
        
        tuning_data = {
            'baseline_parameters': self.baseline_params,
            'search_spaces': self.search_spaces,
            'results_history': self.results_history,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(tuning_data, f, indent=2)
        
        print("Tuning results saved to: %s" % filename)
        return filename
    
    def recommend_best_parameters(self):
        """Recommend best parameters based on all tests"""
        if not self.results_history:
            print("No tuning results available for recommendations.")
            return None
        
        # Find best performing configuration
        best_result = max(self.results_history, key=lambda x: x.get('win_rate', 0))
        
        print("="*60)
        print("PARAMETER RECOMMENDATIONS")
        print("="*60)
        print("Best configuration found:")
        print("  Win rate: %.1f%%" % best_result['win_rate'])
        print("  Average score: %.1f" % best_result['average_score'])
        print()
        print("Recommended parameters:")
        
        for param, value in best_result['parameters'].items():
            baseline_value = self.baseline_params.get(param, 'N/A')
            if value != baseline_value:
                print("  %s = %s  # Was: %s" % (param, value, baseline_value))
            else:
                print("  %s = %s" % (param, value))
        
        print()
        print("To apply these parameters, update your mdpAgents.py file with the values above.")
        
        return best_result['parameters']


# Convenience functions for quick optimization
def quick_optimize(max_tests=20):
    """Quick parameter optimization"""
    tuner = ParameterTuner()
    return tuner.smart_optimization(test_games=15, max_iterations=max_tests)

def sensitivity_check():
    """Quick sensitivity analysis"""
    tuner = ParameterTuner()
    return tuner.quick_sensitivity_analysis(test_games=10)

def comprehensive_tuning():
    """Comprehensive parameter tuning"""
    tuner = ParameterTuner()
    
    print("Starting comprehensive parameter tuning...")
    print("This may take 30-60 minutes depending on your system.")
    
    # Start with sensitivity analysis
    tuner.quick_sensitivity_analysis(test_games=10)
    
    # Focus on most promising parameters
    focus_params = ['FOOD_REWARD', 'GHOST_REWARD', 'DANGER', 'GAMMA']
    tuner.focused_tuning(focus_params, test_games=20)
    
    # Final optimization
    best_result = tuner.smart_optimization(test_games=25)
    
    # Save results and recommendations
    tuner.save_tuning_results()
    tuner.recommend_best_parameters()
    
    return best_result

# Example usage
if __name__ == "__main__":
    print("Parameter Tuning Suite for MDP Pacman Agent")
    print("Current baseline: 60% win rate")
    print("Goal: Optimize parameters for 70%+ win rate")
    print()
    print("Available functions:")
    print("  - quick_optimize() - Fast optimization (~15 mins)")
    print("  - sensitivity_check() - Parameter sensitivity analysis (~10 mins)")
    print("  - comprehensive_tuning() - Full optimization (~60 mins)")
    print()
    print("Example usage:")
    print("  python2 parameter_tuning.py")
    print("  >>> result = quick_optimize()")
    print("  >>> tuner = ParameterTuner()")
    print("  >>> tuner.grid_search_optimization()")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--quick':
            print("\nRunning quick optimization...")
            result = quick_optimize()
        elif sys.argv[1] == '--sensitivity':
            print("\nRunning sensitivity analysis...")
            result = sensitivity_check()
        elif sys.argv[1] == '--comprehensive':
            print("\nRunning comprehensive tuning...")
            result = comprehensive_tuning()
        else:
            print("Unknown option: %s" % sys.argv[1])