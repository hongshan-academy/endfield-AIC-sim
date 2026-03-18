from simulation.components import Splitter, Conveyor, Source, Base
from simulation import Controller

from ..utils import trace_id

from typing import List

class TestSplitter(object):
    def test_splitter(self):
        source = Source(['A', 'B', 'C'])
        conveyor_1 = Conveyor(capacity=3)
        splitter   = Splitter()
        conveyor_2 = Conveyor(capacity=3)
        conveyor_3 = Conveyor(capacity=3)
        
        source.connect_to(conveyor_1)
        conveyor_1.connect_to(splitter)
        splitter.connect_to(conveyor_2)
        splitter.connect_to(conveyor_3)
        
        components: List[Base] = [source, conveyor_1, splitter, conveyor_2, conveyor_3]
        controller = Controller(components)
        trace = [trace_id(components)]
        for _ in range(11):
            controller.step()
            trace.append(trace_id(components))
                
        assert trace[0] == ((1,), (0, 0, 0), (0,), (0, 0, 0), (0, 0, 0)), trace[0]
        assert trace[1] == ((2,), (0, 0, 1), (0,), (0, 0, 0), (0, 0, 0)), trace[1]
        assert trace[2] == ((3,), (0, 1, 2), (0,), (0, 0, 0), (0, 0, 0)), trace[2]
        assert trace[3] == ((4,), (1, 2, 3), (0,), (0, 0, 0), (0, 0, 0)), trace[3]
        assert trace[4] == ((5,), (2, 3, 4), (1,), (0, 0, 0), (0, 0, 0)), trace[4]
        assert trace[5] == ((6,), (3, 4, 5), (2,), (0, 0, 0), (0, 0, 1)), trace[5]
        assert trace[6] == ((7,), (4, 5, 6), (3,), (0, 0, 2), (0, 1, 0)), trace[6]
        assert trace[7] == ((8,), (5, 6, 7), (4,), (0, 2, 0), (1, 0, 3)), trace[7]
        assert trace[8] == ((9,), (6, 7, 8), (5,), (2, 0, 4), (1, 3, 0)), trace[8]
        assert trace[9] == ((10,), (7, 8, 9), (6,), (2, 4, 0), (1, 3, 5)), trace[9]
        assert trace[10] == ((11,), (8, 9, 10), (7,), (2, 4, 6), (1, 3, 5)), trace[10]
        assert trace[11] == ((11,), (8, 9, 10), (7,), (2, 4, 6), (1, 3, 5)), trace[11]