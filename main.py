from tests.components.test_converger import TestConverger
import logging

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    t = TestConverger()
    t.test_converger()