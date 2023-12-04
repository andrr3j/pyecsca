from typing import Dict, Set, Iterator, List, Tuple, Type
from pyecsca.ec.op import OpType
from pyecsca.ec.formula_gen.formula_graph import EFDFormulaGraph, Node, CodeOpNode, CodeOp, parse 
from pyecsca.ec.formula import EFDFormula
from random import randint 

class Fliparoo:
    """
    Fliparoo is a chain of nodes N1->N2->...->Nk in EFDFormulaGraph for k>=2 such that:
        - All Ni are * or All Ni are +/-
        - For every Ni, except for Nk, the only outgoing node is Ni+1
        - Neither of N1,...,Nk-1 is an output node
    """

    def __init__(self, chain: List[Node], graph: EFDFormulaGraph):
        self.verify_chain(chain)
        self.nodes = chain
        self.graph = graph
        self.operator = None

    def verify_chain(self, nodes: List[Node]):
        for i, node in enumerate(nodes[:-1]):
            if node.outgoing_nodes != [nodes[i + 1]]:
                raise BadFliparoo
            if node.output_node:
                raise BadFliparoo

    @property
    def first(self):
        return self.nodes[0]

    @property
    def last(self):
        return self.nodes[-1]

    def __len__(self):
        return len(self.nodes)

    def __repr__(self):
        return "->".join(map(lambda x: x.__repr__(), self.nodes))

    def previous(self, node: Node):
        i = self.nodes.index(node)
        if i == 0:
            return None
        return self.nodes[i - 1]

    def __getitem__(self, i: int):
        return self.nodes[i]

    def __iter__(self):
        return iter(self.nodes)

    def __eq__(self, other):
        return self.graph == other.graph and self.nodes == other.nodes

    def deepcopy(self):
        ngraph = self.graph.deepcopy()
        nchain = [mirror_node(node, self.graph, ngraph) for node in self.nodes]
        return self.__class__(nchain, ngraph)

    def input_nodes(self):
        input_nodes = []
        for node in self:
            input_nodes.extend(
                filter(lambda x: x not in self.nodes, node.incoming_nodes)
            )
        return input_nodes

    def slice(self, i: int, j: int):
        return self.__class__(self.nodes[i:j], self.graph)


class MulFliparoo(Fliparoo):
    def __init__(self, chain: List[Node], graph: EFDFormulaGraph):
        super().__init__(chain, graph)
        operations = set(node.op.operator for node in self.nodes)
        if len(operations) != 1 or list(operations)[0] != OpType.Mult:
            raise BadFliparoo
        self.operator = OpType.Mult


class AddSubFliparoo(Fliparoo):
    def __init__(self, chain: List[Node], graph: EFDFormulaGraph):
        super().__init__(chain, graph)
        operations = set(node.op.operator for node in self.nodes)
        if not operations.issubset([OpType.Add, OpType.Sub]):
            raise BadFliparoo


class AddFliparoo(Fliparoo):
    def __init__(self, chain: List[Node], graph: EFDFormulaGraph):
        super().__init__(chain, graph)
        operations = set(node.op.operator for node in self.nodes)
        if len(operations) != 1 or list(operations)[0] != OpType.Add:
            raise BadFliparoo
        self.operator = OpType.Add


class BadFliparoo(Exception):
    pass


def find_fliparoos(
    graph: EFDFormulaGraph, fliparoo_type: Type[Fliparoo] = None
) -> List[Fliparoo]:
    """Finds a list of Fliparoos in a graph"""
    fliparoos = []
    for ilong_path in graph.find_all_paths():
        long_path = ilong_path[1:]  # get rid of the input variables
        fliparoo = largest_fliparoo(long_path, graph, fliparoo_type)
        if fliparoo and fliparoo not in fliparoos:
            fliparoos.append(fliparoo)

    # remove duplicities and fliparoos in inclusion
    fliparoos = sorted(fliparoos, key=len, reverse=True)
    longest_fliparoos = []
    for fliparoo in fliparoos:
        if not is_subfliparoo(fliparoo, longest_fliparoos):
            longest_fliparoos.append(fliparoo)
    return longest_fliparoos


def is_subfliparoo(fliparoo: Tuple[Node], longest_fliparoos: List[Fliparoo]) -> bool:
    """Returns true if fliparoo is a part of any fliparoo in longest_fliparoos"""
    for other_fliparoo in longest_fliparoos:
        l1, l2 = len(fliparoo), len(other_fliparoo)
        for i in range(l2 - l1):
            if other_fliparoo.slice(i, i + l1) == fliparoo:
                return True
    return False


def largest_fliparoo(
    chain: List[Node], graph: EFDFormula, fliparoo_type: Type[Fliparoo] = None
) -> Fliparoo:
    """Finds the largest fliparoo in a list of Nodes"""
    for i in range(len(chain) - 1):
        for j in range(len(chain) - 1, i, -1):
            subchain = chain[i : j + 1]
            if fliparoo_type:
                try:
                    fliparoo_type(subchain, graph)
                except:
                    continue
            try:
                return MulFliparoo(subchain, graph)
            except BadFliparoo:
                pass
            try:
                return AddSubFliparoo(subchain, graph)
            except BadFliparoo:
                pass
    return None


class SignedNode:

    """
    Represents a summand in an expression X1-X2+X3+X4-X5...
    Used for creating +/- Fliparoos
    """

    def __init__(self, node: Node):
        self.node = node
        self.sign = 1

    def __repr__(self):
        s = {1: "+", -1: "-"}[self.sign]
        return f"{s}{self.node.__repr__()}"


class SignedSubGraph:
    """Subgraph of an EFDFormula graph with signed nodes"""

    def __init__(self, nodes: List[SignedNode], graph: EFDFormulaGraph):
        self.nodes = nodes
        self.supergraph = graph

    def add_node(self, node: SignedNode):
        self.nodes.append(node)

    def remove_node(self, node: SignedNode):
        self.nodes.remove(node)

    def change_signs(self):
        for node in self.nodes:
            node.sign *= -1

    def __getitem__(self, i):
        return self.nodes[i]

    @property
    def components(self):
        return len(self.nodes)

    def deepcopy(self):
        sgraph = self.supergraph.deepcopy()
        return SignedSubGraph(
            [mirror_node(n, self.supergraph, sgraph) for n in self.nodes], sgraph
        )


def mirror_node(node, graph, graph_copy):
    """Finds the corresponding node in a copy of the graph"""
    if isinstance(node, SignedNode):
        ns = SignedNode(graph_copy.nodes[graph.node_index(node.node)])
        ns.sign = node.sign
        return ns
    if isinstance(node, Node):
        return graph_copy.nodes[graph.node_index(node)]
    raise NotImplementedError


class DummyNode(Node):
    def __repr__(self):
        return "Dummy node"

    def label(self):
        pass

    def result(self):
        pass


def generate_fliparood_formulas(formula: EFDFormula, rename: bool = True) -> Iterator[EFDFormula]:
    graph = EFDFormulaGraph()
    graph.construct_graph(formula, rename)
    fliparoos = find_fliparoos(graph)
    for fliparoo in fliparoos:
        for flip_graph in generate_fliparood_graphs(fliparoo):
            yield flip_graph.to_EFDFormula()


def generate_fliparood_graphs(fliparoo: Fliparoo) -> Iterator[EFDFormulaGraph]:
    fliparoo = fliparoo.deepcopy()
    last_str = fliparoo.last.result
    disconnect_fliparoo_outputs(fliparoo)
    
    signed_subgraph = extract_fliparoo_signed_inputs(fliparoo)

    # Starting with a single list of unconnected signed nodes
    signed_subgraphs = [signed_subgraph]
    for _ in range(signed_subgraph.components - 1):
        subgraphs_updated = []
        for signed_subgraph in signed_subgraphs:
            extended_subgraphs = combine_all_pairs_signed_nodes(
                signed_subgraph, fliparoo
            )
            subgraphs_updated.extend(extended_subgraphs)
        signed_subgraphs = subgraphs_updated

    for signed_subgraph in signed_subgraphs:
        graph = signed_subgraph.supergraph
        assert signed_subgraph.components == 1
        final_signed_node = signed_subgraph.nodes[0]
        if final_signed_node.sign != 1:
            continue
        final_node = final_signed_node.node

        opstr = f"{last_str} = {final_node.op.left}{final_node.optype.op_str}{final_node.op.right}"
        final_node.op = CodeOp(parse(opstr))
        reconnect_fliparoo_outputs(graph, final_node)
        graph.update()
        yield graph


def extract_fliparoo_signed_inputs(fliparoo: Fliparoo) -> SignedSubGraph:

    graph = fliparoo.graph
    signed_inputs = SignedSubGraph([], graph)
    for node in fliparoo:
        prev = fliparoo.previous(node)
        left, right = map(SignedNode, node.incoming_nodes)
        if right.node != prev:
            right.sign = -1 if node.is_sub else 1
            signed_inputs.add_node(right)
        if left.node != prev:
            if node.is_sub and right.node == prev:
                signed_inputs.change_signs()
            signed_inputs.add_node(left)
        if prev:
            graph.remove_node(prev)
    graph.remove_node(fliparoo.last)
    return signed_inputs


def disconnect_fliparoo_outputs(fliparoo: Fliparoo):
    # remember positions of the last node with a DummyNode placeholder
    dummy = DummyNode()
    fliparoo.graph.add_node(dummy)
    fliparoo.last.reconnect_outgoing_nodes(dummy)


def reconnect_fliparoo_outputs(graph: EFDFormulaGraph, last_node: Node):
    dummy = next(filter(lambda x: isinstance(x,DummyNode),graph.nodes))
    dummy.reconnect_outgoing_nodes(last_node)
    graph.remove_node(dummy)
    assert not list(filter(lambda x: isinstance(x,DummyNode),graph.nodes))


def combine_all_pairs_signed_nodes(
    signed_subgraph: SignedSubGraph, fliparoo: Fliparoo
) -> List[SignedSubGraph]:
    signed_subgraphs = []
    l = signed_subgraph.components
    for i in range(l):
        for j in range(i + 1, l):
            csigned_subgraph = signed_subgraph.deepcopy()
            v, w = csigned_subgraph[i], csigned_subgraph[j]
            combine_signed_nodes(csigned_subgraph, v, w, fliparoo)
            signed_subgraphs.append(csigned_subgraph)
    return signed_subgraphs


def combine_signed_nodes(
    subgraph: SignedSubGraph,
    left_signed_node: SignedNode,
    right_signed_node: SignedNode,
    fliparoo: Fliparoo,
):

    result = fliparoo.last.result
    left_node, right_node = left_signed_node.node, right_signed_node.node
    sign = 1
    operator = OpType.Mult
    if isinstance(fliparoo, AddSubFliparoo):
        s0, s1 = left_signed_node.sign, right_signed_node.sign
        if s0 == 1:
            operator = OpType.Add if s1 == 1 else OpType.Sub

        if s0 == -1 and s1 == 1:
            operator = OpType.Sub
            left_node, right_node = right_node, left_node

        # propagate the sign
        if s0 == -1 and s1 == -1:
            operator = OpType.Add
            sign = -1

    new_node = CodeOpNode.from_str(
        f"Fliparoo{randint(1,100000)}", left_node.result, operator, right_node.result
    ) # TODO the randint is not ideal
    new_node.incoming_nodes = [left_node, right_node]
    left_node.outgoing_nodes.append(new_node)
    right_node.outgoing_nodes.append(new_node)
    subgraph.supergraph.add_node(new_node)
    new_node = SignedNode(new_node)
    new_node.sign = sign
    subgraph.remove_node(left_signed_node)
    subgraph.remove_node(right_signed_node)
    subgraph.add_node(new_node)
