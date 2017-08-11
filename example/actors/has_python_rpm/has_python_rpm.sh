#!/usr/bin/env bash

# Actors can receive as input a path to JSON file containning data from
# previous actor executed on the Workflow. Following code will provide
# following variables: $ACTOR_SRC, $ACTOR_RC, $ACTOR_STDOUT, $ACTOR_STDERR
if [ $# -eq 1 -a -f "${1}" ]; then
    eval `python -c "
import json, sys
try:
    data = json.loads(open('"${1}"').read())
except ValueError:
    sys.exit(1)
print('; '.join(['{}=\"{}\"'.format(k.upper(), d) for k, d in data.items()]))"`
fi


echo "$RPM_LIST" | grep -o python | wc -l
