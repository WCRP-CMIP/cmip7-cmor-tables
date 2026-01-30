#!/bin/bash
# Create the CMOR CVs JSON file
#
# Works in the currently activated environment,
# therefore we recommend creating and activating a virtual environment
# before running this script (we use Python 3.13 in our CI at the time of writing).
#
# Options:
#
# -o: file in which to write the output (deafult: cmor-cvs.json)
# -r: file from which to read the requirements (default: requirements-cmor-cvs-table.txt)
# -e: install dependencies before creating the file
# -v: verbose mode
#
# If you're on windows, sorry.
# You should be able to more or less copy these commands out.

# Environment variables that this file uses.
# If they're not set, the default values are used.
# Note: the defaults below are working values.
# In future, we should switch to the commented out lines further below.
ESGVOC_FORK="${ESGVOC_FORK:=znichollscr}"
ESGVOC_REVISION="${ESGVOC_REVISION:=6f75519f4bf1a6965b4121509256a6ecdd7ec431}"
UNIVERSE_CVS_FORK="${UNIVERSE_CVS_FORK:=znichollscr}"
UNIVERSE_CVS_BRANCH="${UNIVERSE_CVS_BRANCH:=add-ukmo-entries}"
CMIP7_CVS_FORK="${CMIP7_CVS_FORK:=znichollscr}"
CMIP7_CVS_BRANCH="${CMIP7_CVS_BRANCH:=add-ukmo-entries}"
# ESGVOC_FORK="${ESGVOC_FORK:=ESGF}"
# ESGVOC_REVISION="${ESGVOC_REVISION:=}" # vTBD
# UNIVERSE_CVS_FORK="${UNIVERSE_CVS_FORK:=WCRP-CMIP}"
# UNIVERSE_CVS_BRANCH="${UNIVERSE_CVS_BRANCH:=esgvoc}"
# CMIP7_CVS_FORK="${CMIP7_CVS_FORK:=WCRP-CMIP}"
# CMIP7_CVS_BRANCH="${CMIP7_CVS_BRANCH:=esgvoc}"

verbose=0
install_env=0
out_file='cmor-cvs.json'
requirements_file='requirements-cmor-cvs-table.txt'

while getopts "o:r:ve" OPTION; do
    case $OPTION in
    o) out_file="${OPTARG}" ;;
    r) requirements_file="${OPTARG}" ;;
    v) verbose=1 ;;
    e) install_env=1 ;;
    *)
        echo "usage: $0 [-v] [-e] [-o output-file]" >&2
        exit 1
        ;;
    esac
done

function log() {
    if [[ $verbose -eq 1 ]]; then
        echo "$@"
    fi
}

if [[ $install_env -eq 1 ]]; then

    log "ESGVOC_FORK=$ESGVOC_FORK"
    log "ESGVOC_REVISION=$ESGVOC_REVISION"
    log "UNIVERSE_CVS_FORK=$UNIVERSE_CVS_FORK"
    log "UNIVERSE_CVS_BRANCH=$UNIVERSE_CVS_BRANCH"
    log "CMIP7_CVS_FORK=$CMIP7_CVS_FORK"
    log "CMIP7_CVS_BRANCH=$CMIP7_CVS_BRANCH"

    log "out_file=$out_file"
    log "requirements_file=$requirements_file"

    sed -i -E -e 's#(.*)/github.com/.*/(.*)#\1/github.com/'"${ESGVOC_FORK}"'/\2#' "${requirements_file}"
    sed -i -E -e 's#(.*)/esgf-vocab.git@.*#\1/esgf-vocab.git@'"${ESGVOC_REVISION}"'#' "${requirements_file}"
    # # Mac equivalent of the above
    # sed -i -E -e 's#\(.*\)/github.com/.*/\(.*\)#\1/github.com/'"${ESGVOC_FORK}"'/\2#' "${requirements_file}"
    # sed -i -E -e 's#\(.*\)/esgf-vocab.git@.*#\1/esgf-vocab.git@'"${ESGVOC_REVISION}"'#' "${requirements_file}"

    pip install -r "${requirements_file}"

    esgvoc config create cmip7-cvs-ci
    esgvoc config switch cmip7-cvs-ci

    esgvoc config remove-project -f cmip6
    esgvoc config remove-project -f cmip6plus
    esgvoc config remove-project -f cmip7

    esgvoc config set "universe:github_repo=https://github.com/$UNIVERSE_CVS_FORK/WCRP-universe" "universe:branch=$UNIVERSE_CVS_BRANCH"
    esgvoc config add-project cmip7 --custom --repo "https://github.com/$CMIP7_CVS_FORK/CMIP7-CVs" --branch "$CMIP7_CVS_BRANCH"

    esgvoc install

fi

esgvoc cmor-export-cvs-table --out-path "${out_file}"

log "Wrote output to ${out_file}"
