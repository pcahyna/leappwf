""" Actors able to execute checks on our workflow """

import json
import logging
import os
from subprocess import Popen, PIPE
from wowp.actors import FuncActor

from .portannotation import ActorError, MsgType
from .msgtypes import ShellCommandStatus


class PrereqError(ActorError):
    def __init__(self, errmsg, prereqname, errdetails):
        super(PrereqError, self).__init__("skipped", errmsg, errdetails)
        self.prereqname = prereqname


class ScriptError(ActorError):
    pass


class AnnotatedFuncActor(FuncActor):
    def __init__(self,
                 func,
                 args=(), kwargs={},
                 name=None,
                 inports=None,
                 inports_annotations=None,
                 outports=None,
                 outports_annotations=None):

        super(AnnotatedFuncActor, self).__init__(func,
                                                 args, kwargs,
                                                 name=name,
                                                 inports=inports,
                                                 outports=outports)

        for ipn in self.inports.keys():
            self.inports[ipn].annotation = inports_annotations[ipn]

        for opn in self.outports.keys():
            self.outports[opn].annotation = outports_annotations[opn]


class DirAnnotatedShellActor(AnnotatedFuncActor):
    output_data_path = '~/.leappwf/actors_output'

    def _default_prefunc(self, _, inportargs):
        """ Default function to run before main script """
        logging.debug("[RUNNING] [pre] (default): %s", self.name)

        for arg in inportargs:
            if isinstance(arg, MsgType):
                if arg.errorinfo:
                    raise PrereqError("required actor failed",
                                      arg.srcname,
                                      arg.errorinfo)

                if isinstance(arg, ShellCommandStatus):
                    if arg.payload != 0:
                        raise PrereqError(
                            "required actor returned a nonzero exit code",
                            arg.srcname,
                            arg.payload)
        return inportargs

    def _default_postfunc(self, res):
        """ Default function to run after main script """
        logging.debug("[RUNNING] [post] (default): %s", self.name)

        json_keys = ['actor_src', 'actor_rc', 'actor_stdout', 'actor_stderr']
        json_data = dict(zip(json_keys, [self.name] + list(res)))

        if not os.path.exists(os.path.expanduser(self.output_data_path)):
            try:
                os.makedirs(os.path.expanduser(self.output_data_path))
            except os.error as err:
                logging.warning("Failed to create path for actors' output: %s",
                                err)

        try:
            with open(os.path.join(os.path.expanduser(self.output_data_path),
                                   self.name + '_out.json'), 'w') as outfile:
                json.dump(json_data, outfile)
        except IOError as err:
            logging.warning("Failed to write actor output: %s",
                            err)

        return self.outports.values()[0].annotation.msgtype(self.name,
                                                            None,
                                                            res[0])

    def _execfunc(self, _):
        """ Method that should be executed by actor"""
        logging.debug("[RUNNING]: %s", self.name)

        script_input = open(self._script)
        child = Popen(self._target_cmd,
                      stdin=script_input,
                      stdout=PIPE,
                      stderr=PIPE)
        out, err = child.communicate()
        return (child.returncode, out, err)

    def _allfunc(self, *inportargs):
        try:
            preres = self._prefunc(self.inports, inportargs)
            try:
                res = self._execfunc(preres)
            except Exception as ee:
                raise ScriptError("failed", "script execution failed", ee)

        except ActorError as ae:
            if len(self.outports) == 1:
                excres = self.outports.at(0).annotation.msgtype(self.name,
                                                                ae,
                                                                None)
            else:
                excres = tuple(port.annotation.msgtype(self.name, ae, None) for port in self.outports)
            return excres

        return self._postfunc(res)

    def __init__(self,
                 name,
                 target_cmd,
                 script,
                 args=(),
                 kwargs={},
                 inports=None,
                 inports_annotation=None,
                 outports=None,
                 outports_annotation=None):

        self._target_cmd = target_cmd
        self._prefunc = self._default_prefunc
        self._postfunc = self._default_postfunc
        self._script = script

        super(DirAnnotatedShellActor, self).__init__(self._allfunc,
                                                     args, kwargs,
                                                     name,
                                                     inports,
                                                     inports_annotation,
                                                     outports,
                                                     outports_annotation)
