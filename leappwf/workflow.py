""" Handle actors execution using Workflow programming """

from .actor import AnnotatedFuncActor
from .msgtypes import ShellCommandStatus, Trigger
from .portannotation import (
    All,
    DstPortAnnotation,
    FinalPortAnnotation,
    InitialPortAnnotation,
    PortAnnotation,
    connectactors)


class Workflow(object):
    """ Manage dependencies between actors and execute workflow """

    def __init__(self):
        self._actors = {}

    def add_actor(self, actor):
        """ Add actor to workflow """
        self._actors[actor.name] = actor

    def run(self):
        """ Execute check workflow """
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
        self.add_actor(def_end)

        connectactors(self._actors.values())

        workflow = self._actors['default_end'].get_workflow()

        ret_workflow = workflow(initial=True)
        return ret_workflow['final_out'].pop()
