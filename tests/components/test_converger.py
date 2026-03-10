from simulation.components import Converger, Splitter, Source, Sink, Conveyor, Component
from typing import List

class TestConverger(object):
    def test_converger(self):
        converger = Converger('*')
        
        conveyor_1 = Conveyor(5, '1')
        conveyor_2 = Conveyor(3, '2')
        conveyor_3 = Conveyor(3, '3')
        conveyor_5 = Conveyor(2, '5')
        conveyor_4 = Conveyor(10, '4')
        
        source_1 = Source(['A'], '1')
        source_2 = Source(['B'], '2')
        source_3 = Source(['C'], '3')
        
        source_1.connect_to(conveyor_1)
        source_2.connect_to(conveyor_5)
        source_3.connect_to(conveyor_3)
        
        conveyor_5.connect_to(conveyor_2)
        
        conveyor_1.connect_to(converger)
        conveyor_2.connect_to(converger)
        conveyor_3.connect_to(converger)
        converger.connect_to(conveyor_4)
        
        components: List[Component] = [source_1, source_2, source_3, conveyor_1, conveyor_5, conveyor_2, conveyor_3, converger, conveyor_4]
        trace = [tuple(
            [item.id + 1 if item else 0 for item in component._items] for component in components[::-1]
        )]
        for _ in range(10):
            for component in components:
                if isinstance(component, Source):
                    component._phase_1_request()
            for component in components:
                component._phase_2_adjudicate()
            for component in components:
                component._phase_3_response()
            for component in components:
                component._phase_4_send()
            for component in components:
                component._phase_5_commit()
            trace.append(tuple(
                [item.id + 1 if item else 0 for item in component._items] for component in components[::-1]
            ))
        
        for t in trace:
            print(t)
        # assert trace[0] == ([0, 0, 0], [0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [1], [1], [1])
        # assert trace[1] == ([0, 0, 0], [0], [0, 0, 1], [0, 0, 1], [0, 0, 1], [2], [2], [2])
        # assert trace[2] == ([0, 0, 0], [0], [0, 1, 2], [0, 1, 2], [0, 1, 2], [3], [3], [3])
        # assert trace[3] == ([0, 0, 0], [0], [1, 2, 3], [1, 2, 3], [1, 2, 3], [4], [4], [4])
        # assert trace[4] == ([0, 0, 0], [1], [1, 2, 3], [2, 3, 4], [1, 2, 3], [5], [5], [5])
        # assert trace[5] == ([0, 0, 1], [1], [2, 3, 5], [2, 3, 4], [1, 2, 3], [6], [6], [6])
        # assert trace[6] == ([0, 1, 1], [1], [2, 3, 5], [2, 3, 4], [2, 3, 6], [7], [7], [7])
        # assert trace[7] == ([1, 1, 1], [2], [2, 3, 5], [3, 4, 7], [2, 3, 6], [8], [8], [8]), ([1, 1, 1], [2], [2, 3, 5], [3, 4, 7], [2, 3, 6], [8], [8], [8])
    
    def test_ring(self):
        pass
    
    def test_blockage_1(self):
        pass
    
    def test_blockage_2(self):
        pass

