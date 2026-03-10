from simulation.components import Conveyor, Source, Component

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
        
        components: List[Component] = [source, conveyor_3, conveyor_1, conveyor_2]
        trace = [(
            [item.id + 1 if item else 0 for item in conveyor_2._items], 
            [item.id + 1 if item else 0 for item in conveyor_1._items], 
            [item.id + 1 if item else 0 for item in conveyor_3._items], 
            [item.id + 1 if item else 0 for item in source._items], 
        )]
        for _ in range(8):
            for component in components:
                component._phase_1_request()
            for component in components:
                component._phase_2_response()
            for component in components:
                component._phase_3_send()
            for component in components:
                component._phase_4_commit()
            trace.append((
                [item.id + 1 if item else 0 for item in conveyor_2._items], 
                [item.id + 1 if item else 0 for item in conveyor_1._items], 
                [item.id + 1 if item else 0 for item in conveyor_3._items], 
                [item.id + 1 if item else 0 for item in source._items], 
            ))
        
        assert trace[0] == ([0, 0, 0], [0, 0], [0], [1])
        assert trace[1] == ([0, 0, 0], [0, 0], [1], [2])
        assert trace[2] == ([0, 0, 0], [0, 1], [2], [3])
        assert trace[3] == ([0, 0, 0], [1, 2], [3], [4])
        assert trace[4] == ([0, 0, 1], [2, 3], [4], [5])
        assert trace[5] == ([0, 1, 2], [3, 4], [5], [6])
        assert trace[6] == ([1, 2, 3], [4, 5], [6], [7])
        assert trace[7] == ([1, 2, 3], [4, 5], [6], [7])