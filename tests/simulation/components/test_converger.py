from simulation.components import Converger, Splitter, Source, Sink, Conveyor, Component
from simulation import Controller, run_simulation
from ..utils import trace_id, trace_bool 

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
        controller = Controller(components)
        trace = [trace_id(components)]
        for _ in range(24):
            controller.step()
            trace.append(trace_id(components))
        
        assert trace[-1][-2] == (1, 1, 2, 2, 1, 3, 3, 2, 4, 4), trace
    
    def test_converger_order_invariance(self):
        random.seed(42)

        def _get_components_list() -> List[Component]:
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

            return [source_1, source_2, source_3, conveyor_1, conveyor_2, conveyor_3, conveyor_4, converger]
        
        traces = set()

        for _ in range(1000):
            components = _get_components_list()
            order = components.copy()
            random.shuffle(order)
    
            controller = Controller(order)
            trace = [trace_id(components)]

            for _ in range(24):
                controller.step()
                trace.append(trace_id(components))

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
        controller = Controller(components)
        trace = [trace_id(components)]
        for _ in range(13):
            controller.step()
            trace.append(trace_id(components))
        
        assert trace[-2] == ((12,), (11,), (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)), trace
        assert trace[-1] == ((12,), (11,), (1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
    
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
        controller = Controller(components)
        trace = [trace_bool(components)]
        for _ in range(20):
            controller.step()
            trace.append(trace_bool(components))

        assert tuple(t[-1][0] for t in trace[-6:]) in {
            (0, 0, 1, 0, 0, 1), 
            (0, 1, 0, 0, 1, 0), 
            (1, 0, 0, 1, 0, 0)
        }    
    
    def test_blockage_2(self):
        conveyors = [
            Conveyor(1, '0'), 
            Conveyor(1, '1'), 
            Conveyor(1, '2'), 
            Conveyor(5, '3'), 
            Conveyor(1, '4'), 
            Conveyor(1, '5'), 
            Conveyor(1, '6'), 
            Conveyor(5, '7')
        ]
        
        convergers = [
            Converger('0'), 
            Converger('1')
        ]
        
        splitters = [
            Splitter('0'), 
            Splitter('1')
        ]
        
        source = Source(['A'])
        sink = Sink()
        
        source.connect_to(conveyors[0])
        conveyors[0].connect_to(convergers[0])
        convergers[0].connect_to(conveyors[1])
        conveyors[1].connect_to(splitters[0])
        splitters[0].connect_to(conveyors[4])
        splitters[0].connect_to(conveyors[3])
        splitters[0].connect_to(conveyors[2])
        conveyors[2].connect_to(sink)
        conveyors[3].connect_to(convergers[1])
        convergers[1].connect_to(conveyors[7])
        conveyors[7].connect_to(convergers[0])
        conveyors[4].connect_to(splitters[1])
        splitters[1].connect_to(conveyors[5])
        conveyors[5].connect_to(convergers[0])
        splitters[1].connect_to(conveyors[6])
        conveyors[6].connect_to(convergers[1])
        
        components: List[Component] = [source, *conveyors, *convergers, *splitters, sink]
        controller = Controller(components)
        trace = [trace_bool(components)]
        for _ in range(100):
            controller.step()            
            trace.append(trace_bool(components))
        
        assert ((1,), (1,), (1,), (1,), (1, 1, 1, 1, 1), (0,), (0,), (0,), (1, 1, 1, 1, 1), (1,), (1,), (1,), (1,), (0,)) in trace
        assert ((1,), (1,), (1,), (0,), (1, 1, 1, 1, 1), (1,), (0,), (0,), (1, 1, 1, 1, 1), (1,), (1,), (1,), (0,), (1,)) in trace

        assert tuple(t[-1][0] for t in trace[-10:]) in {
            (1, 0, 0, 1, 0, 1, 0, 0, 1, 0), 
            (0, 0, 1, 0, 1, 0, 0, 1, 0, 1), 
            (0, 1, 0, 1, 0, 0, 1, 0, 1, 0), 
            (1, 0, 1, 0, 0, 1, 0, 1, 0, 0), 
            (0, 1, 0, 0, 1, 0, 1, 0, 0, 1)
        }
        
    def test_blockage_3(self):
        source = Source(['A'])
        sink = Sink()
        
        conveyors = [
            Conveyor(1, '0'), 
            Conveyor(1, '1'), 
            Conveyor(1, '2'), 
            
            Conveyor(5, '3'), 
            
            Conveyor(1, '4'), 
            Conveyor(1, '5'), 
            Conveyor(1, '6'), 
            
            Conveyor(1, '7'), 
            Conveyor(1, '8'), 
            Conveyor(1, '9'), 
            
            Conveyor(5, '10'), 
        ]
        
        splitters = [
            Splitter('0'), 
            Splitter('1'), 
            Splitter('2'), 
        ]
        
        convergers = [
            Converger('0'), 
            Converger('1'), 
            Converger('2')
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
        
        components: List[Component] = [source, *conveyors, *convergers, *splitters, sink]
        controller = Controller(components)
        trace = [trace_bool(components)]
        for _ in range(100):
            controller.step()
            trace.append(trace_bool(components))
        
        assert tuple(t[-1][0] for t in trace[-14:]) in {
            (1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0), 
            (0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1), 
            (0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0), 
            (1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0), 
            (0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1), 
            (1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0), 
            (0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1), 
        }
            
    # TODO: realize `StorageBox`
    # def test_blockage_4(self):
    #     source = Source(['A'])
    #     sink_1 = Sink()
    #     sink_2 = Sink()

    def test_priority(self):
        source_0 = Source(['A'])
        source_1 = Source(['B'])
        sink = Sink()
        
        conveyor_0 = Conveyor(1, '0')
        conveyor_1 = Conveyor(1, '1')
        conveyor_2 = Conveyor(1, '1')
        
        splitter = Splitter()
        converger = Converger()
        
        source_0.connect_to(conveyor_0)
        source_1.connect_to(conveyor_1)
        
        splitter.connect_to(converger)
        
        conveyor_1.connect_to(splitter)
        conveyor_0.connect_to(converger)
        converger.connect_to(conveyor_2)
        conveyor_2.connect_to(sink)
        
        components: List[Component] = [source_0, source_1, conveyor_0, conveyor_1, conveyor_2, converger, splitter, sink]
        run_simulation(components, 20)
        
        assert sink._received_items[0].name == 'A'
        assert [i.name for i in sink._received_items[-10:]] == ['B'] * 10
        
        