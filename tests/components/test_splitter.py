from simulation.components import Splitter, Conveyor, Source, Component
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
        
        components: List[Component] = [source, conveyor_1, splitter, conveyor_2, conveyor_3]
        trace = [(
            [item.id + 1 if item else 0 for item in conveyor_3._items], 
            [item.id + 1 if item else 0 for item in conveyor_2._items], 
            [item.id + 1 if item else 0 for item in splitter._items], 
            [item.id + 1 if item else 0 for item in conveyor_1._items], 
            [item.id + 1 if item else 0 for item in source._items], 
        )]
        for _ in range(11):
            for component in components:
                component._phase_1_request()
            for component in components:
                component._phase_2_adjudicate()
            for component in components:
                component._phase_3_response()
            for component in components:
                component._phase_4_send()
            for component in components:
                component._phase_5_commit()
            trace.append((
                [item.id + 1 if item else 0 for item in conveyor_3._items], 
                [item.id + 1 if item else 0 for item in conveyor_2._items], 
                [item.id + 1 if item else 0 for item in splitter._items], 
                [item.id + 1 if item else 0 for item in conveyor_1._items], 
                [item.id + 1 if item else 0 for item in source._items], 
            ))
        
        assert trace[0] == ([0, 0, 0], [0, 0, 0], [0], [0, 0, 0], [1])
        assert trace[1] == ([0, 0, 0], [0, 0, 0], [0], [0, 0, 1], [2])
        assert trace[2] == ([0, 0, 0], [0, 0, 0], [0], [0, 1, 2], [3])
        assert trace[3] == ([0, 0, 0], [0, 0, 0], [0], [1, 2, 3], [4])
        assert trace[4] == ([0, 0, 0], [0, 0, 0], [1], [2, 3, 4], [5])
        assert trace[5] == ([0, 0, 1], [0, 0, 0], [2], [3, 4, 5], [6])
        assert trace[6] == ([0, 1, 0], [0, 0, 2], [3], [4, 5, 6], [7])
        assert trace[7] == ([1, 0, 3], [0, 2, 0], [4], [5, 6, 7], [8])
        assert trace[8] == ([1, 3, 0], [2, 0, 4], [5], [6, 7, 8], [9])
        assert trace[9] == ([1, 3, 5], [2, 4, 0], [6], [7, 8, 9], [10])
        assert trace[10] == ([1, 3, 5], [2, 4, 6], [7], [8, 9, 10], [11])
        assert trace[11] == ([1, 3, 5], [2, 4, 6], [7], [8, 9, 10], [11])