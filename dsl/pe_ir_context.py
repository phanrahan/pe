import pe_ir_nodes


class IrContext:
    def __init__(self):
        self.nodes = []

    def add_node(self, node):
        if not isinstance(node, pe_ir_nodes.IrNode):
            raise ValueError("node must be a proper IrNode")
        self.nodes.append(node)

    def get_nodes(self):
        return self.nodes
