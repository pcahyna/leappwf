#!/usr/bin/env bash

RPM_LIST=`rpm -qa`

OUT_JSON="{ \"outports\": { \"RPMList\": ["
SEP=" "
for PKG in ${RPM_LIST}; do
    printf -v OUT_JSON '%s%s"%s"' "${OUT_JSON}" "${SEP}" "${PKG}"
    SEP=,
done
OUT_JSON+="] } }"

echo ${OUT_JSON}
