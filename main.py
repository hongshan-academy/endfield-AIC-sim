from tests.simulation.components.test_converger import TestConverger
# from tests.simulation.components.test_conveyor import TestConveyor
# from tests.simulation.components.test_splitter import TestSplitter
import logging

if __name__ == '__main__':
    logging.basicConfig(
        filename='simulation.log', 
        filemode='w', 
        level=logging.DEBUG
    )
    
    # t = TestSplitter()
    t = TestConverger()
    # t.test_blockage_3()
    # t.test_converger_cycle()
    # t.test_splitter()
    # t.test_converger()
    t.test_priority()