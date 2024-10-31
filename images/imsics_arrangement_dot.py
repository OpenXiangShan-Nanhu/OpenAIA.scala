from pydot import Dot, Edge, Node, Subgraph



class Group(Subgraph):
  class IMSICHart(Subgraph):
    class IMSIC(Subgraph):
      def __init__(self, gid, mid):
        name = f"imsic_{gid}_{mid}"
        Subgraph.__init__(self, name, label=f"IMSIC {gid}{mid}", cluster=True,
          bgcolor="#F8CECC", pencolor="#B85450",
        )
        self.intFiles = [
          Node(f"{name}_intfile_m",     label="M IntFile"),
          Node(f"{name}_intfile_s",     label="S IntFile"),
          Node(f"{name}_intfile_vs_0",  label="VS IntFile 0"),
          Node(f"{name}_intfile_vs_1",  label="VS IntFile 1"),
        ]
        m = Subgraph(f"{name}_m", label="M Level", cluster=True,
          bgcolor="#FFE6CC", pencolor="#D79B00",
        )
        m.add_node(self.intFiles[0])
        self.add_subgraph(m)
        s = Subgraph(f"{name}_s", label="S Level", cluster=True,
          bgcolor="#FFE6CC", pencolor="#D79B00",
        )
        for intFile in self.intFiles[1:]:
          s.add_node(intFile)
        self.add_subgraph(s)
    def __init__(self, gid, mid):
      name = f"imsichart_{gid}_{mid}"
      Subgraph.__init__(self, name, label=f"Member {gid}{mid}", cluster=True,
        pencolor="#82B366", bgcolor="#D5E8D4",
      )
      self.hart = Node(f"{name}_hart", label=f"Hart {gid}{mid}", height=4)
      self.add_node(self.hart)
      self.imsic = self.IMSIC(gid, mid)
      self.add_subgraph(self.imsic)
      for intFile in self.imsic.intFiles:
        self.add_edge(Edge(intFile, self.hart))

  def __init__(self, gid):
    Subgraph.__init__(self, f"group_{gid}", label=f"Group {gid}", cluster=True,
      pencolor="#6C8EBF", bgcolor="#DAE8FC",
    )
    self.bus = Node(f"bus_{gid}", label=f"Group Bus {gid}", height=10)
    self.add_node(self.bus)
    self.imsicharts = [self.IMSICHart(gid, i) for i in range(0,2)]
    for imsichart in self.imsicharts:
      self.add_subgraph(imsichart)
      for intFile in imsichart.imsic.intFiles:
        self.add_edge(Edge(self.bus, intFile))

graph = Dot(label="IMSIC Logic Arrangement", bgcolor="transparent",
  splines="ortho", rankdir="LR",
)
graph.set_node_defaults(shape="box", margin=0)

bus = Node(f"bus", label="System Bus", height=20)
graph.add_node(bus)

groups = [Group(i) for i in range(0,2)]
for group in groups:
  graph.add_subgraph(group)
  graph.add_edge(Edge(bus, group.bus, color='"black:invis:black"'))

graph.write(__file__.replace("_dot.py", "_py.dot"), prog="circo")
