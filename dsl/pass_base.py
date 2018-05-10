import pe_ir_context as context
import pe_ir_nodes as nodes


# Base class for all compiler-like passes. Children should *only* override the
# init_pass() and visit_* functions.
class PassBase:
    def __init__(self):
        pass

    def __call__(self, ctx):
        if not isinstance(ctx, context.IrContext):
            raise ValueError("Expected ctx to be of type "
                             "pe_ir_context.IrContext")
        self.init_pass()
        for node in ctx.get_nodes():
            self.process_node(node)

    def init_pass(self):
        pass

    def process_node(self, node):
        if not isinstance(node, nodes.IrNode):
            return
        _type = type(node)
        fn_name = "visit_" + _type.__name__
        getattr(self, fn_name)(node)

    def visit_Literal(self, node):
        pass

    def visit_VariableDeclaration(self, node):
        pass

    def visit_Name(self, node):
        pass

    def visit_Expression(self, node):
        pass

    def visit_Assignment(self, node):
        pass

    def visit_SwitchCase(self, node):
        pass
