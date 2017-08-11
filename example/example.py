#!/usr/bin/env python
""" Build and run workflow using LeApp Workflow module """

import leappwf

if __name__ == '__main__':
    wf = leappwf.LeAppWorkflow('./actors')
    wf.load_actors()
    ret = wf.run_actors()
    for actor, data in ret.items():
        print("* {}:".format(actor))
        #if data['payload']:
        #    print("[payload]: {}".format(data['payload']))
        if data['errorinfo']:
            print("\t[errorinfo]: {}".format(data['errorinfo']))
        else:
            print("\t[OK]")
