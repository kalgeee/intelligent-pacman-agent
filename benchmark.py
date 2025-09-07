# benchmark.py - Benchmark MDP Agent Performance
# Clean Python 2.7 compatible version

import os
import sys
import time
import json
import subprocess
from datetime import datetime

class MDPBenchmark:
    """Comprehensive benchmarking suite for MDP Pacman agent"""
    
    def __init__(self, pacman_directory="."):
        self.pacman_dir = pacman_directory
        self.results = {}
        self.test_configurations = {
            'layouts': ['smallGrid', 'mediumClassic', 'openClassic', 'trappedClassic'],
            'game_counts': [10, 25, 50],
            'time_limits': {'smallGrid': 300, 'mediumClassic': 1500, 'others': 2000}
        }
    
    def run_single_test(self, layout, num_games, agent_class="MDPAgent", quiet=True):
        """Run a single benchmark test and return results"""
        print("Running %d games on %s layout..." % (num_games, layout))
        
        # Construct command
        cmd = [
            'python2', 'pacman.py',
            '-p', agent_class,
            '-l', layout,
            '-n', str(num_games)
        ]
        
        if quiet:
            cmd.append('-q')
        
        start_time = time.time()
        
        try:
            # Run the test
            result = subprocess.Popen(
                cmd, 
                cwd=self.pacman_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = result.communicate()
            end_time = time.time()
            
            # Parse results from output
            output_lines = stdout.split('\n')
            wins = 0
            total_score = 0
            scores = []
            
            # Look for win/loss indicators and scores
            for line in output_lines:
                if 'Pacman emerges victorious' in line or 'WIN' in line:
                    wins += 1
                elif 'Game' in line and 'finished' in line:
                    # Count completed games for win rate calculation
                    pass
                elif 'Score:' in line:
                    try:
                        score = int(line.split('Score:')[1].strip())
                        scores.append(score)
                        total_score += score
                    except:
                        pass
            
            # Alternative win detection - look for positive final scores as wins
            if wins == 0 and scores:
                # If no explicit win messages, infer wins from positive scores
                wins = sum(1 for score in scores if score > 0)
            
            # Calculate metrics
            win_rate = (float(wins) / float(num_games)) * 100.0 if num_games > 0 else 0.0
            avg_score = float(total_score) / float(num_games) if num_games > 0 else 0.0
            execution_time = end_time - start_time
            
            result_data = {
                'layout': layout,
                'num_games': num_games,
                'wins': wins,
                'win_rate': win_rate,
                'total_score': total_score,
                'average_score': avg_score,
                'scores': scores,
                'execution_time': execution_time,
                'games_per_second': num_games / execution_time if execution_time > 0 else 0,
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'error': None
            }
            
            print("  Results: %d/%d wins (%.1f%%), avg score: %.1f" % 
                  (wins, num_games, win_rate, avg_score))
            
            return result_data
            
        except Exception as e:
            print("  ERROR: %s" % str(e))
            return {
                'layout': layout,
                'num_games': num_games,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_comprehensive_benchmark(self, save_results=True):
        """Run comprehensive benchmark across all configurations"""
        print("="*60)
        print("COMPREHENSIVE MDP AGENT BENCHMARK")
        print("="*60)
        print("Testing layouts: %s" % ', '.join(self.test_configurations['layouts']))
        print("Game counts: %s" % ', '.join(map(str, self.test_configurations['game_counts'])))
        print()
        
        all_results = []
        
        for layout in self.test_configurations['layouts']:
            print("\n--- Testing %s Layout ---" % layout)
            
            layout_results = []
            
            for num_games in self.test_configurations['game_counts']:
                result = self.run_single_test(layout, num_games)
                layout_results.append(result)
                all_results.append(result)
                
                # Brief pause between tests
                time.sleep(1)
            
            # Layout summary
            successful_tests = [r for r in layout_results if r.get('success', False)]
            if successful_tests:
                avg_win_rate = sum(r['win_rate'] for r in successful_tests) / len(successful_tests)
                avg_score = sum(r['average_score'] for r in successful_tests) / len(successful_tests)
                print("  %s Summary: %.1f%% win rate, %.1f avg score" % 
                      (layout, avg_win_rate, avg_score))
        
        # Overall analysis
        self._analyze_benchmark_results(all_results)
        
        if save_results:
            filename = "benchmark_results_%s.json" % datetime.now().strftime("%Y%m%d_%H%M%S")
            self.save_results(all_results, filename)
        
        return all_results
    
    def run_statistical_analysis(self, layout='mediumClassic', num_trials=5, games_per_trial=25):
        """Run multiple trials for statistical significance"""
        print("="*60)
        print("STATISTICAL ANALYSIS - %s Layout" % layout)
        print("="*60)
        print("Running %d trials of %d games each..." % (num_trials, games_per_trial))
        
        trial_results = []
        
        for trial in range(num_trials):
            print("\nTrial %d/%d:" % (trial + 1, num_trials))
            result = self.run_single_test(layout, games_per_trial)
            trial_results.append(result)
        
        # Statistical analysis
        win_rates = [r['win_rate'] for r in trial_results if r.get('success', False)]
        avg_scores = [r['average_score'] for r in trial_results if r.get('success', False)]
        
        if win_rates:
            print("\n--- Statistical Summary ---")
            print("Win Rate Statistics:")
            print("  Mean: %.2f%%" % (sum(win_rates) / len(win_rates)))
            print("  Min: %.2f%%" % min(win_rates))
            print("  Max: %.2f%%" % max(win_rates))
            print("  Range: %.2f%%" % (max(win_rates) - min(win_rates)))
            
            # Standard deviation calculation
            mean_wr = sum(win_rates) / len(win_rates)
            variance = sum((wr - mean_wr) ** 2 for wr in win_rates) / len(win_rates)
            std_dev = variance ** 0.5
            print("  Std Dev: %.2f%%" % std_dev)
            
            print("\nScore Statistics:")
            print("  Mean: %.1f" % (sum(avg_scores) / len(avg_scores)))
            print("  Min: %.1f" % min(avg_scores))
            print("  Max: %.1f" % max(avg_scores))
            
            # Confidence interval (95%, assuming normal distribution)
            confidence_margin = 1.96 * (std_dev / (len(win_rates) ** 0.5))
            print("  95%% Confidence Interval: %.2f%% +/- %.2f%%" % (mean_wr, confidence_margin))
        
        return trial_results
    
    def _analyze_benchmark_results(self, results):
        """Analyze and summarize benchmark results"""
        print("\n" + "="*60)
        print("BENCHMARK ANALYSIS SUMMARY")
        print("="*60)
        
        successful_results = [r for r in results if r.get('success', False)]
        
        if not successful_results:
            print("No successful test results to analyze.")
            return
        
        # Group by layout
        layout_performance = {}
        for result in successful_results:
            layout = result['layout']
            if layout not in layout_performance:
                layout_performance[layout] = []
            layout_performance[layout].append(result)
        
        # Performance summary by layout
        print("Performance by Layout:")
        for layout, layout_results in layout_performance.items():
            win_rates = [r['win_rate'] for r in layout_results]
            avg_win_rate = sum(win_rates) / len(win_rates)
            
            scores = [r['average_score'] for r in layout_results]
            avg_score = sum(scores) / len(scores)
            
            print("  %s: %.1f%% win rate, %.1f avg score (%d tests)" % 
                  (layout, avg_win_rate, avg_score, len(layout_results)))
        
        # Overall performance
        overall_win_rate = sum(r['win_rate'] for r in successful_results) / len(successful_results)
        overall_avg_score = sum(r['average_score'] for r in successful_results) / len(successful_results)
        
        print("\nOverall Performance:")
        print("  Average win rate across all tests: %.1f%%" % overall_win_rate)
        print("  Average score across all tests: %.1f" % overall_avg_score)
        
        # Performance recommendations
        print("\nPerformance Assessment:")
        if overall_win_rate >= 80:
            print("  EXCELLENT: Agent performs very well across layouts")
        elif overall_win_rate >= 65:
            print("  GOOD: Solid performance with room for optimization")
        elif overall_win_rate >= 50:
            print("  MODERATE: Decent performance, consider parameter tuning")
        else:
            print("  NEEDS IMPROVEMENT: Significant optimization required")
    
    def save_results(self, results, filename):
        """Save benchmark results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print("\nBenchmark results saved to: %s" % filename)


def quick_benchmark(layout='mediumClassic', num_games=25):
    """Quick benchmark function for immediate testing"""
    benchmark = MDPBenchmark()
    return benchmark.run_single_test(layout, num_games)

def compare_agents(agent1_class="MDPAgent", agent2_class="RandomAgent", 
                  layout='mediumClassic', num_games=25):
    """Compare two different agent implementations"""
    benchmark = MDPBenchmark()
    
    print("Comparing %s vs %s on %s" % (agent1_class, agent2_class, layout))
    
    result1 = benchmark.run_single_test(layout, num_games, agent1_class)
    result2 = benchmark.run_single_test(layout, num_games, agent2_class)
    
    if result1.get('success') and result2.get('success'):
        print("\nComparison Results:")
        print("  %s: %.1f%% win rate, %.1f avg score" % 
              (agent1_class, result1['win_rate'], result1['average_score']))
        print("  %s: %.1f%% win rate, %.1f avg score" % 
              (agent2_class, result2['win_rate'], result2['average_score']))
        
        win_rate_diff = result1['win_rate'] - result2['win_rate']
        score_diff = result1['average_score'] - result2['average_score']
        
        print("  Difference: %.1f%% win rate, %.1f score" % (win_rate_diff, score_diff))
    
    return result1, result2

# Example usage
if __name__ == "__main__":
    print("MDP Agent Benchmark Suite")
    print("Available functions:")
    print("  - quick_benchmark(layout, num_games)")
    print("  - compare_agents(agent1, agent2, layout, num_games)")
    print("  - MDPBenchmark().run_comprehensive_benchmark()")
    print("  - MDPBenchmark().run_statistical_analysis()")
    print()
    print("Example usage:")
    print("  python2 benchmark.py")
    print("  >>> quick_benchmark('mediumClassic', 25)")
    print("  >>> benchmark = MDPBenchmark()")
    print("  >>> benchmark.run_comprehensive_benchmark()")
    
    # Run a quick demo if script is executed directly
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        print("\nRunning demo benchmark...")
        result = quick_benchmark('smallGrid', 10)
        print("Demo completed. Result: %s" % result)