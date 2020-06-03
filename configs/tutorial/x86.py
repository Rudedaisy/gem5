import m5
from m5.objects import *

def init_fs(system, membus):
    system.pc = Pc()
    
    # Constants similar to x86_traits.hh
    IO_address_space_base = 0x8000000000000000
    pci_config_address_space_base = 0xc000000000000000
    interrupts_address_space_base = 0xa000000000000000
    APIC_range_size = 1 << 12;

    # North Bridge
    system.iobus = IOXBar()
    system.bridge = Bridge(delay='50ns')
    system.bridge.master = system.iobus.slave
    system.bridge.slave = membus.master
    # Allow the bridge to pass through:
    #  1) kernel configured PCI device memory map address: address range
    #     [0xC0000000, 0xFFFF0000). (The upper 64kB are reserved for m5ops.)
    #  2) the bridge to pass through the IO APIC (two pages, already contained in 1),
    #  3) everything in the IO address range up to the local APIC, and
    #  4) then the entire PCI address space and beyond.
    system.bridge.ranges = \
        [
        AddrRange(0xC0000000, 0xFFFF0000),
        AddrRange(IO_address_space_base,
                  interrupts_address_space_base - 1),
        AddrRange(pci_config_address_space_base,
                  Addr.max)
        ]

    # Create a bridge from the IO bus to the memory bus to allow access to
    # the local APIC (two pages)
    system.apicbridge = Bridge(delay='50ns')
    system.apicbridge.slave = system.iobus.master
    system.apicbridge.master = membus.slave
    # This should be expanded for multiple CPUs
    system.apicbridge.ranges = [AddrRange(interrupts_address_space_base,
                                           interrupts_address_space_base +
                                           1 * APIC_range_size
                                           - 1)]

    #"""
    # Introduce pcie_nic here (using PCI)
    system.nic = IGbE_pcie(pci_bus=0, pci_dev=0, pci_func=0,
                                          InterruptLine=1, InterruptPin=1, root_port_number=0, host=system.pc.pci_host)
    system.nic.dma = system.iobus.slave
    system.nic.pio = system.iobus.master

    # create distributed ethernet link
    system.etherlink = DistEtherLink(speed = "10Gbps", #options.ethernet_linkspeed,
                                     delay = "10us", #options.ethernet_linkdelay,
                                     dist_rank = 0, #options.dist_rank,
                                     dist_size = 1, #options.dist_size,
                                     server_name = "127.0.0.1", #options.dist_server_name,
                                     server_port = 1200, #options.dist_server_port,
                                     sync_start = "1000000000000t", #options.dist_sync_start,
                                     sync_repeat = "0us") #options.dist_sync_repeat)
    system.etherlink.int0 = Parent.system.nic.interface
    #"""
    
    """
    # params to-change
    switch_up_lanes = 4 # 1
    lanes = 4 # 1
    cacheline_size = 64
    replay_buffer_size = 50
    should_print = False
    switch_buffer_size = 50
    pcie_switch_delay = '50ns'
    
    # Instantiate PCIe links - note that there is no PCIe between rootport and IO-/mem-bus
    system.pcie1 = PCIELink(lanes = switch_up_lanes, speed = '5Gbps', mps=cacheline_size, max_queue_size=replay_buffer_size)
    system.pcie3 = PCIELink(lanes = lanes , speed = '5Gbps', mps = cacheline_size, max_queue_size=replay_buffer_size)
    system.pcie4 = PCIELink(lanes = lanes , speed = '5Gbps',  mps = cacheline_size,max_queue_size=replay_buffer_size)
    system.pcie5 = PCIELink(lanes = lanes , speed = '5Gbps', mps = cacheline_size, max_queue_size=replay_buffer_size)
    system.pcie6 = PCIELink(lanes = lanes , speed = '5Gbps' ,mps = cacheline_size, max_queue_size=replay_buffer_size)
    system.pcie7 = PCIELink(lanes = lanes , speed = '5Gbps', mps = cacheline_size, max_queue_size=replay_buffer_size)
    #system.iobus_dma = IOXBar()

    # Instantiate Root Complex and connect it to PCIe links
    # TODO: automatically create PCIe links (via a std::vector) and connect them in the background
    system.Root_Complex = Root_Complex(is_transmit = should_print ,req_size = switch_buffer_size, resp_size = switch_buffer_size ,  delay = '150ns', host=system.pc.pci_host)
    system.Root_Complex.slave = system.membus.master
    system.Root_Complex.slave_dma1 = system.pcie1.upstreamMaster
    system.Root_Complex.slave_dma2 = system.pcie6.upstreamMaster
    system.Root_Complex.slave_dma3 = system.pcie7.upstreamMaster 
    system.Root_Complex.master1    = system.pcie1.upstreamSlave 
    system.Root_Complex.master2    = system.pcie6.upstreamSlave 
    system.Root_Complex.master3    = system.pcie7.upstreamSlave 
    system.Root_Complex.master_dma = system.iobus.slave # system.iobus_dma.slave

    # Instantiate a PCIe switch and connect it to PCIe links
    system.switch = PciESwitch(pci_bus = 1 , delay=pcie_switch_delay , req_size=switch_buffer_size , resp_size = switch_buffer_size, host=system.pc.pci_host)
    system.switch.slave = system.pcie1.downstreamMaster
    system.switch.slave_dma1 = system.pcie3.upstreamMaster
    system.switch.slave_dma2 = system.pcie4.upstreamMaster 
    system.switch.slave_dma3 = system.pcie5.upstreamMaster
    system.switch.master1    = system.pcie3.upstreamSlave
    system.switch.master2    = system.pcie4.upstreamSlave 
    system.switch.master3    = system.pcie5.upstreamSlave
    system.switch.master_dma = system.pcie1.downstreamSlave

    # Instantiate and attach PCI/PCIe devices
    system.ethernet1 = IGbE_pcie(pci_bus = 6, pci_dev = 0, pci_func = 0, InterruptLine = 3, InterruptPin = 2, root_port_number = 1, host=system.pc.pci_host)
    system.ethernet1.pio = system.pcie6.downstreamMaster
    system.ethernet1.dma = system.pcie6.downstreamSlave
    system.ethernet2 = IGbE_pcie(pci_bus=4, pci_dev = 0, pci_func = 0, InterruptLine = 3, InterruptPin = 1, root_port_number = 0, host=system.pc.pci_host, is_invisible = 0)
    system.ethernet2.pio = system.pcie4.downstreamMaster
    system.ethernet2.dma = system.pcie4.downstreamSlave
    system.ethernet3 = IGbE_e1000(pci_bus=5,pci_dev=0, pci_func = 0, InterruptLine = 0x1E, InterruptPin = 2, root_port_number = 0, host=system.pc.pci_host, is_invisible = 1)
    system.ethernet3.pio = system.pcie5.downstreamMaster
    system.ethernet3.dma = system.pcie5.downstreamSlave
    system.ethernet4 = IGbE_pcie(pci_bus=7,pci_dev=0, pci_func = 0, InterruptLine = 0x1E, InterruptPin = 4, root_port_number = 2, host=system.pc.pci_host, is_invisible = 1)
    system.ethernet4.pio = system.pcie7.downstreamMaster
    system.ethernet4.dma = system.pcie7.downstreamSlave
    #system.ide = IdeController(disks = [], pci_bus=3, pci_dev=0, pci_func=0, InterruptLine=2, InterruptPin=1, root_port_number = 0, flag=1)
    system.ide = IGbE_pcie(pci_bus=3, pci_dev=0, pci_func = 0, InterruptLine = 0x2, InterruptPin = 1, root_port_number = 0, host=system.pc.pci_host, is_invisible = 1)
    system.ide.pio = system.pcie3.downstreamMaster
    system.ide.dma = system.pcie3.downstreamSlave
    system.ide.host = system.pc.pci_host
    #"""

    # connect the io bus
    system.pc.attachIO(system.iobus)#, [system.nic.dma])

    # Add a tiny cache to the IO bus.
    # This cache is required for the classic memory model to mantain coherence
    system.iocache = Cache(assoc=8,
                           tag_latency = 50,
                           data_latency = 50,
                           response_latency = 50,
                           mshrs = 20,
                           size = '1kB',
                           tgts_per_mshr = 12,
                           #forward_snoops = False,
                           addr_ranges = system.mem_ranges[0]) ########## MIGHT NEED TO REMOVE [0]
    system.iocache.cpu_side = system.iobus.master
    system.iocache.mem_side = system.membus.slave

    intrctrl = IntrControl()
    system.intrctrl = intrctrl
    
    ###############################################

    # Add in a Bios information structure.
    system.smbios_table.structures = [X86SMBiosBiosInformation()]

    # Set up the Intel MP table
    base_entries = []
    ext_entries = []
    # This is the entry for the processor.
    # You need to make multiple of these if you have multiple processors
    # Note: Only one entry should have the flag bootstrap = True!
    bp = X86IntelMPProcessor(
            local_apic_id = 0,
            local_apic_version = 0x14,
            enable = True,
            bootstrap = True)
    base_entries.append(bp)
    # For multiple CPUs, change id to 1 + the final CPU id above (e.g., cpus)
    io_apic = X86IntelMPIOAPIC(
            id = 1,
            version = 0x11,
            enable = True,
            address = 0xfec00000)
    system.pc.south_bridge.io_apic.apic_id = io_apic.id
    system.pc.south_bridge.ide.root_port_number = 0
    base_entries.append(io_apic)
    pci_bus = X86IntelMPBus(bus_id = 0, bus_type='PCI')
    base_entries.append(pci_bus)
    isa_bus = X86IntelMPBus(bus_id = 1, bus_type='ISA')
    base_entries.append(isa_bus)
    connect_busses = X86IntelMPBusHierarchy(bus_id=1,
            subtractive_decode=True, parent_bus=0)
    ext_entries.append(connect_busses)
    pci_dev4_inta = X86IntelMPIOIntAssignment(
            interrupt_type = 'INT',
            polarity = 'ConformPolarity',
            trigger = 'ConformTrigger',
            source_bus_id = 0,
            source_bus_irq = 0 + (4 << 2),
            dest_io_apic_id = io_apic.id,
            dest_io_apic_intin = 16)
    base_entries.append(pci_dev4_inta)
    def assignISAInt(irq, apicPin):
        assign_8259_to_apic = X86IntelMPIOIntAssignment(
                interrupt_type = 'ExtInt',
                polarity = 'ConformPolarity',
                trigger = 'ConformTrigger',
                source_bus_id = 1,
                source_bus_irq = irq,
                dest_io_apic_id = io_apic.id,
                dest_io_apic_intin = 0)
        base_entries.append(assign_8259_to_apic)
        assign_to_apic = X86IntelMPIOIntAssignment(
                interrupt_type = 'INT',
                polarity = 'ConformPolarity',
                trigger = 'ConformTrigger',
                source_bus_id = 1,
                source_bus_irq = irq,
                dest_io_apic_id = io_apic.id,
                dest_io_apic_intin = apicPin)
        base_entries.append(assign_to_apic)
    assignISAInt(0, 2)
    assignISAInt(1, 1)
    for i in range(3, 15):
        assignISAInt(i, i)
    system.intel_mp_table.base_entries = base_entries
    system.intel_mp_table.ext_entries = ext_entries

    # This is setting up the physical memory layout
    # Each entry represents a physical address range
    # The last entry in this list is the main system memory
    # Note: If you are configuring your system to use more than 3 GB then you
    #       will need to make significant changes to this section
    entries = \
       [
        # Mark the first megabyte of memory as reserved
        X86E820Entry(addr = 0, size = '639kB', range_type = 1),
        X86E820Entry(addr = 0x9fc00, size = '385kB', range_type = 2),
        # Mark the rest of physical memory as available
        X86E820Entry(addr = 0x100000,
                size = '%dB' % (system.mem_ranges[0].size() - 0x100000),
                range_type = 1),
        ]
    # Mark [mem_size, 3GB) as reserved if memory less than 3GB, which force
    # IO devices to be mapped to [0xC0000000, 0xFFFF0000). Requests to this
    # specific range can pass though bridge to iobus.
    entries.append(X86E820Entry(addr = system.mem_ranges[0].size(),
        size='%dB' % (0xC0000000 - system.mem_ranges[0].size()),
        range_type=2))

    # Reserve the last 16kB of the 32-bit address space for the m5op interface
    entries.append(X86E820Entry(addr=0xFFFF0000, size='64kB', range_type=2))

    system.e820_table.entries = entries
