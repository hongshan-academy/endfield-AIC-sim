from simulation.components import *
from simulation.item import *
from simulation.controller import Controller


def main():
    controller = Controller()

    # Create components
    source = Source([Item("A", i) for i in range(1, 100)])
    conveyor_a = Conveyor(length=3)
    conveyor_b = Conveyor(length=3)
    sink = Sink()
    
    # Connect components: Source → ConveyorA → ConveyorB → Sink
    conveyor_a.connect([source])
    conveyor_b.connect([conveyor_a])
    sink.connect([conveyor_b])
    
    # Add to controller
    controller.set_components([source, conveyor_a, conveyor_b, sink])
    controller.initialize()
    
    # Run simulation and track item positions
    trace = []
    for tick in range(10):
        controller.step()
        controller.print_state()
        
        # Record buffer states
        buffer_a = [item.id if item else 0 for item in conveyor_a.get_buffer()]
        buffer_b = [item.id if item else 0 for item in conveyor_b.get_buffer()]
        trace.append((buffer_a, buffer_b, sink.items_received))


if __name__ == "__main__":
    main()
