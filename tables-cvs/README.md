# CMOR CVs table

This directory contains the controlled vocabularies (CVs)
JSON file (aka table) required by CMOR.
It is stored in the file `cmor-cvs.json`.

This table is kept up to date via GitHub actions.
The table is checked for updates daily (if there are updates, a new pull request is made)
and the table can also be updated manually either locally
(by running the script `recreate-cmor-cvs-json.sh`)
or by triggering the relevant GitHub action manually.
