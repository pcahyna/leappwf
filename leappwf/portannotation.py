import logging

from wowp.actors import DictionaryMerge

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

def matchtypes(intype, outtype):
    # no classes yet for snactor
    #return issubclass(outtype, intype)
    return intype == outtype

def matchport(inport, outport):
    try:
        return (matchtypes(inport.annotation.msgtype, outport.annotation.msgtype) and
                (inport.annotation.srcname == Any or
                 inport.annotation.srcname == All or
                 outport.owner.name == inport.annotation.srcname ))
    except AttributeError:
        #print('Warning: no annotation in ', str(inport), " or ", str(outport))
        return False

class MsgType(object):
    def __init__(self, srcname, errorinfo, payload):
        self.srcname=srcname
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
            logging.debug('initial found %s: %s(%s)', ip.owner, ip.owner.name, ip.name)
            continue

        if ip.annotation.srcname==All:
            ip.annotation.matchports=[]

        for op in alloutports:
            if matchport(ip, op):
                logging.debug("matched! %s: %s(%s) -> %s(%s)", op.owner, op.owner.name, op.name, ip.owner.name, ip.name)
                opcount += 1
                if ip.annotation.srcname==All:
                    logging.debug("wildcard matched! %s", ip)
                    ip.annotation.matchports.append(op)
                else:
                    ip += op
                # we do not want to have more than one output port connected to one input port
                # break
        if ip.annotation.srcname == All:
            namesports = {(mp.owner.name + '__' + mp.name):mp for mp in ip.annotation.matchports}
            logging.debug('adding DictionaryMerge for %s', ip)
            ip.annotation.linkedactor = DictionaryMerge(inport_names=namesports.keys(), outport_name='out')
            ip += ip.annotation.linkedactor.outports['out']
            for n, mp in namesports.items():
                ip.annotation.linkedactor.inports[n] += mp
        else:
            if opcount > 1:
                logging.warning("Warning: input port %s has %d output ports", ip, opcount)
