class Status:
    def __str__(self):
        raise NotImplementedError("Can not call __str__ on abstract class "
                                  "Status")

    def ok(self):
        raise NotImplementedError("Can not call ok on abstract class Status")
