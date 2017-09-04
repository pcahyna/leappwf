""" Handle actors execution using Workflow programming """

import logging

from .actor import AnnotatedFuncActor, AnnotatedSnActor
from .msgtypes import ShellCommandStatus, Trigger
from .portannotation import (
    All, Any,
    DstPortAnnotation,
    FinalPortAnnotation,
    InitialPortAnnotation,
    PortAnnotation,
    connectactors)

from snactor.registry import get_actor, get_registered_actors

_PORT_NAME_KEY = 'name'
_PORT_SRC_KEY = 'src'
_PORT_TYPE_KEY = 'type'

_DEFAULT_INPORT = 'default_in'


class Workflow(object):
    """ Manage dependencies between actors and execute workflow """

    def __init__(self):
        self._actors = {}
        self.snactors = {}

    def snactor2wowp(self, sn_actor):
        """ Parse actor definition and return an annotated WOW:-P actor """
        in_names = []
        in_annotation = {}
        if not sn_actor.definition.inputs:
            # If no inport was defined via YAML file use the Trigger one
            in_names.append(_DEFAULT_INPORT)
            in_annotation.update({_DEFAULT_INPORT: DstPortAnnotation(Trigger,
                                                                     Any)})
        for port in sn_actor.definition.inputs:
            # not used yet ...
            if _PORT_SRC_KEY not in port:
                # ... so we will be always taking this branch for now
                psrc = Any
            elif port[_PORT_SRC_KEY] == '*':
                psrc = All
            else:
                psrc = port[_PORT_SRC_KEY]

            pname = port[_PORT_NAME_KEY]
            print (pname)
            # we don't derive inport name from source port, at least not yet.
            # pname = None
            # if _PORT_NAME_KEY in port:
            #     pname = port[_PORT_NAME_KEY]
            # else:
            #     pname = psrc + _INPORT_SUFFIX

            msg_type = None
            if _PORT_TYPE_KEY in port:
                #ptype, _ = os.path.splitext(port[_PORT_TYPE_KEY])
                ptype = port[_PORT_TYPE_KEY]

                msg_type = ptype
                # self.class_factory.get_actor_class(sn_actor.name,
                #                                              ptype)

            #the following allows to inherit inport type from connected outport type.
            #since we dn't do that yet, it is commented out - and would need modifications for snactor
            # elif isinstance(psrc, types.StringTypes):
            #     if psrc in self.actors_data:
            #         if len(self.actors_data[psrc].outports) == 1:
            #             oport = self.actors_data[psrc].outports[0]
            #             if _PORT_TYPE_KEY in oport:
            #                 ptype, _ = os.path.splitext(oport[_PORT_TYPE_KEY])
            #                 msg_type = self.class_factory.get_actor_class(psrc,
            #                                                               ptype)
            #         else:
            #             logging.warning("skip %s: source actor %s has multiple outports",
            #                             sn_actor.name, psrc)
            #     else:
            #         logging.warning("skip %s: source actor %s not found",
            #                         sn_actor.name, psrc)
            else:
                # no type information and wildcarded source actor. Let's use the most generic type
                msg_type = 'MsgType'

            if msg_type:
                in_names.append(pname)
                in_annotation.update({pname: DstPortAnnotation(msg_type,
                                                               psrc)})
            else:
                logging.warning("skip %s: no inport type information",
                                sn_actor.name)
                return

        out_names = []
        out_annotation = {}
        for port in sn_actor.definition.outputs:

            ptype = None
            if _PORT_TYPE_KEY in port:
                #    ptype, _ = os.path.splitext(port[_PORT_TYPE_KEY])
                ptype = port[_PORT_TYPE_KEY]

            pname = port[_PORT_NAME_KEY]
            # we dont't derive inport name from source port, at least not yet.
            #pname = None
            # if _PORT_NAME_KEY in port:
            #     pname = port[_PORT_NAME_KEY]
            # else:
            #     pname = ptype

            msg_type = None
            if ptype:
                msg_type = ptype

                #msg_type = self.class_factory.get_actor_class(sn_actor.name,
                #                                             ptype)

            if msg_type:
                out_names.append(pname)
                out_annotation.update({pname: PortAnnotation(msg_type)})
            else:
                logging.warning("skip %s: no outport provided",
                                sn_actor.name)
                return

        self.add_actor(AnnotatedSnActor(
            sn_actor,
            inports=in_names,
            inports_annotation=in_annotation,
            outports=out_names,
            outports_annotation=out_annotation
        ))

    def add_actor(self, actor):
        """ Add a WOW:-P actor to workflow """
        self._actors[actor.name] = actor

    def complete(self):
        """ Complete workflow by adding implementation actors for start/end"""
        def start_workflow(initial):
            """ Simple function to trigger all other actors """
            return Trigger()

        def end_workflow(stats):
            """ Simple function to unify all actors output """
            ret = {}
            for msg in stats.values():
                ret.update({msg.srcname: {'payload': msg.payload,
                                          'errorinfo': msg.errorinfo}})
            return ret

        def_start = AnnotatedFuncActor(
            func=start_workflow,
            inports=['initial'],
            inports_annotations={'initial': InitialPortAnnotation()},
            outports=['initial_out'],
            outports_annotations={'initial_out': PortAnnotation(Trigger)}
        )

        def_end = AnnotatedFuncActor(
            func=end_workflow,
            name='default_end',
            inports=['stats'],
            inports_annotations={'stats': DstPortAnnotation(ShellCommandStatus,
                                                            All)},
            outports=['final_out'],
            outports_annotations={'final_out': FinalPortAnnotation}
        )

        self.add_actor(def_start)
        #self.add_actor(def_end)

    def prepare(self):
        """ Prepare the worflow for running: resolve dependencies"""
        connectactors(self._actors.values())

    def run(self, final_actor):
        """ Execute workflow """
        workflow = self._actors[final_actor].get_workflow()
        #print(workflow.inports.keys())
        #print(workflow.outports.keys())
        ret_workflow = workflow(initial=True)
        return ret_workflow
        #['final_out'].pop()

    def load_snactors(self):
        self.snactors = {aname: get_actor(aname) for aname in get_registered_actors().keys()}
        #print (self.snactors)
        for a in self.snactors.values():
            self.snactor2wowp(a)
