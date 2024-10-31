from pydot import Dot, Edge, Node, Subgraph

###############################################################################
# Nodes and Subgraphs
###############################################################################
msi_devices = [
  Node("msi_device_0", label="MSI Device 0"),
  Node("msi_device_1", label="MSI Device 1"),
  Node("msi_device__", label="MSI Device ..."),
]

class APLIC(Subgraph):
  def __init__(self):
    Subgraph.__init__(self, "aplic", label="APLIC", cluster=True,
      style='filled', bgcolor="#F8CECC", pencolor="#B85450",
    )
    self.domains = [
      Node("m_domain", label="M Domain", height=1.5),
      Node("s_domain", label="S Domain", height=1.5),
    ]
    for domain in self.domains:
      self.add_node(domain)
aplic = APLIC()

wired_devices = [
  Node("wired_device_0", label="Wired Device 0"),
  Node("wired_device_1", label="Wired Device 1"),
  Node("wired_device__", label="Wired Device ..."),
]

bus_network = Node("bus_network", label="Bus", height=7)

class IMSICHart(Subgraph):
  class IMSIC(Subgraph):
    def __init__(self, id, suffix):
      Subgraph.__init__(self, f"imsic_{suffix}", label=f"IMSIC {id}", cluster=True,
        style="filled", bgcolor="#F8CECC", pencolor="#B85450",
      )
      self.intFiles = [
        Node(f"imsic_{suffix}_mint_file", label="M IntFile"),
        Node(f"imsic_{suffix}_sint_file", label="S IntFile"),
      ]
      self.intFiles += [
        Node(f"imsic_{suffix}_vsint_file_0", label=f"VS IntFile 0"),
        Node(f"imsic_{suffix}_vsint_file__", label=f"VS IntFile ..."),
      ]
      for intFile in self.intFiles:
        self.add_node(intFile)

  def __init__(self, id, suffix):
    Subgraph.__init__(self, f"imsic_hart_{suffix}", label="", cluster=True,
      pencolor="transparent",
    )
    self.imsic = self.IMSIC(id, suffix)
    self.add_subgraph(self.imsic)
    self.hart = Node(f"hart_{suffix}", label=f"Hart {id}", height=3.2)
    self.add_node(self.hart)

imsic_harts = [IMSICHart(0, 0), IMSICHart("...", "_")]

###############################################################################
# Edges
###############################################################################
class MessageEdge(Edge):
  def __init__(self, src, dst, obj_dict=None, **attrs):
    Edge.__init__(self, src, dst, obj_dict, **attrs, color='"black:invis:black"')
class WireEdge(Edge):
  def __init__(self, src, dst, obj_dict=None, **attrs):
    Edge.__init__(self, src, dst, obj_dict, **attrs)

###############################################################################
# Graph
###############################################################################
class AIADot(Dot):
  class Legend(Subgraph):
    def __init__(self):
      Subgraph.__init__(self, "legend", label="Legend", cluster=True, pencolor="gray")
    def add_edge_legend(self, EdgeClass, label):
      src = Node(f"legend_${label}_edge_src", shape="plain", label=label)
      self.add_node(src)
      dst = Node(f"legend_${label}_edge_dst", shape="plain", label=" ")
      self.add_node(dst)
      self.add_edge(EdgeClass(src, dst))

  def __init__(self, *argsl, **argsd):
    Dot.__init__(self, *argsl, **argsd,
      splines="ortho",
      bgcolor="transparent",
    )
    self.main = Subgraph("main", label="", cluster=True, pencolor="transparent")
    self.main.set_node_defaults(shape="box")
    self.add_subgraph(self.main)
    self.legend = self.Legend()
    self.add_subgraph(self.legend)
    self.legend.add_edge_legend(WireEdge, "wire")
    self.legend.add_edge_legend(MessageEdge, "message")
