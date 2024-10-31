from pydot import Dot, Edge, Node, Subgraph

graph = Dot(label="IMSIC", rankdir="LR", splines="ortho", bgcolor="transparent")
graph.set_node_defaults(shape="box")

bus = Node("bus", label="Bus", height=12)
graph.add_node(bus)

hart = Node("hart", label="Hart", height=12)
graph.add_node(hart)

class IMSIC(Subgraph):
  class IntFile(Subgraph):
    class Mem(Subgraph):
      def __init__(self, parent_name):
        name = f"{parent_name}_mem"
        Subgraph.__init__(self, name, label="Mem[4KB]", cluster=True,
          bgcolor="#F5F5F5", pencolor="#666666",
        )
        self.seteipnum = Node(f"{name}_seteipnum", label="seteipnum[4B]")
        self.add_node(self.seteipnum)

    def __init__(self, name, label):
      Subgraph.__init__(self, name, label=label, cluster=True,
        bgcolor="#FFE6CC", pencolor="#D79B00",
      )
      self.mem = self.Mem(name)
      self.add_subgraph(self.mem)
  
      self.pending = Node(f"{name}_pending", label="pending[1b]")
      self.add_node(self.pending)
      self.add_edge(Edge(self.mem.seteipnum, self.pending, color="transparent"))
      self.topei = Node(f"{name}_topei", label="topei")
      self.add_node(self.topei)
      self.add_edge(Edge(self.mem.seteipnum, self.topei, color="transparent"))

      self.iselect = Node(f"{name}_iselect", label="iselect")
      self.add_node(self.iselect)
      self.add_edge(Edge(self.mem.seteipnum, self.iselect, color="transparent"))
      self.ireg = Node(f"{name}_ireg", label="ireg")
      self.add_node(self.ireg)
      self.add_edge(Edge(self.mem.seteipnum, self.ireg, color="transparent"))

      self.add_node(Node(f"{name}_eips", label="eip[]"))
      self.add_node(Node(f"{name}_eies", label="eie[]"))

  def __init__(self):
    Subgraph.__init__(self, "imsic", label="IMSIC", cluster=True, bgcolor="#F8CECC", pencolor="#B85450")
    self.intFiles = [
      self.IntFile(f"imsic_mint_file",       label="M IntFile"),
      self.IntFile(f"imsic_sint_file",       label="S IntFile"),
      self.IntFile(f"imsic_vsint_file_0",    label=f"VS IntFile 0"),
      self.IntFile(f"imsic_vsint_file_1",    label=f"VS IntFile 1"),
    ]
    for intFile in self.intFiles:
      self.add_subgraph(intFile)

    self.mtopei = Node("imsic_mtopei", label="mtopei[4B]")
    self.add_node(self.mtopei)
    self.add_edge(Edge(self.intFiles[0].topei, self.mtopei))
    self.stopei = Node("imsic_stopei", label="stopei[4B]")
    self.add_node(self.stopei)
    self.add_edge(Edge(self.intFiles[1].topei, self.stopei))
    self.vstopei = Node("imsic_vstopei", label="vstopei[4B]", height=1.2)
    self.add_node(self.vstopei)
    self.add_edge(Edge(self.intFiles[2].topei, self.vstopei))
    self.add_edge(Edge(self.intFiles[3].topei, self.vstopei))

    self.pendings = [Node(f"imsic_pending_{i}", label=f"pending{i}[1b]") for i in range(0,4)]
    for intFile, pending in zip(self.intFiles, self.pendings):
      self.add_node(pending)
      self.add_edge(Edge(intFile.pending, pending))

    self.miselect = Node("imsic_miselect", label="miselect[4B]")
    self.add_node(self.miselect)
    self.add_edge(Edge(self.intFiles[0].iselect, self.miselect, dir="back"))
    self.siselect = Node("imsic_siselect", label="siselect[4B]")
    self.add_node(self.siselect)
    self.add_edge(Edge(self.intFiles[1].iselect, self.siselect, dir="back"))
    self.vsiselect = Node("imsic_vsiselect", label="vsiselect[4B]", height=1.2)
    self.add_node(self.vsiselect)
    self.add_edge(Edge(self.intFiles[2].iselect, self.vsiselect, dir="back"))
    self.add_edge(Edge(self.intFiles[3].iselect, self.vsiselect, dir="back"))

    self.mireg = Node("imsic_mireg", label="mireg[4B]")
    self.add_node(self.mireg)
    self.add_edge(Edge(self.intFiles[0].ireg, self.mireg, dir="both"))
    self.sireg = Node("imsic_sireg", label="sireg[4B]")
    self.add_node(self.sireg)
    self.add_edge(Edge(self.intFiles[1].ireg, self.sireg, dir="both"))
    self.vsireg = Node("imsic_vsireg", label="vsireg[4B]", height=1.2)
    self.add_node(self.vsireg)
    self.add_edge(Edge(self.intFiles[2].ireg, self.vsireg, dir="both"))
    self.add_edge(Edge(self.intFiles[3].ireg, self.vsireg, dir="both"))

    self.vgein = Node("imsic_vgein", label="vgein", dir="back")
    self.add_node(self.vgein)
    self.add_edge(Edge(self.vgein, self.vstopei,    constraint=False, color="gray"))
    self.add_edge(Edge(self.vgein, self.vsiselect,  constraint=False, color="gray"))
    self.add_edge(Edge(self.vgein, self.vsireg,     constraint=False, color="gray"))
    vgein_same_rank = Subgraph("vgein_same_rank", label="", samerank=True, pencolor="transparent")
    self.add_subgraph(vgein_same_rank)
    vgein_same_rank.add_node(self.vgein)
    vgein_same_rank.add_node(self.vstopei)
    vgein_same_rank.add_node(self.vsiselect)
    vgein_same_rank.add_node(self.vsireg)

imsic = IMSIC()
graph.add_subgraph(imsic)
for intFile in imsic.intFiles:
  graph.add_edge(Edge(bus, intFile.mem.seteipnum, color='"black:invis:black"'))
for pending in imsic.pendings:
  graph.add_edge(Edge(pending, hart))
graph.add_edge(Edge(imsic.mtopei, hart))
graph.add_edge(Edge(imsic.stopei, hart))
graph.add_edge(Edge(imsic.vstopei, hart))
graph.add_edge(Edge(imsic.miselect, hart, dir="back"))
graph.add_edge(Edge(imsic.siselect, hart, dir="back"))
graph.add_edge(Edge(imsic.vsiselect, hart, dir="back"))
graph.add_edge(Edge(imsic.mireg, hart, dir="both"))
graph.add_edge(Edge(imsic.sireg, hart, dir="both"))
graph.add_edge(Edge(imsic.vsireg, hart, dir="both"))
graph.add_edge(Edge(imsic.vgein, hart, dir="back"))

graph.write(__file__.replace("_dot.py", "_py.dot"))
