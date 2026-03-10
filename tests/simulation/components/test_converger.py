from simulation.components import Converger, Splitter, Source, Sink, Conveyor, Component
from typing import List

import random

class TestConverger(object):
    def test_converger(self):
        converger = Converger('*')
        
        conveyor_1 = Conveyor(4, '1')
        conveyor_2 = Conveyor(3, '2')
        conveyor_3 = Conveyor(6, '3')
        conveyor_4 = Conveyor(10, '4')
        
        source_1 = Source(['A'], '1')
        source_2 = Source(['B'], '2')
        source_3 = Source(['C'], '3')
        
        source_1.connect_to(conveyor_1)
        source_2.connect_to(conveyor_2)
        source_3.connect_to(conveyor_3)
        
        conveyor_3.connect_to(converger)
        conveyor_2.connect_to(converger)
        conveyor_1.connect_to(converger)
        converger.connect_to(conveyor_4)
        
        components: List[Component] = [source_1, source_2, source_3, conveyor_1, conveyor_2, conveyor_3, conveyor_4, converger]
        trace = [tuple(
            [(item.id + 1) if item else 0 for item in component._items] for component in components[::-1]
        )]
        for _ in range(24):
            for component in components:
                if isinstance(component, (Source, Converger)):
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
                [(item.id + 1) if item else 0 for item in component._items] for component in components[::-1]
            ))
        
        assert trace[-1][1] == ([1, 1, 2, 2, 1, 3, 3, 2, 4, 4])
    
    def test_converger_order_invariance(self):
        random.seed(42)

        converger = Converger('*')
        conveyor_1 = Conveyor(4, '1')
        conveyor_2 = Conveyor(3, '2')
        conveyor_3 = Conveyor(6, '3')
        conveyor_4 = Conveyor(10, '4')
        source_1 = Source(['A'], '1')
        source_2 = Source(['B'], '2')
        source_3 = Source(['C'], '3')

        source_1.connect_to(conveyor_1)
        source_2.connect_to(conveyor_2)
        source_3.connect_to(conveyor_3)

        conveyor_3.connect_to(converger)
        conveyor_2.connect_to(converger)
        conveyor_1.connect_to(converger)
        converger.connect_to(conveyor_4)

        components: List[Component] = [source_1, source_2, source_3, conveyor_1, conveyor_2, conveyor_3, conveyor_4, converger]

        traces = set()

        for _ in range(1000):
            order = components.copy()
            random.shuffle(order)

            converger.__init__('*')
            conveyor_1.__init__(4, '1')
            conveyor_2.__init__(3, '2')
            conveyor_3.__init__(6, '3')
            conveyor_4.__init__(10, '4')
            source_1.__init__(['A'], '1')
            source_2.__init__(['B'], '2')
            source_3.__init__(['C'], '3')

            source_1.connect_to(conveyor_1)
            source_2.connect_to(conveyor_2)
            source_3.connect_to(conveyor_3)
            conveyor_3.connect_to(converger)
            conveyor_2.connect_to(converger)
            conveyor_1.connect_to(converger)
            converger.connect_to(conveyor_4)

            trace = [tuple(
                tuple((item.id + 1) if item else 0 for item in component._items)
                for component in components[::-1]
            )]

            for _ in range(24):
                for component in order:
                    if isinstance(component, (Source, Converger)):
                        component._phase_1_request()
                for component in order:
                    component._phase_2_adjudicate()
                for component in order:
                    component._phase_3_response()
                for component in order:
                    component._phase_4_send()
                for component in order:
                    component._phase_5_commit()

                trace.append(tuple(
                    tuple((item.id + 1) if item else 0 for item in component._items)
                    for component in components[::-1]
                ))

            assert (1, 1, 2, 2, 1, 3, 3, 2, 4, 4) in trace[-1]

            traces.add(tuple(trace))

        assert len(traces) <= 1, len(traces)
    
    def test_converger_cycle(self):
        source = Source(['A'])
        converger = Converger()
        conveyor = Conveyor(10)
        
        source.connect_to(converger)
        converger.connect_to(conveyor)
        conveyor.connect_to(converger)
        
        components: List[Component] = [source, converger, conveyor]
        trace = [tuple(
            tuple((item.id + 1) if item else 0 for item in component._items) for component in components[::-1]
        )]
        for _ in range(13):
            for component in components:
                if isinstance(component, (Source, Converger)):
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
                tuple((item.id + 1) if item else 0 for item in component._items) for component in components[::-1]
            ))
        
        assert trace[-2] == ((1, 2, 3, 4, 5, 6, 7, 8, 9, 10), (11,), (12,))
        assert trace[-1] == ((1, 2, 3, 4, 5, 6, 7, 8, 9, 10), (11,), (12,))
    
    def test_blockage_1(self):
        source = Source(['A'])
        sink = Sink()
        
        conveyors = [
            Conveyor(1, 'i'), 
            Conveyor(2, 'l'), 
            Conveyor(2, 'r'), 
            Conveyor(1, 'o')
        ]
        
        splitter = Splitter()
        converger = Converger()
        
        source.connect_to(conveyors[0])
        conveyors[0].connect_to(converger)
        converger.connect_to(splitter)
        splitter.connect_to(conveyors[1])
        splitter.connect_to(conveyors[3])
        splitter.connect_to(conveyors[2])
        conveyors[1].connect_to(converger)
        conveyors[2].connect_to(converger)
        conveyors[3].connect_to(sink)
        
        
        components: List[Component] = [source, *conveyors, converger, splitter, sink]
        trace = [tuple(
            tuple((item.id + 1) if item else 0 for item in component._items) for component in components[::-1]
        )]
        for _ in range(20):
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
            
            trace.append(tuple(
                tuple((item.id + 1) if item else 0 for item in component._items) for component in components[::-1]
            ))
        
        for t in trace:
            print(t)
    
    def test_blockage_2(self):
        conveyors = [
            Conveyor(1, 'i'), 
            Conveyor(1, '1'), 
            Conveyor(1, 'o'), 
            Conveyor(5, '2'), 
            Conveyor(1, '3'), 
            Conveyor(1, '4'), 
            Conveyor(5, '5'), 
            Conveyor(1, '6')
        ]
        
        convergers = [
            Converger('1'), 
            Converger('2')
        ]
        
        splitters = [
            Splitter('1'), 
            Splitter('2')
        ]
        
        source = Source(['A'])
        sink = Sink()
        
        source.connect_to(conveyors[0])
        conveyors[0].connect_to(convergers[0])
        convergers[0].connect_to(conveyors[1])
        conveyors[1].connect_to(splitters[0])
        splitters[0].connect_to(conveyors[2])
        conveyors[2].connect_to(sink)
        splitters[0].connect_to(conveyors[3])
        conveyors[3].connect_to(convergers[1])
        splitters[0].connect_to(splitters[1])
        splitters[1].connect_to(conveyors[7])
        conveyors[7].connect_to(convergers[1])
        splitters[1].connect_to(conveyors[5])
        conveyors[5].connect_to(convergers[0])
        convergers[1].connect_to(conveyors[6])
        conveyors[6].connect_to(convergers[0])
        
        components: List[Component] = [source, *conveyors, *convergers, *splitters, sink]
        trace = [tuple(
            tuple((item.id + 1) if item else 0 for item in component._items) for component in components[::-1]
        )]
        for _ in range(50):
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
            
            trace.append(tuple(
                tuple((item.id + 1) if item else 0 for item in component._items) for component in components[::-1]
            ))
        
        for t in trace:
            print(t)
        
    def test_blockage_3(self):
        source = Source(['A'])
        sink = Sink()
        
        conveyors = [
            Conveyor(1, '1'), 
            Conveyor(1, '2'), 
            Conveyor(1, '3'), 
            
            Conveyor(5, '4'), 
            
            Conveyor(1, '5'), 
            Conveyor(1, '6'), 
            Conveyor(1, '7'), 
            
            Conveyor(1, '8'), 
            Conveyor(1, '9'), 
            Conveyor(1, '10'), 
            
            Conveyor(5, '11'), 
        ]
        
        splitters = [
            Splitter('1'), 
            Splitter('2'), 
            Splitter('3'), 
        ]
        
        convergers = [
            Converger('1'), 
            Converger('2'), 
            Converger('3')
        ]
        
        source.connect_to(conveyors[0])
        
        convergers[0].connect_to(conveyors[4])
        convergers[1].connect_to(conveyors[3])
        convergers[2].connect_to(conveyors[6])
        
        splitters[0].connect_to(conveyors[2])
        splitters[0].connect_to(conveyors[1])
        
        splitters[1].connect_to(conveyors[5])
        splitters[1].connect_to(conveyors[9])
        
        splitters[2].connect_to(conveyors[7])
        splitters[2].connect_to(conveyors[10])
        splitters[2].connect_to(conveyors[8])
        
        conveyors[0].connect_to(convergers[0])
        conveyors[1].connect_to(convergers[0])
        conveyors[2].connect_to(convergers[1])
        conveyors[3].connect_to(convergers[0])
        conveyors[4].connect_to(splitters[2])
        conveyors[5].connect_to(splitters[0])
        conveyors[6].connect_to(convergers[1])
        conveyors[7].connect_to(sink)
        conveyors[8].connect_to(splitters[1])
        conveyors[9].connect_to(convergers[2])
        conveyors[10].connect_to(convergers[2])
        
        components: List[Component] = [source, sink, *convergers, *conveyors, *splitters]
        trace = [tuple(
            tuple((item.id + 1) if item else 0 for item in component._items) for component in components[::-1]
        )]
        for _ in range(500):
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
            
            trace.append(tuple(
                tuple((item.id + 1) if item else 0 for item in component._items) for component in components[::-1]
            ))
        
        for t in trace:
            print(' '.join('1' if i else '0' for i in t[6]))
    
    def test_blockage_4(self):
        pass

