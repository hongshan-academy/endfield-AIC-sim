from tests.simulation.components.test_converger import TestConverger
import logging

if __name__ == '__main__':
    logging.basicConfig(
        filename='simulation.log', 
        filemode='w', 
        level=logging.DEBUG
    )
    
    t = TestConverger()
    # t.test_blockage_3()
    t.test_converger_cycle()