# simulation/test/test_simulation.py

import unittest
from typing import List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..item import Item
from ..controller import Controller
from ..components import Source, Sink, Conveyor, Splitter, Converger


class TestConveyorChain(unittest.TestCase):    
    def setUp(self):
        self.controller = Controller()
    
    def test_conveyor_latency(self):
        # Create components
        source = Source([Item("A", i) for i in range(1, 100)])
        conveyor_a = Conveyor(length=3)
        conveyor_b = Conveyor(length=3)
        sink = Sink()
        
        # Connect components: Source → ConveyorA → ConveyorB → Sink
        conveyor_a.connect([source])
        conveyor_b.connect([conveyor_a])
        sink.connect([conveyor_b])
        
        # Add to controller
        self.controller.set_components([source, conveyor_a, conveyor_b, sink])
        self.controller.initialize()
        
        # Run simulation and track item positions
        trace = []
        for tick in range(10):
            self.controller.step()
            
            # Record buffer states
            buffer_a = [item.id if item else 0 for item in conveyor_a.get_buffer()]
            buffer_b = [item.id if item else 0 for item in conveyor_b.get_buffer()]
            trace.append((buffer_a, buffer_b, sink.items_received))
        
        # Verify trace matches expected behavior
        # Tick 0: [0,0,0] [0,0,0] received=0
        # Tick 1: [1,0,0] [0,0,0] received=0
        # Tick 2: [2,1,0] [0,0,0] received=0
        # Tick 3: [3,2,1] [0,0,0] received=0
        # Tick 4: [4,3,2] [1,0,0] received=0 *
        # Tick 5: [5,4,3] [2,1,0] received=0
        # Tick 6: [6,5,4] [3,2,1] received=0
        # Tick 7: [7,6,5] [4,3,2] received=1 *
        
        self.assertEqual(trace[0], ([0, 0, 0], [0, 0, 0], 0))
        self.assertEqual(trace[1], ([1, 0, 0], [0, 0, 0], 0))
        self.assertEqual(trace[3], ([3, 2, 1], [0, 0, 0], 0))
        self.assertEqual(trace[4], ([4, 3, 2], [1, 0, 0], 0))
        self.assertEqual(trace[7], ([7, 6, 5], [4, 3, 2], 1))

def run_all_tests():
    """
    Runs all test cases and prints summary.
    
    Returns:
        True if all tests passed, False otherwise.
    """
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestConveyorChain))
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print("=" * 60)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_all_tests()