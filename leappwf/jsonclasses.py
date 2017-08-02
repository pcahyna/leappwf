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

    def actor_classes(self, src_actor):
        """ Return a list of all generated classes for a src actor """
        if src_actor not in self._classes:
            return []

        return self._classes[src_actor].keys()

    def _parse_json_file(self, src_actor, file_path, class_name=None):
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

        if src_actor not in self._classes_data:
            self._classes_data.update({src_actor: []})

        self._classes_data[src_actor].append((name, class_data))

    def add_json_class(self, src_actor, json_path, class_name=None):
        """ Load and parse provided JSON file with class definition """
        if not json_path.endswith('.json'):
            logging.warning("%s not JSON file ignored", json_path)
            return

        self._parse_json_file(src_actor, json_path, class_name)

    def get_actor_class(self, src_actor, class_name):
        """ Return generated class by name """
        if class_name not in self.actor_classes(src_actor):
            return None

        return self._classes[src_actor][class_name]

    def _generate_class(self, src_actor, name, superclass_name=None):
        """ Generate Class from data """
        superclass = None
        if superclass_name:
            # FIXME: THIS WILL FAIL
            if superclass_name in self.actor_classes(src_actor):
                superclass = self.get_actor_class(src_actor, superclass_name)
            else:
                try:
                    superclass = getattr(sys.modules[__name__],
                                         superclass_name)
                except AttributeError:
                    superclass = None

            if not superclass:
                return False

        new_class = None
        if superclass:
            new_class = type(name, (superclass,), {})
        else:
            new_class = type(name, (MsgType,), {})

        if src_actor not in self._classes:
            self._classes.update({src_actor: {}})

        self._classes[src_actor].update({name: new_class})
        return True

    def generate_classes(self):
        """ Generate all classes """
        for src_actor, classes_data in self._classes_data.items():
            while True:
                pending = ()
                something_built = False

                for name, data in classes_data:
                    if name in self.actor_classes(src_actor):
                        continue

                    superclass_name = None
                    if u'superclass' in data:
                        superclass_name = data[u'superclass'].encode('ascii')

                    if self._generate_class(src_actor, name, superclass_name):
                        something_built = True
                    else:
                        pending.append(name)

                if not pending:
                    break
                elif not something_built:
                    logging.warning("Classes not built for missing deps: %s",
                                    pending)

                    break
