from bit_vector import BitVector
import pass_base
import pe_ir_nodes as nodes
import pe_ir_ops as ops
import pe_ir_types as types

# This pass checks that all types in the IR tree are valid. Note that this does
# not check that the types used within the tree nodes are valid (e.g. InputType
# etc.) rather that the tree is well formed and that the python types we expect
# are in fact there.
class MetaTypeCheckPass(pass_base.PassBase):
    def __init__(self):
        self.violations = None

    def init_pass(self):
        self.violations = []

    def general_type_checker(self, node, checks):
        for field_name, valid_types in checks.items():
            field = getattr(node, "get_%s" % field_name)()
            valid = False
            for t in valid_types:
                if isinstance(field, t):
                    valid = True
                    break
            if not valid:
                self.violations.append((field_name, valid_types, type(field)))

    def visit_Literal(self, node):
        checks = {
            'type' : (types.Type,),
            'value' : (BitVector, str,),
        }
        self.general_type_checker(node, checks)

    def visit_VariableDeclaration(self, node):
        checks = {
            'id' : (str,),
            'type' : (types.Type,),
        }
        self.general_type_checker(node, checks)

    def visit_Name(self, node):
        self.general_type_checker(node, {'id' : (str,)})

    def visit_Expression(self, node):
        self.general_type_checker(node, {'op' : (ops.Op,)})
        for arg in node.get_arguments():            
            self.process_node(arg)

    def visit_Assignment(self, node):
        checks = {
            'lhs' : (nodes.Name,),
            'rhs' : (nodes.Expression, nodes.Name, nodes.Literal),
        }
        self.general_type_checker(node, checks)
        self.process_node(node.get_lhs())
        self.process_node(node.get_rhs())

    def visit_SwitchCase(self, node):
        checks = {
            'subject': (nodes.Name,),
            'case_map': (dict,),
        }
        self.general_type_checker(node, checks)
        for case, body in node.get_case_map().items():
            if not isinstance(case, nodes.Literal):
                self.violations.append(('case', (nodes.Literal,), type(case)))
            if not isinstance(body, list):
                self.violations.append(('case_body', (list,), type(body)))
            for bi in body:
                if not isinstance(bi, nodes.IrNode):
                    self.violations.append(('case_body element',
                                            (nodes.IrNode,), type(bi)))
                else:                    
                    self.process_node(bi)

    def get_violations(self):
        return self.violations
