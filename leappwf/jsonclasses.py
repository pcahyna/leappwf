""" Generate classes automatically based on JSON """

import json
import logging
import os
import sys
from jsonschema import exceptions, validate

from .msgtypes import ShellCommandStatus
from .portannotation import MsgType


class JSONClassFactory(object):
    """ Parse JSON files, generate and keep track of defined classes """
    def __init__(self):
        # FIXME: Current idea is to use a JSON Schema to define classes
        # but we need to add 'superclass' to JSON Schema vocabulary to
        # keep track of hierarchy. Also 'properties' are being ignored
        # by now, it should be properly handled if necessity shows up
        self._schema = {
            'title': 'Class',
            'type': 'object',
            'properties': {
                'type': {'type': 'string'},
                'superclass': {'type': 'string'},
                'properties': {'type': 'object'}
            }
        }

        self._classes_data = {}
        self._classes = {}

    @property
    def classes(self):
        """ Return a list of all generated classes """
        return self._classes.keys()

    def _parse_json_file(self, file_path, class_name=None):
        """ Parse and validate JSON file """
        with open(file_path, 'r') as stream:
            try:
                class_data = json.load(stream)
            except ValueError:
                logging.warning("%s: decoding JSON has failed", file_path)
                return

            try:
                validate(class_data, self._schema)
            except exceptions.ValidationError as err:
                logging.warning("%s: validating JSON has failed: %s",
                                file_path, err)
                return

        name = None
        if class_name:
            name = class_name
        else:
            file_name = os.path.basename(file_path)
            name, _ = os.path.splitext(file_name)

        self._classes_data.update({name: class_data})

    def add_json_class(self, json_path, class_name=None):
        """ Load and parse provided JSON file with class definition """
        if not json_path.endswith('.json'):
            logging.warning("%s not JSON file ignored", json_path)
            return

        self._parse_json_file(json_path, class_name)

    def get_class(self, name):
        """ Return generated class by name """
        if name not in self._classes.keys():
            return None

        return self._classes[name]

    def _generate_class(self, name, superclass):
        """ Generate Class from data """
        if superclass:
            self._classes.update({name: type(name, (superclass,), {})})
            return

        self._classes.update({name: type(name, (MsgType,), {})})

    def generate_classes(self):
        """ Generate all classes """
        while True:
            pending = {}
            something_built = False

            for name, data in self._classes_data.items():
                if name in self.classes:
                    continue

                superclass_name = None
                if u'superclass' in data:
                    superclass_name = data[u'superclass'].encode('ascii')

                superclass = None
                if superclass_name in self.classes:
                    superclass = self.get_class(superclass_name)
                else:
                    try:
                        superclass = getattr(sys.modules[__name__],
                                             superclass_name)
                    except AttributeError:
                        superclass = None

                if not superclass_name or superclass:
                    self._generate_class(name, superclass)
                    something_built = True
                    continue

                pending.update({name: data})

            if not pending:
                break
            elif not something_built:
                logging.warning("Classes not built for missing deps: %s",
                                pending)

                break
