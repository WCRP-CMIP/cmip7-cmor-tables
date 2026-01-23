import cmor
import numpy 
import json
import os
import shutil
import sys
from copy import deepcopy as copy

DATASET_INFO = {
    "_AXIS_ENTRY_FILE": "tables/CMIP7_coordinate.json",
    "_FORMULA_VAR_FILE": "tables/CMIP7_formula_terms.json",
    "_cmip7_option": 1,
    "_controlled_vocabulary_file": "test/cmor-cvs.json",  # SEPARATE TO MIP TABLES FOR TESTING ONLY
    "activity_id": "CMIP",
    "branch_method": "standard",
    "branch_time_in_child": 30.0,
    "branch_time_in_parent": 10800.0,
    "calendar": "360_day",
    "cv_version": "7.0.0.0",
    "drs_specs": "MIP-DRS7",
    "data_specs_version": "MIP-DS7.0.0.0",
    "experiment_id": "1pctCO2",
    "forcing_index": "f3",
    "grid": "N96",
    "grid_label": "g99",
    "initialization_index": "i1",
    "institution_id": "CCCma",
    "license_id": "CC-BY-4-0",
    "nominal_resolution": "100 km",
    "outpath": ".",
    "parent_mip_era": "CMIP7",
    "parent_time_units": "days since 1850-01-01",
    "parent_activity_id": "CMIP",
    "parent_source_id": "CanESM6-MR",
    "parent_experiment_id": "piControl",
    "parent_variant_label": "r1i1p1f3",
    "physics_index": "p1",
    "realization_index": "r9",
    "source_id": "CanESM6-MR",
    "tracking_prefix": "hdl:21.14107",
    "host_collection": "CMIP7",
    "frequency": "mon",
    "region": "glb",
    "archive_id": "WCRP",
    "mip_era": "CMIP7",
}

def main():
    if len(sys.argv) < 2:
        print('Please specify a temporary location to write to as the argument to this script. Exiting.')
        sys.exit(1)
        
    tempdir = sys.argv[1]
    if not os.path.exists(tempdir):
        os.mkdir(tempdir)
    
    dataset_info = copy(DATASET_INFO)
    dataset_info['outpath'] = tempdir
    input_json = os.path.join(tempdir,'input.json')
    with open(input_json, 'w') as fh:
        json.dump(dataset_info, fh, indent=2)

    cmor.setup(inpath="tables", netcdf_file_action=cmor.CMOR_REPLACE)

    cmor.dataset_json(input_json)

    tos = numpy.array([27.] * 24)
    tos.shape = (2, 3, 4)
    lat = numpy.array([10., 20., 30.])
    lat_bnds = numpy.array([5., 15., 25., 35.])
    lon = numpy.array([0., 90., 180., 270.])
    lon_bnds = numpy.array([-45., 45.,
                            135.,
                            225.,
                            315.
                            ])
    time = numpy.array([15.0, 45.0])
    time_bnds = numpy.array([0.0, 30.0, 60.0])
    
    
    realm = "ocean"
    cmor.load_table(f"CMIP7_{realm}.json")
    cmorlat = cmor.axis("latitude",
                        coord_vals=lat,
                        cell_bounds=lat_bnds,
                        units="degrees_north")
    cmorlon = cmor.axis("longitude",
                        coord_vals=lon,
                        cell_bounds=lon_bnds,
                        units="degrees_east")
    cmortime = cmor.axis("time",
                        coord_vals=time,
                        cell_bounds=time_bnds,
                        units="days since 2018")
    axes = [cmortime, cmorlat, cmorlon]
    variable = "tos_tavg-u-hxy-sea"
    cmortos = cmor.variable(variable, "degC", axes)

    region = DATASET_INFO['region']
    frequency = DATASET_INFO['frequency']
    cmip7_compound_name = ".".join([realm] + variable.split("_") + [frequency, region])
    print('cmip7 compound name:', cmip7_compound_name)
    with open('tables/CMIP7_cell_measures.json') as fh:
        cell_measures = json.load(fh)

    # Check that cell_measures are valid ( option flags need to be manually replaced )
    variable_cell_measures = cell_measures['cell_measures'][cmip7_compound_name]

    cmor.set_variable_attribute(cmortos, "cell_measures", "c", variable_cell_measures)

    with open('tables/CMIP7_long_name_overrides.json') as fh:
        long_name_overrides = json.load(fh)

    if cmip7_compound_name in long_name_overrides['long_name_overrides']:
        new_long_name = long_name_overrides['long_name_overrides'][cmip7_compound_name]
        cmor.set_variable_attribute(cmortos, "long_name", "c", new_long_name)

    cmor.write(cmortos, tos)
    filename = cmor.close(cmortos, file_name=True)
    print(filename)
    for root, directories, files in os.walk(tempdir):
        for f in files:
            if f.endswith('.nc'):
                print(os.path.join(root, f))
                os.system(f'ncdump -h {root}/{f}')

    input('Hit enter to delete all data created')
    
    try:
        shutil.rmtree(tempdir)
    except OSError:
        pass


if __name__ == '__main__':
    main()
