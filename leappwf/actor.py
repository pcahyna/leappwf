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
    inports_data_path = '~/.leappwf/actors_inport'
    outports_key = 'outports'

    def _default_prefunc(self, inports, inportargs):
        """ Default function to run before main script """
        logging.debug("[RUNNING] [pre] (default): %s", self.name)

        inports_data = {}
        for arg in inportargs:
            if isinstance(arg, MsgType):
                if arg.errorinfo:
                    raise PrereqError("required actor failed",
                                      arg.srcname,
                                      arg.errorinfo)

                if isinstance(arg, ShellCommandStatus) and arg.payload:
                    for port, portannotation in inports.items():
                        if isinstance(arg, portannotation.annotation.msgtype):
                            inports_data.update({port: arg.payload})
                            break

        inports_file = ''
        if inports_data:
            if not os.path.exists(os.path.expanduser(self.inports_data_path)):
                try:
                    os.makedirs(os.path.expanduser(self.inports_data_path))
                except os.error as err:
                    logging.warning("Error creating input data path: %s",
                                    err)

            try:
                inports_file = os.path.join(
                    os.path.expanduser(self.inports_data_path),
                    self.name + '_in.json')

                with open(inports_file, 'w') as infile:
                    json.dump(inports_data, infile)
            except IOError as err:
                logging.warning("Failed to write actor inports data: %s",
                                err)
        return inportargs, inports_file

    def _default_postfunc(self, res):
        """ Default function to run after main script """
        logging.debug("[RUNNING] [post] (default): %s", self.name)

        outports_data = {}
        try:
            json_data = json.loads(res[1])
            if isinstance(json_data, dict) and self.outports_key in json_data:
                outports_data = json_data[self.outports_key]
        except ValueError:
            pass

        payload = None
        if self.outports.keys()[0] in outports_data:
            payload = outports_data[self.outports.keys()[0]]

        return self.outports.values()[0].annotation.msgtype(self.name,
                                                            None,
                                                            payload)

    def _execfunc(self, _, inports_file):
        """ Method that should be executed by actor"""
        logging.debug("[RUNNING]: %s", self.name)

        child = Popen(['sudo', self._script, inports_file],
                      stdin=PIPE,
                      stdout=PIPE,
                      stderr=PIPE)
        out, err = child.communicate()
        return (child.returncode, out, err)

    def _allfunc(self, *inportargs):
        try:
            preres, inports_file = self._prefunc(self.inports, inportargs)
            try:
                res = self._execfunc(preres, inports_file)
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
                 script,
                 args=(),
                 kwargs={},
                 inports=None,
                 inports_annotation=None,
                 outports=None,
                 outports_annotation=None):

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
