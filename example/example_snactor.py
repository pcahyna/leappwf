#!/usr/bin/env python
""" Build and run workflow using LeApp Workflow module """

import leappwf
from pprint import pprint
from snactor.loader import load
from snactor.registry import get_actor, _REGISTERED_ACTORS

if __name__ == '__main__':
    load('sn_actors', tags=('check_target',))
    #a = get_actor('simple-actor')
    #print (a.definition.__dict__)

    print(_REGISTERED_ACTORS.keys())

    wf = leappwf.Workflow()
    wf.load_snactors()
    wf.complete()
    wf.prepare()
    pprint(wf.run('check_target')['targetinfo'].pop().payload)
    #    wf = leappwf.LeAppWorkflow('./actors')
    # wf.load_actors()
    # ret = wf.run_actors()
    # for actor, data in ret.items():
    #     print("* {}:".format(actor))
    #     #if data['payload']:
    #     #    print("[payload]: {}".format(data['payload']))
    #     if data['errorinfo']:
    #         print("\t[errorinfo]: {}".format(data['errorinfo']))
    #     else:
    #         print("\t[OK]")
