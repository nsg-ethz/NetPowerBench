# This python script connects two ports s.t. packets are forwarded to each other.

# This one in particular is written to do a snake test. 
# Physical ports are assigned in connected-pairs (x,y). This means, externally these ports are connected with a cable.
# These are (5,6), (7,8), (9,10), (11,12), (13,14), (15,16), (17,18), (19, 20).

# We need to send traffic internally from (6,7), (10, 11), etc. This done here through static routing. E.g., all packets arriving at 4 will be forwarded to 5, and vice-versa

# Moreover, we recv/send external traffic from physical ports 3 (144) and 21 (32).

PORTS = [None,144, 160,168, 176,184, 60,52, 44,36, 28,20, 12,4, 0,8, 16,24, 32,None]

# #clear ports and tables
bfrt.pre.clear()
bfrt.port.port.clear()
bfrt.port_based_forwarder.clear()

p4 = bfrt.port_based_forwarder.pipe
port_t = p4.MyIngress.port_t

l_ports = PORTS[1:-1:2]                                      # Assign pairs
r_ports = PORTS[2::2]
assert(len(l_ports) == len(r_ports))

for l, r in zip(l_ports, r_ports):
    assert(l != None or r != None)
    port_t.entry_with_forward(ingress_port=l, port=r).push()
    port_t.entry_with_forward(ingress_port=r, port=l).push()

# port_t.entry_with_forward(ingress_port=144, port=32).push()
# port_t.entry_with_forward(ingress_port=32, port=144).push()


bfrt.complete_operations()

