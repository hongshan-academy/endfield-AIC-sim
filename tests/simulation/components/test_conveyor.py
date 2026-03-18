from simulation.components import Conveyor, Source, Base
from simulation import Controller

from ..utils import trace_id

from typing import List

class TestConveyor(object):
    def test_conveyor(self):
        source = Source(['A', 'B', 'C'])
        conveyor_2 = Conveyor(capacity=3)
        conveyor_1 = Conveyor(capacity=2)
        conveyor_3 = Conveyor(capacity=1)
        # sink = Sink()
        
        source.connect_to(conveyor_3)
        conveyor_3.connect_to(conveyor_1)
        conveyor_1.connect_to(conveyor_2)
        
        components: List[Base] = [source, conveyor_3, conveyor_1, conveyor_2]
        controller = Controller(components)
        trace = [trace_id(components)]
        for _ in range(8):
            controller.step()
            trace.append(trace_id(components))
        
        assert trace[0] == ((1,), (0,), (0, 0), (0, 0, 0)), trace[0]
        assert trace[1] == ((2,), (1,), (0, 0), (0, 0, 0)), trace[1]
        assert trace[2] == ((3,), (2,), (0, 1), (0, 0, 0)), trace[2]
        assert trace[3] == ((4,), (3,), (1, 2), (0, 0, 0)), trace[3]
        assert trace[4] == ((5,), (4,), (2, 3), (0, 0, 1)), trace[4]
        assert trace[5] == ((6,), (5,), (3, 4), (0, 1, 2)), trace[5]
        assert trace[6] == ((7,), (6,), (4, 5), (1, 2, 3)), trace[6]
        assert trace[7] == ((7,), (6,), (4, 5), (1, 2, 3)), trace[7]