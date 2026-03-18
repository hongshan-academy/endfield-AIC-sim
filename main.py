# from tests.simulation.components.test_converger import TestConverger
# from tests.simulation.components.test_conveyor import TestConveyor
# from tests.simulation.components.test_splitter import TestSplitter

from simulation import Component, Splitter, Conveyor, Source, Sink
from tests.simulation.utils import trace_bool, trace_id
from typing import List
import logging


def main():
    source = Source(['A'])
    sink   = Sink()
    
    conveyors = [
        Conveyor(3, '0'), 
        Conveyor(3, '1'), 
        Conveyor(3, '2')
    ]
    splitter = Splitter()

    source.connect_to(conveyors[0])
    
    # splitter.connect_to(conveyors[1])
    splitter.connect_to(conveyors[2])
    
    conveyors[0].connect_to(splitter)
    conveyors[2].connect_to(sink)
    
    components: List[Component] = [source, *conveyors, sink]
    
    for _ in range(40):
        for component in components:
            component.phase_1_tick()
        splitter.phase_5_tick()
        for component in components:
            component.phase_2_tick()        
        splitter.phase_1_tick()        
        for component in components:
            component.phase_3_tick()
        splitter.phase_2_tick()
        
        print('1/2:', trace_id(components + [splitter]))
        
        for component in components:
            component.phase_4_tick()
        splitter.phase_3_tick()
        for component in components:
            component.phase_5_tick()
        splitter.phase_4_tick()

        print('2/2:', trace_id(components + [splitter]))

if __name__ == '__main__':
    logging.basicConfig(
        filename='simulation.log', 
        filemode='w', 
        level=logging.DEBUG
    )
    
    main()
    
    # t = TestConveyor()
    # t = TestSplitter()
    # t = TestConverger()
    # t.test_blockage_3()
    # t.test_converger_cycle()
    # t.test_splitter()
    # t.test_converger()
    # t.test_priority()
    # t.test_conveyor()