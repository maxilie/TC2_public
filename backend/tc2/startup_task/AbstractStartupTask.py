from tc2.TC2Program import TC2Program


class AbstractStartupTask:
    """
    Contains code to be run off-thread at startup, usually for debugging.
    """
    program: TC2Program

    def __init__(self,
                 program: TC2Program):
        self.program = program

    def run(self) -> None:
        raise NotImplementedError
