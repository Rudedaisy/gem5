import m5
from m5.objects import *
from m5.util import convert

import x86

from caches import *

class MySystem(LinuxX86System):
    def __init__(self, opts):
        super(MySystem, self).__init__()
        self._opts = opts
        
        self.clk_domain = SrcClockDomain()
        self.clk_domain.clock = '3GHz'
        self.clk_domain.voltage_domain = VoltageDomain()

        mem_size = '3GB'
        self.mem_ranges = [AddrRange(mem_size),
                           AddrRange(0xC0000000, size=0x200000) # PCIe and I/O ////////
                           ]

        self.membus = SystemXBar()
        self.membus.badaddr_responder = BadAddr()
        self.membus.default = self.membus.badaddr_responder.pio

        self.system_port = self.membus.slave

        # initialize x86 system
        x86.init_fs(self, self.membus)

        self.kernel = '/root/images/baseTDNN/vmlinux-5.2.3'
        #self.kernel = '/root/Gem5-PCI-Express/vmlinux' # only works for ARM system I think
        
        boot_options = ['earlyprintk=ttyS0', 'console=ttyS0', 'lpj=7999923', 'root=/dev/hda1']

        self.boot_osflags = ' '.join(boot_options)

        self.setDiskImage('/root/images/miniDNN/linux-x86.img')

        self.createCPU()

        self.createCacheHierarchy()

        self.createMemoryControllers()

        self.setupInterrupts()

        #self.setupPcieNic() # already handled in init_fs()

    def setDiskImage(self, img_path):
        """ Set the disk image
        @param img_path path on the host to the image file for the disk
        """
        disk0 = CowDisk(img_path)
        self.pc.south_bridge.ide.disks = [disk0]

    def createCPU(self):
        self.cpu = TimingSimpleCPU()
        self.mem_mode = 'timing'
        self.cpu.createThreads()

    def createCacheHierarchy(self):
        """ Create a simple cache heirarchy with the caches from part1 """

        # Create an L1 instruction and data caches and an MMU cache
        # The MMU cache caches accesses from the inst and data TLBs
        self.cpu.icache = L1ICache()
        self.cpu.dcache = L1DCache()
        
        # Connect the instruction, data, and MMU caches to the CPU
        self.cpu.icache.connectCPU(self.cpu)
        self.cpu.dcache.connectCPU(self.cpu)
        
        # Hook the CPU ports up to the membus
        self.cpu.icache.connectBus(self.membus)
        self.cpu.dcache.connectBus(self.membus)
        
        # Connect the CPU TLBs directly to the mem.
        self.cpu.itb.walker.port = self.membus.slave
        self.cpu.dtb.walker.port = self.membus.slave

    def createMemoryControllers(self):
        self.mem_cntrl = DDR3_1600_8x8(range = self.mem_ranges[0],
                                       port = self.membus.master)

    def setupInterrupts(self):
        """ Create the interrupt controller for the CPU """
        self.cpu.createInterruptController()
        self.cpu.interrupts[0].pio = self.membus.master
        self.cpu.interrupts[0].int_master = self.membus.slave
        self.cpu.interrupts[0].int_slave = self.membus.master

    #def setupPcieNic(self):
    #    self.pci_host = GenericPciHost()
    #    
    #    self.pcie_nic = IGbE_e1000()
    #    #self.pcie_nic.system = self
    #    return
        
class CowDisk(IdeDisk):
    """ Wrapper class around IdeDisk to make a simple copy-on-write disk
    for gem5. Creates an IDE disk with a COW read/write disk image.
    Any data written to the disk in gem5 is saved as a COW layer and
    thrown away on the simulator exit.
    """

    def __init__(self, filename):
        """ Initialize the disk with a path to the image file.
        @param filename path to the image file to use for the disk.
        """
        super(CowDisk, self).__init__()
        self.driveID = 'master'
        self.image = CowDiskImage(child=RawDiskImage(read_only=True),
                                  read_only=False)
        self.image.child.image_file = filename

def TwoSystem(opts):
    mainSystem = MySystem(opts)

    system2 = MySystem(opts)
    # not done yet.... continue function design here

    return mainSystem
