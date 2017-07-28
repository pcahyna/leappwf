from wowp.actors import DictionaryMerge
import logging

class Any(object):
    """A unique wildcard object

    Note that we cannot use None as this can be used by users
    """

    def __init__(self):
        raise Exception('Any cannot be instantiated')

class All(object):
    """A unique wildcard object

    Note that we cannot use None as this can be used by users
    """

    def __init__(self):
        raise Exception('All cannot be instantiated')

class PortAnnotation(object):
    def __init__(self, msgtype):
        self.msgtype = msgtype


class DstPortAnnotation(PortAnnotation):
    def __init__(self, msgtype, srcname=Any):
        super(DstPortAnnotation, self).__init__(msgtype)
        self.srcname = srcname

#dummy class annotating workflow results
class FinalPortAnnotation(PortAnnotation):
    def __init__(self):
        pass

class InitialPortAnnotation(DstPortAnnotation):
    def __init__(self):
        pass

#class AnnotatedInPort(InPort):
#    def __init__(self, *args, **kwargs):
#        super().__init__(*args, **kwargs)


def matchport(inport, outport):
    try:
        return (issubclass(outport.annotation.msgtype, inport.annotation.msgtype) and
                (inport.annotation.srcname == Any or
                 inport.annotation.srcname == All or
                 outport.owner.name == inport.annotation.srcname ))
    except AttributeError:
        #print('Warning: no annotation in ', str(inport), " or ", str(outport))
        return False

class MsgType(object):
    def __init__(self, srcname, output, errorinfo, payload):
        self.srcname=srcname
        self.output=output
        # errorinfo is an ActorError exception defined below
        self.errorinfo=errorinfo
        self.payload=payload

class ActorError(Exception):
    def __init__(self, errtype, errmsg, errdetails):
        # "failed" or "skipped"
        self.errtype = errtype
        # what error happened
        self.errmsg = errmsg
        # more details: why it happened
        self.errdetails = errdetails
    def __str__(self):
        return "actor " + self.errtype + ": " + self.errmsg + " " + self.errdetails.__str__()

def connectactors(actors):
    allinports=[p for a in actors for p in a.inports.values()]
    alloutports=[p for a in actors for p in a.outports.values()]

    for ip in allinports:
        opcount = 0
        if isinstance(ip.annotation, InitialPortAnnotation):
            continue

        if ip.annotation.srcname==All:
            ip.annotation.matchports=[]

        for op in alloutports:
            if matchport(ip, op):
                # print("matched! ", ip)
                opcount += 1
                if ip.annotation.srcname==All:
                    # print("wildcard matched! ", ip)
                    ip.annotation.matchports.append(op)
                else:
                    ip += op
                # we do not want to have more than one output port connected to one input port
                # break
        if ip.annotation.srcname == All:
            names = [mp.name for mp in ip.annotation.matchports]
            ip.annotation.linkedactor = DictionaryMerge(inport_names=names, outport_name='out')
            ip += ip.annotation.linkedactor.outports['out']
            for mp in ip.annotation.matchports:
                ip.annotation.linkedactor.inports[mp.name] += mp
        else:
            if opcount > 1:
                print("Warning: input port ", ip, "has {} output ports".format(opcount) )
