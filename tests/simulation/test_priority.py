from simulation import Converger, Conveyor, Splitter, Sink, Source
from simulation import Controller

from .utils import trace_type

class TestPriority(object):
    def test_priority_1(self):
        conveyors = [
            Conveyor(2, '0'), 
            Conveyor(2, '1'), 
            Conveyor(20, '2'), 
            Conveyor(20, '3'), 
        ]
        
        splitter = Splitter()
        converger = Converger()
        
        sources = [
            Source(['A'], '0'), 
            Source(['B'], '1')
        ]
        
        sinks = [
            Sink('0'), 
            Sink('1')
        ]
        
        splitter.connect_to(converger)
        splitter.connect_to(conveyors[3])
        
        converger.connect_to(conveyors[2])
        
        sources[0].connect_to(conveyors[0])
        sources[1].connect_to(conveyors[1])
        
        conveyors[0].connect_to(converger)
        conveyors[1].connect_to(splitter)
        conveyors[2].connect_to(sinks[0])
        conveyors[3].connect_to(sinks[1])
        
        components = [*sources, *conveyors, splitter, converger, *sinks]
        controller = Controller(components)
        trace = [trace_type(components)]
        for _ in range(91):
            controller.step()
            trace.append(trace_type(components))
        
        for t in trace:
            for c in t:
                for i in c:
                    print(i, end='')
                print(end=' ')
            print()