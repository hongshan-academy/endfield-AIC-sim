from simulation.components import Converger, Splitter, Source, Sink, Conveyor, Component
from typing import List

class TestConverger(object):
    def test_converger(self):
        converger = Converger('*')
        
        conveyor_1 = Conveyor(3, '1')
        conveyor_2 = Conveyor(3, '2')
        conveyor_3 = Conveyor(3, '3')
        conveyor_4 = Conveyor(3, '4')
        
        source_1 = Source(['A'], '1')
        source_2 = Source(['B'], '2')
        source_3 = Source(['C'], '3')
        
        source_1.connect_to(conveyor_1)
        source_2.connect_to(conveyor_2)
        source_3.connect_to(conveyor_3)
        
        conveyor_1.connect_to(converger)
        conveyor_2.connect_to(converger)
        conveyor_3.connect_to(converger)
        converger.connect_to(conveyor_4)
        
        components: List[Component] = [source_1, source_2, source_3, conveyor_1, conveyor_2, conveyor_3, converger, conveyor_4]
        trace = [tuple(
            ['%s.%d' % (item.name, item.id + 1) if item else '0' for item in component._items] for component in components[::-1]
        )]
        for _ in range(8):
            for component in components:
                if isinstance(component, Source):
                    component._phase_1_request()
            for component in components:
                component._phase_2_response()
            for component in components:
                component._phase_3_send()
            for component in components:
                component._phase_4_commit()
            trace.append(tuple(
                ['%s.%d' % (item.name, item.id + 1) if item else '0' for item in component._items] for component in components[::-1]
            ))
        
        for t in trace:
            print(t)
    
    def test_ring(self):
        pass
    
    def test_blockage_1(self):
        pass
    
    def test_blockage_2(self):
        pass

