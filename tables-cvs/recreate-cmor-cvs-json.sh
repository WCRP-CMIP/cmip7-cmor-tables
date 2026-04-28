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
# -p: directory in which to write the split view of the output (default: split-view)
# -r: file from which to read the requirements (default: requirements-cmor-cvs-table.txt)
# -e: install dependencies before creating the file
# -v: verbose mode
#
# If you're on windows, sorry.
# You should be able to more or less copy these commands out.

# Environment variables that this file uses.
# If they're not set, the default values are used.
ESGVOC_FORK="${ESGVOC_FORK:=ESGF}"
# esgvoc_versioned=0
# ESGVOC_REVISION="${ESGVOC_REVISION:=cd1ad4d}" # v3.1.0
esgvoc_versioned=1
ESGVOC_FORK="${ESGVOC_FORK:=znichollscr}"
ESGVOC_REVISION="${ESGVOC_REVISION:=7bfe0e2b915ed52427e494b5e0036674300e247f}" # versionning branch with fixes
ESGVOC_CMIP7_DB_VERSION="${ESGVOC_CMIP7_DB_VERSION:=latest}"
UNIVERSE_CVS_FORK="${UNIVERSE_CVS_FORK:=WCRP-CMIP}"
UNIVERSE_CVS_BRANCH="${UNIVERSE_CVS_BRANCH:=esgvoc}"
CMIP7_CVS_FORK="${CMIP7_CVS_FORK:=WCRP-CMIP}"
CMIP7_CVS_BRANCH="${CMIP7_CVS_BRANCH:=esgvoc}"

verbose=0
install_env=0
out_file='cmor-cvs.json'
out_path_split_view="split-view"
requirements_file='requirements-cmor-cvs-table.txt'
generation_script='generate-cmor-cvs-table.py'

while getopts "o:d:r:s:ve" OPTION; do
    case $OPTION in
    o) out_file="${OPTARG}" ;;
    d) out_path_split_view="${OPTARG}" ;;
    r) requirements_file="${OPTARG}" ;;
    s) generation_script="${OPTARG}" ;;
    v) verbose=1 ;;
    e) install_env=1 ;;
    *)
        echo "usage: $0 [-v] [-e] [-o output-file] [-d out-path-split-view] [-r requirements-file] [-s generation-script]" >&2
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

    log "requirements_file=$requirements_file"

    sed -i -E -e 's#(.*)/github.com/.*/(.*)#\1/github.com/'"${ESGVOC_FORK}"'/\2#' "${requirements_file}"
    sed -i -E -e 's#(.*)/esgf-vocab.git@.*#\1/esgf-vocab.git@'"${ESGVOC_REVISION}"'#' "${requirements_file}"
    # Mac equivalent of the above
    sed -i -E -e 's#\(.*\)/github.com/.*/\(.*\)#\1/github.com/'"${ESGVOC_FORK}"'/\2#' "${requirements_file}"
    sed -i -E -e 's#\(.*\)/esgf-vocab.git@.*#\1/esgf-vocab.git@'"${ESGVOC_REVISION}"'#' "${requirements_file}"

    pip install -r "${requirements_file}"

    if [[ $esgvoc_versioned -eq 1 ]]; then

        log "ESGVOC_CMIP7_DB_VERSION=$ESGVOC_CMIP7_DB_VERSION"
        export ESGVOC_REGISTRY_BASE_URL=https://raw.githubusercontent.com/ltroussellier/test_esgvoc_dbs/main
        # TODO: see what happens if we run this twice
        esgvoc use "cmip7@${ESGVOC_CMIP7_DB_VERSION}"

    else

        log "UNIVERSE_CVS_FORK=$UNIVERSE_CVS_FORK"
        log "UNIVERSE_CVS_BRANCH=$UNIVERSE_CVS_BRANCH"
        log "CMIP7_CVS_FORK=$CMIP7_CVS_FORK"
        log "CMIP7_CVS_BRANCH=$CMIP7_CVS_BRANCH"
        # esgvoc config create cmip7-cvs-ci
        # esgvoc config switch cmip7-cvs-ci
        #
        # esgvoc config remove-project -f cmip6
        # esgvoc config remove-project -f cmip6plus
        # esgvoc config remove-project -f cmip7

        # # TODO: if clauses to allow both paths
        # esgvoc config set "universe:github_repo=https://github.com/$UNIVERSE_CVS_FORK/WCRP-universe" "universe:branch=$UNIVERSE_CVS_BRANCH"
        # esgvoc config add-project cmip7 --custom --repo "https://github.com/$CMIP7_CVS_FORK/CMIP7-CVs" --branch "$CMIP7_CVS_BRANCH"

        # Hopefully there is a way to raise an error on issues here soon
        # https://github.com/ESGF/esgf-vocab/issues/202
        esgvoc install

    fi

fi

log "generation_script=$generation_script"
log "out_file=$out_file"
log "out_path_split_view=$out_path_split_view"
python -m pdb "${generation_script}" --out-path "${out_file}" --out-path-split-view "${out_path_split_view}" && log "Wrote output to ${out_file} and split view to ${out_path_split_view}"

export_table_status=$?
if [ $export_table_status -ne 0 ]; then
    echo "Exporting table failed"
    exit $export_table_status
fi

# If we get to here, exit with 'success' status
exit 0
