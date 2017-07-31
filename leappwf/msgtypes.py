from .portannotation import MsgType


class Trigger(MsgType):
    def __init__(self):
        super(Trigger, self).__init__(None, None, None)


class ShellCommandStatus(MsgType):
    def __init__(self, srcname, errorinfo, retcode):
        super(ShellCommandStatus, self).__init__(srcname,
                                                 errorinfo,
                                                 retcode)
