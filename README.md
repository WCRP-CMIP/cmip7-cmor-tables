# cmip7-cmor-tables

[![Recreate CMOR CVs JSON file](https://github.com/WCRP-CMIP/cmip7-cmor-tables/actions/workflows/recreate-cmor-cvs-json.yaml/badge.svg)](https://github.com/WCRP-CMIP/cmip7-cmor-tables/actions/workflows/recreate-cmor-cvs-json.yaml)

CMOR MIP tables for use with CMOR v3.13.1 and newer versions in preparation for CMIP7.

Note that versions of CMOR after v3.10 will be able to use these MIP tables, but minimum version 3.13 is required to correctly output the realization, initialization, physics and forcing indices.

To support overriding of long names, in the very small number of cases where this is required to match the Data Request v1.2.2.3, CMOR v3.13.2 is needed and the examples here have been updated to use it.

## CVs JSON file

The CVs JSON file is now hosted in the [tables-cvs directory](https://github.com/WCRP-CMIP/cmip7-cmor-tables/tree/main/tables-cvs). 
This file will be updated around 00Z each day via a github action using the esgvoc tools. 
Initially only two source_id entries exist for demonstration purposes, but these will be extended as the Essential Model Documentation is collected and processed. 
An update to modelling groups will be sent in the second half of February.

⚠️ **Note that there is no intention to generate a tag/release for every update to the CVs JSON file**.⚠️

A large number of changes  will be made to the CVs as new models, grids and eventually experiments are registered making this unwieldly.
To reference a particular version of the CVs JSON file we recommend using the commit hash (e.g. 58efe39) from [here](https://github.com/WCRP-CMIP/cmip7-cmor-tables/blob/main/tables-cvs/cmor-cvs.json) and the date.

## Changes relative to CMIP6

With the introduction of [branded variable names](https://wcrp-cmip.github.io/cmip7-guidance/CMIP7/branded_variables/) and an updated set of [global attributes](https://zenodo.org/records/17250297) the tables here look a little different to those for CMIP6. 

* Variables are arranged in MIP tables by realm and indexed by branded variable name.
* Frequency is no longer defined for a specific variable and any valid frequency can be set via the input JSON file (the same is true for region).

Notable changes to the input JSON file used by CMOR
* `drs_specs` should be set to the drs_specs version this will be `MIP-DRS7.0.0.0` initially, but will be updated as changes to the data definitions are produced, e.g. new version of the Data Request.
* `region` is required (usually `"glb"` for global variables, note the change in case as of Data Request v1.2.2.3) 
* `archive_id` is `"WCRP"`
* `frequency` must be specified and does not contain any suffixes as in CMIP6 (e.g. `6hrPt` and similar have been removed as has `1hrCM` used for the diurnal cycle diagnostics. The time sampling is now described in the [Branded Variable Name](https://wcrp-cmip.github.io/cmip7-guidance/CMIP7/branded_variables/).
* `*_index` fields are now strings and must have the appropriate prefix, e.g. `realization_index` should be `"r1"` rather than `1`
* `tracking_prefix` has been updated with the value required for CMIP7
* `long_name` and `cell_measures` both have separate files keyed by the CMIP7 compound names. Modelling groups are asked to use these files as shown in the example notebooks

## Changes relative to the Data Request

The tables and examples presented here are derived directly from [Data Request version v1.2.2.3](https://wcrp-cmip.org/cmip7-data-request-v1-2-2-3/) with the following changes;

* `long_name` and `modeling_realm` fields have been mostly "homogenised". Data Request variables sharing the same branded name also share the same `long_name` (16 Data Request variables in v1.2.2.3 are exceptions, all sea ice variables). 
* `comment` fields have been left blank as we have not yet "homogenised" this data.
* `cell_measures` are currently blank, with a separate JSON file containing them indexed by the CMIP7 Compound name from the Data Request -- the examples show how to re-introduce this metadata, and updated guidance will be added here.

## Known issues

* There are some branded variable names that appear in both atmos and landIce MIP tables. We are expecting to change this in the next version of the Data Request to avoid duplication.

## Examples

Each of these use the tables and the testing CVs JSON file

* [Simple CMOR demo notebook](cmor_demo.ipynb) ([python script equivalent](scripts/cmor_test.py))
    * Get the right environment either using conda with `cmor_environment.yml` or pixi using the `pixi.lock` file
* [Example of "re-cmorising" CMIP6 data](Simple_recmorise_cmip6-cmip7.ipynb)

Note in particular the lines used to add `cell_measures` metadata to variables.

## Testing

Testing of these tables has been limited, so please report problems / suggestions via the issues. 

## Construction notes

The [construction](scripts/construction.py) script uses the Data Request API and a set of reference files (adapted from CMIP6Plus) to construct the MIP tables and associated files.
