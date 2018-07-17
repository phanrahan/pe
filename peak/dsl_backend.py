import copy
import dsl_ir

class DslBackend:
    def __init__(self, ir : dsl_ir.Ir):
        self._ir = copy.deepcopy(ir)

    def generate(self):
        raise NotImplementedError("Can not call generate() on abstract class "
                                  "DslBackend")
