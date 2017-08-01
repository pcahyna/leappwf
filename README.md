LeApp: Workflow Module
======================

LeApp Workflow Module based on wowp

Prerequisites
=============
```
# dnf copr enable amello/python-wowp
# dnf install -y python2-future python2-jsonschema python2-networkx python2-six python2-wowp
```

Install
=======
```
$ git clone https://github.com/artmello/leappwf.git
$ cd leappwf
$ pip --user install .
```

Examples
========

Inside example directory there are a folder containing multiples samples actors and a Python script that will use leappwf to parse those actors, build a workflow using wowp and run it, respecting the dependencies graph.

Running the example:
```
$ cd example/
$ ./example.py
WARNING: skip MISSING_OUTPORT: no outport description for SomeOutport
WARNING: skip NO_OUTPORT: no outport provided
WARNING: skip NO_MATCH_INPORT: no inport/outport match for NO_ONE_PROVIDES_THIS
WARNING: skip MISSING_SCRIPT: no script defined
* rsync:
[retcode]: 0
* docker_list:
[retcode]: 0
* has_docker:
[retcode]: 0
* DEP_FAIL:
[retcode]: None
* has_rsync:
[retcode]: 0
* docker:
[retcode]: 0
* basic:
[retcode]: 0
* WILL_FAIL:
[retcode]: 1
```

These are the sample actors:
- basic: No dependencies. Run with out errors. Exec 'uname -a' 
- has_docker: No dependencies. Will check if docker cmd is available.
- has_rsync: No dependencies. Will check if rsync cmd is available.
- docker: Depends on 'has_docker'. Will check if docker service is available.
- docker_list: Depends on 'has_docker'. Will list docker processes.
- rsync: Depends on 'has_rsync'. Will display rsync version.
- DEP_FAIL: Depends on 'WILL_FAIL'. Sample actor to show how to handlea failed dep.
- MISSING_OUTPORT: Will be ignored for defining unexistent outport.
- MISSING_SCRIPT: Will be ignored for missing script definition.
- NO_MATCH_INPORT: Will be ignored for requesting an inport that is not provided by any other actor.
- NO_OUTPORT: Will be ignored for missing outport definition.
- WILL_FAIL: No dependencies. All runs will fail to show as example.
