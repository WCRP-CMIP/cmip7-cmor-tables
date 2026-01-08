# cmip7-cmor-tables

CMOR MIP tables for use with CMOR v3.13.1 in preparation for CMIP7.

Note that versions of CMOR after v3.10 will be able to use these MIP tables, but minimum version 3.13 is required to correctly output the realization, initialization, physics and forcing indices.

## Changes relative to CMIP6

With the introduction of [branded variable names](https://wcrp-cmip.github.io/cmip7-guidance/CMIP7/branded_variables/) and an updated set of [global attributes](https://zenodo.org/records/17250297) the tables here look a little different to those for CMIP6. 

* Variables are arranged in MIP tables by realm and indexed by branded variable name.
* Frequency is no longer defined for a specific variable and any valid frequency can be set via the input JSON file (the same is true for region).

Notable changes to the input JSON file used by CMOR
* `drs_specs` should be set to `"MIP-DRS7"`
* `region` is required (usually `"GLB"` for global variables)
* `archive_id` is `"WCRP"`
* `frequency` must be specified
* `*_index` fields are now strings and must have the appropriate prefix, e.g. `realization_index` should be `"r1"` rather than `1`
* `tracking_prefix` has been updated with the value required for CMIP7

The CV json files in this repository are for **TESTING** only. In the near future we are planning for the `CMIP7_CV.json` file to be constructed and supplied via the [CMIP7-CVs](https://github.com/WCRP-CMIP/CMIP7-CVs) repository. Updates will be posted here when progress has been made

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
