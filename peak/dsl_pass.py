import dsl_ir

class DslPass:
    def __init__(self, ir : dsl_ir.Ir) -> None:
        self._ir = ir

    def run(self):
        raise NotImplementedError("Can not call run() on abstract "
                                  "class DslPass")
