from simulation.units import StorageBox
from simulation import Controller, Sink, Source, Conveyor, Splitter, Converger
from ..utils import trace_bool, trace_id, trace_type

class TestStorageBox(object):
    def test_storage_box_1(self):
        source_0 = Source(['A'])
        source_1 = Source(['B'])
        
        conveyors = [
            Conveyor(1, '0'), 
            Conveyor(2, '1'), 
            Conveyor(2, '2'), 
            Conveyor(1, '3'), 
            Conveyor(4, '4'), 
            Conveyor(6, '5'), 
            Conveyor(6, '6'), 
            Conveyor(6, '7'), 
        ]
        
        splitter  = Splitter()
        converger = Converger()
        
        storage_box = StorageBox()
        
        source_0.connect_to(conveyors[0])
        source_1.connect_to(conveyors[4])
        
        sink_0 = Sink('0')
        sink_1 = Sink('1')
        
        splitter.connect_to(conveyors[1])
        splitter.connect_to(conveyors[3])
        splitter.connect_to(conveyors[2])
        converger.connect_to(splitter)
        
        storage_box.connect_to(conveyors[5])
        storage_box.connect_to(conveyors[6])
        storage_box.connect_to(conveyors[7])
        
        conveyors[0].connect_to(converger)
        conveyors[1].connect_to(converger)
        conveyors[2].connect_to(converger)
        conveyors[3].connect_to(storage_box)
        conveyors[4].connect_to(storage_box)
        conveyors[6].connect_to(sink_0)
        conveyors[7].connect_to(sink_1)
        
        components = [source_0, source_1, *conveyors, converger, splitter, storage_box, sink_0, sink_1]
        controller = Controller(components)
        trace = [trace_type(components)]
        for _ in range(50):
            controller.step()
            trace.append(trace_type(components))
        
        for t in trace:
            for c in t:
                for i in c:
                    print(i, end='')
                print(end=' ')
            print()
    
    def test_storage_box_2(self):
        source_0 = Source(['A'])
        source_1 = Source(['A'])
        
        conveyors = [
            Conveyor(1, '0'), 
            Conveyor(2, '1'), 
            Conveyor(2, '2'), 
            Conveyor(1, '3'), 
            Conveyor(4, '4'), 
            Conveyor(6, '5'), 
            Conveyor(6, '6'), 
            Conveyor(6, '7'), 
        ]
        
        splitter  = Splitter()
        converger = Converger()
        
        storage_box = StorageBox()
        
        source_0.connect_to(conveyors[0])
        source_1.connect_to(conveyors[4])
        
        sink_0 = Sink('0')
        
        splitter.connect_to(conveyors[1])
        splitter.connect_to(conveyors[3])
        splitter.connect_to(conveyors[2])
        converger.connect_to(splitter)
        
        storage_box.connect_to(conveyors[5])
        storage_box.connect_to(conveyors[6])
        storage_box.connect_to(conveyors[7])
        
        conveyors[0].connect_to(converger)
        conveyors[1].connect_to(converger)
        conveyors[2].connect_to(converger)
        conveyors[3].connect_to(storage_box)
        conveyors[4].connect_to(storage_box)
        conveyors[6].connect_to(sink_0)
        
        components = [source_0, source_1, *conveyors, converger, splitter, storage_box, sink_0]
        controller = Controller(components)
        trace = [trace_type(components)]
        for _ in range(2300):
            controller.step()
            trace.append(trace_type(components))
        
        for t in trace:
            for c in t:
                for i in c:
                    print(i, end='')
                print(end=' ')
            print()
    
    def test_storage_box_3(self):
        source = Source(['A'])
        
        sinks = [
            Sink('0'), 
            Sink('1')
        ]
        
        storage_box = StorageBox()
        
        convergers = [
            Converger('0'), 
            Converger('1')
        ]
        
        splitters = [
            Splitter('0'), 
            Splitter('1'), 
            Splitter('2'), 
        ]
        
        conveyors = [
            Conveyor(1, '0'), 
            Conveyor(2, '1'), 
            Conveyor(1, '2'), 
            Conveyor(1, '3'), 
            Conveyor(6, '4'), 
            Conveyor(2, '5'), 
            Conveyor(3, '6'), 
            Conveyor(6, '7'), 
            Conveyor(10, '8'), 
        ]
        
        splitters[0].connect_to(conveyors[2])
        splitters[0].connect_to(conveyors[3])
        splitters[0].connect_to(conveyors[4])
        splitters[1].connect_to(conveyors[5])
        splitters[1].connect_to(splitters[2])
        splitters[2].connect_to(conveyors[6])
        splitters[2].connect_to(conveyors[8])
        
        convergers[0].connect_to(splitters[1])
        convergers[1].connect_to(conveyors[7])
        
        storage_box.connect_to(conveyors[1])
        storage_box.connect_to(splitters[0])
        
        conveyors[0].connect_to(storage_box)
        conveyors[1].connect_to(convergers[0])
        conveyors[2].connect_to(convergers[0])
        conveyors[3].connect_to(convergers[0])
        conveyors[4].connect_to(storage_box)
        conveyors[5].connect_to(convergers[1])
        conveyors[6].connect_to(convergers[1])
        conveyors[7].connect_to(sinks[0])
        conveyors[8].connect_to(sinks[1])
        
        source.connect_to(conveyors[0])
        
        components = [source, *conveyors, *convergers, *splitters, storage_box, *sinks]
        controller = Controller(components)
        trace = [trace_type(components)]
        for _ in range(50):
            controller.step()
            trace.append(trace_type(components))
        
        for t in trace:
            for c in t:
                for i in c:
                    print(i, end='')
                print(end=' ')
            print()        