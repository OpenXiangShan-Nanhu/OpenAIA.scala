from arch_common import *

###############################################################################
# Graph
###############################################################################
graph = AIADot(label="Configuration Paths in an AIA System", rankdir="RL")
configure = graph.main

###############################################################################
# Nodes and Subgraphs
###############################################################################
configure.add_subgraph(aplic)
configure.add_node(bus_network)
for imsic_hart in imsic_harts:
  configure.add_subgraph(imsic_hart)

###############################################################################
# Edges
###############################################################################
for domain in aplic.domains:
  configure.add_edge(MessageEdge(bus_network, domain))
for imsic_hart in imsic_harts:
  imsic = imsic_hart.imsic
  hart = imsic_hart.hart
  for intFile in imsic.intFiles:
    configure.add_edge(WireEdge(hart, intFile))
    configure.add_edge(Edge(intFile, bus_network, color="transparent"))
  configure.add_edge(MessageEdge(hart, bus_network))

###############################################################################
# Output
###############################################################################
graph.write(__file__.replace("_dot.py", "_py.dot"))
