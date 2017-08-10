""" Load and run actors and build workflow """
import glob
import logging
import os
import yaml

from .actor import DirAnnotatedShellActor
from .jsonclasses import JSONClassFactory
from .msgtypes import Trigger
from .portannotation import Any, DstPortAnnotation, PortAnnotation
from .workflow import Workflow

_YAML_FILENAME = 'actordecl.yaml'

_SCRIPT_KEY = 'script'
_INPORTS_KEY = 'inports'
_OUTPORTS_KEY = 'outports'
_PORT_NAME_KEY = 'name'
_PORT_SRC_KEY = 'src'
_PORT_TYPE_KEY = 'type'

_DEFAULT_INPORT = 'default_in'
_DEFAULT_OUTPORT = 'out'
_INPORT_SUFFIX = 'in'


class ActorData(object):
    """ Handle actor's data """
    def __init__(self, name, path, data):
        self._name = name
        self._path = path
        self._data = data

    @property
    def name(self):
        """ Return actor's name """
        return self._name

    @property
    def path(self):
        """ Return actor's path """
        return self._path

    @property
    def script(self):
        """ Return actor's script """
        if self._data and _SCRIPT_KEY in self._data:
            return os.path.join(self._path, self._data[_SCRIPT_KEY])

        script_list = glob.glob(os.path.join(self._path, '*.sh'))
        if len(script_list) == 1:
            return script_list.pop()

        return None

    @property
    def inports(self):
        """ Return actor's inports """
        if self._data and _INPORTS_KEY in self._data:
            return self._data[_INPORTS_KEY]
        return []

    @property
    def outports(self):
        """ Return actor's outports """
        if self._data and _OUTPORTS_KEY in self._data:
            return self._data[_OUTPORTS_KEY]
        return []

    def set_outports(self, outports):
        """ Override current outports list """
        if self._data and _OUTPORTS_KEY in self._data:
            self._data[_OUTPORTS_KEY] = outports
        elif self._data:
            self._data.update({_OUTPORTS_KEY: outports})
        else:
            self._data = {_OUTPORTS_KEY: outports}


class LeAppWorkflow(object):
    """ LeApp Worflow based on actors """
    def __init__(self, path):
        self._workflow = Workflow()
        self._actors_path = path
        self._class_factory = JSONClassFactory()
        self._actors_data = {}

    @property
    def workflow(self):
        """ Return actor's workflow """
        return self._workflow

    @property
    def class_factory(self):
        """ Return Msg Type Class factory """
        return self._class_factory

    @property
    def actors_data(self):
        """ Return list of actors data """
        return self._actors_data

    @property
    def actors_path(self):
        """ Return path that should be scanned for actors """
        return self._actors_path

    def _add_actor(self, actor):
        """ Parse actor data and add to workflow """
        script = actor.script
        if not script:
            logging.warning("skip %s: no script defined", actor.name)
            return

        in_names = []
        in_annotation = {}
        if not actor.inports:
            # If no inport was defined via YAML file use the Trigger one
            in_names.append(_DEFAULT_INPORT)
            in_annotation.update({_DEFAULT_INPORT: DstPortAnnotation(Trigger,
                                                                     Any)})
        for port in actor.inports:
            if _PORT_SRC_KEY not in port:
                logging.warning("skip %s: no src actor defined for inport",
                                actor.name)
                return
            psrc = port[_PORT_SRC_KEY]

            pname = None
            if _PORT_NAME_KEY in port:
                pname = port[_PORT_NAME_KEY]
            else:
                pname = psrc + _INPORT_SUFFIX

            msg_type = None
            if _PORT_TYPE_KEY in port:
                ptype, _ = os.path.splitext(port[_PORT_TYPE_KEY])

                msg_type = self.class_factory.get_actor_class(actor.name,
                                                              ptype)
            else:
                if psrc in self.actors_data:
                    if len(self.actors_data[psrc].outports) == 1:
                        oport = self.actors_data[psrc].outports[0]
                        if _PORT_TYPE_KEY in oport:
                            ptype, _ = os.path.splitext(oport[_PORT_TYPE_KEY])
                            msg_type = self.class_factory.get_actor_class(psrc,
                                                                          ptype)

            if msg_type:
                in_names.append(pname)
                in_annotation.update({pname: DstPortAnnotation(msg_type,
                                                               psrc)})
            else:
                logging.warning("skip %s: no inport/outport match",
                                actor.name)
                return

        out_names = []
        out_annotation = {}
        for port in actor.outports:
            ptype = None
            if _PORT_TYPE_KEY in port:
                ptype, _ = os.path.splitext(port[_PORT_TYPE_KEY])

            pname = None
            if _PORT_NAME_KEY in port:
                pname = port[_PORT_NAME_KEY]
            else:
                pname = ptype

            msg_type = None
            if ptype:
                msg_type = self.class_factory.get_actor_class(actor.name,
                                                              ptype)

            if msg_type:
                out_names.append(pname)
                out_annotation.update({pname: PortAnnotation(msg_type)})
            else:
                logging.warning("skip %s: no outport provided",
                                actor.name)
                return

        self.workflow.add_actor(DirAnnotatedShellActor(
            actor.name,
            script,
            inports=in_names,
            inports_annotation=in_annotation,
            outports=out_names,
            outports_annotation=out_annotation
        ))

    def _parse_inports(self, actor_data):
        """ Parse inports data """
        if actor_data.inports:
            for port in actor_data.inports:
                if _PORT_TYPE_KEY in port:
                    port_json = os.path.join(actor_data.path,
                                             port[_PORT_TYPE_KEY])
                    if not os.path.isfile(port_json):
                        logging.warning("skip %s: no inport descr for %s",
                                        actor_data.name,
                                        port[_PORT_TYPE_KEY])
                        return False
                    self.class_factory.add_json_class(actor_data.name,
                                                      port_json)

        return True

    def _parse_outports(self, actor_data):
        """ Parse outports data """
        if actor_data.outports:
            for port in actor_data.outports:
                if _PORT_TYPE_KEY in port:
                    port_json = os.path.join(actor_data.path,
                                             port[_PORT_TYPE_KEY])
                    if not os.path.isfile(port_json):
                        logging.warning("skip %s: no outport descr for %s",
                                        actor_data.name,
                                        port[_PORT_TYPE_KEY])
                        return False

                    self.class_factory.add_json_class(actor_data.name,
                                                      port_json)
                else:
                    logging.warning("skip %s: no outport descr",
                                    actor_data.name)
                    return False

        else:
            port_json = os.path.join(actor_data.path,
                                     _DEFAULT_OUTPORT + '.json')
            if not os.path.isfile(port_json):
                logging.warning("skip %s: no outport provided",
                                actor_data.name)
                return False

            outport_name = _DEFAULT_OUTPORT
            actor_data.set_outports([{_PORT_TYPE_KEY: outport_name + '.json'}])
            self.class_factory.add_json_class(actor_data.name,
                                              port_json,
                                              outport_name)

        return True

    def load_actors(self):
        """ Scan actors path and parse provided data """
        if not self.actors_path or not os.path.isdir(self.actors_path):
            logging.warning("%s should be a directory",
                            self.actors_path)
            return

        for actor_name in os.listdir(os.path.join(self.actors_path)):
            actor_path = os.path.join(self.actors_path, actor_name)
            if not os.path.isdir(actor_path):
                logging.warning("skip %s: not a dir", actor_name)
                continue

            yaml_file = os.path.join(actor_path, _YAML_FILENAME)

            actor_yaml = None
            if os.path.isfile(yaml_file):
                with open(yaml_file, 'r') as stream:
                    try:
                        actor_yaml = yaml.load(stream)

                    except yaml.YAMLError as err:
                        logging.warning("loading yaml error: %s", err)

            actor_data = ActorData(actor_name,
                                   actor_path,
                                   actor_yaml)

            parsed_inports = self._parse_inports(actor_data)
            parsed_outports = self._parse_outports(actor_data)
            if parsed_inports and parsed_outports:
                self.actors_data.update({actor_name: actor_data})

        self.class_factory.generate_classes()

        for _, data in self.actors_data.items():
            self._add_actor(data)

    def run_actors(self):
        """ Run workflow """
        return self.workflow.run()
