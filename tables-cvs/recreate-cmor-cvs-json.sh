#!/bin/bash
# Handy trick (full details here https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425?permalink_comment_id=3799230):
# -e: exit immediately if any command fails
# -u: exit if you reference any unset variable
# -o: pipefail means that a non-zero exit code is returned if any command in the script fails
set -euo pipefail

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
ESGVOC_REVISION="${ESGVOC_REVISION:=4.0.1}"
### Non-versioned esgvoc config
# # Use when we are using a branches of CVs
esgvoc_versioned=0
UNIVERSE_CVS_FORK="${UNIVERSE_CVS_FORK:=znichollscr}"
UNIVERSE_CVS_REF="${UNIVERSE_CVS_REF:=zn-integration}"
# UNIVERSE_CVS_FORK="${UNIVERSE_CVS_FORK:=WCRP-CMIP}"
# UNIVERSE_CVS_REF="${UNIVERSE_CVS_REF:=esgvoc_dev}"
CMIP7_CVS_FORK="${CMIP7_CVS_FORK:=WCRP-CMIP}"
CMIP7_CVS_REF="${CMIP7_CVS_REF:=zn-integration}"
# CMIP7_CVS_REF="${CMIP7_CVS_REF:=esgvoc_dev}"

# # Versioned esgvoc config
# # Use when we are using a versioned esgvoc release
# esgvoc_versioned=1
# ESGVOC_CMIP7_DB_VERSION="${ESGVOC_CMIP7_DB_VERSION:=dev-latest}"
# # ESGVOC_CMIP7_DB_VERSION="${ESGVOC_CMIP7_DB_VERSION:=latest}"

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

    if [[ "$(uname)" == "Darwin" ]]; then
        sed_platform_specific_args=(-i '')
    else
        sed_platform_specific_args=(-i)
    fi

    sed "${sed_platform_specific_args[@]}" -e 's#\(.*\)/github.com/.*/\(.*\)#\1/github.com/'"${ESGVOC_FORK}"'/\2#' "${requirements_file}"
    sed "${sed_platform_specific_args[@]}" -e 's#\(.*\)/esgf-vocab.git@.*#\1/esgf-vocab.git@'"${ESGVOC_REVISION}"'#' "${requirements_file}"

    pip install -r "${requirements_file}"

    if [[ $esgvoc_versioned -eq 1 ]]; then

        echo "Using versioned esgvoc"
        log "ESGVOC_CMIP7_DB_VERSION=$ESGVOC_CMIP7_DB_VERSION"
        esgvoc use "cmip7@${ESGVOC_CMIP7_DB_VERSION}"

    else

        echo "Using non-versioned esgvoc"
        log "UNIVERSE_CVS_FORK=$UNIVERSE_CVS_FORK"
        log "UNIVERSE_CVS_REF=$UNIVERSE_CVS_REF"
        log "CMIP7_CVS_FORK=$CMIP7_CVS_FORK"
        log "CMIP7_CVS_REF=$CMIP7_CVS_REF"

        esgvoc admin build \
            --project-repo "https://github.com/${CMIP7_CVS_FORK}/CMIP7-CVs" \
            --project-ref "${CMIP7_CVS_REF}" \
            --universe-repo "https://github.com/${UNIVERSE_CVS_FORK}/WCRP-universe" \
            --universe-ref "${UNIVERSE_CVS_REF}" \
            --project-id cmip7 \
            --cv-version dev \
            --universe-version dev \
            --output /tmp/cmip7.db

        esgvoc admin install cmip7 /tmp/cmip7.db --name local --activate

    fi

fi

log "generation_script=$generation_script"
log "out_file=$out_file"
log "out_path_split_view=$out_path_split_view"
python "${generation_script}" --out-path "${out_file}" --out-path-split-view "${out_path_split_view}" && log "Wrote output to ${out_file} and split view to ${out_path_split_view}"
