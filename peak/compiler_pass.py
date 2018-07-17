import peak_ir

class DslPass:
    def __init__(self, ir : peak_ir.Ir) -> None:
        self._ir = ir

    def run(self):
        raise NotImplementedError("Can not call run() on abstract "
                                  "class DslPass")
