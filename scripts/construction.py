import argparse
from collections import defaultdict
from copy import deepcopy as copy
from dataclasses import dataclass, asdict
from typing import Optional
import datetime
import hashlib
import json
import os

import data_request_api.content.dreq_content as dc
import data_request_api.query.dreq_query as dq

DR_TO_CMOR_COORDINATE_KEY_MAPPING = {
    'axis': 'axis_flag',
    'bounds_values': 'bounds_scalar', 
    'climatology': 'climatology_flag',
    'formula': None,  # does not exist
    'generic_level_name': None,  # does not exist
    'long_name': 'title',
    'must_have_bounds': 'bounds_flag',
    'out_name': 'output_name',
    'positive': 'positive_direction',
    'requested': 'requested_values',
    'requested_bounds': 'requested_bounds',
    'standard_name': 'cf_standard_name',
    'stored_direction': 'stored_direction',
    'tolerance': 'tolerance',
    'type': 'type',
    'units': 'units',
    'valid_max': 'maximum_valid_value',
    'valid_min': 'minimum_valid_value',
    'value': 'value_scalar_or_string',
    'z_bounds_factors': None,
    'z_factors': None,
}
GENERIC_LEVELS = {
    'atmos': "alevel alevhalf", 
    'land': "", 
    'ocean': "olevel olevhalf", 
    'aerosol': "alevel alevhalf", 
    'atmosChem': "alevel alevhalf",
    'landIce': "", 
    'ocnBgchem': "olevel olevhalf", 
    'seaIce': "olevel olevhalf"
}
TIMESTAMP = datetime.datetime.today().strftime("%Y-%m-%d %T")
TABLE_TEMPLATE = {
    "Header": {
        "Conventions": "CF-1.12 CMIP-7.0",
        "checksum": "to be calculated",
        "cmor_version": "3.13",
        "generic_levels": "",
        "int_missing_value": "-999",
        "missing_value": "1e20",
        "ok_max_mean_abs": "",
        "ok_min_mean_abs": "",
        "positive": "",
        "product": "model-output",
        "realm": "",
        "table_date": TIMESTAMP,
        "table_id": "",
        "type": "real",
        "valid_max": "",
        "valid_min": ""
    }
}

@dataclass
class DataRequestVariable:
    """
    Container Class for a data request variable
    """
    branded_variable_name: str
    branding_label: str
    cell_measures: str
    cell_methods: str
    cmip6_compound_name: str
    cmip6_table: str
    cmip7_compound_name: str
    comment: str
    dimensions: str
    frequency: str
    long_name: str
    modeling_realm: str
    out_name: str
    physical_parameter_name: str
    positive: str
    processing_note: str
    region: str
    spatial_shape: str
    standard_name: str
    temporal_shape: str
    type: str
    uid: str
    units: str
    variableRootDD: str
    flag_values: Optional[str] = None
    flag_meanings: Optional[str] = None

    def to_cmorvar(self):
        """
        Construct a CMOR variable from the data request info
        """
        # pick up cmor keys from data request information of the same name
        cmor_keys = CMORvar.__dataclass_fields__.keys()
        cmor_args = {k:v for k,v in vars(self).items() if k in cmor_keys}
        #override dimensions type
        cmor_args['dimensions'] = self.dimensions.split()
        return CMORvar(**cmor_args)


@dataclass
class CMORvar:
    """
    Container class for CMOR variable
    """
    cell_measures: str
    cell_methods: str
    comment: str
    out_name: str
    positive : str
    units: str
    long_name: str
    standard_name: str
    branded_variable_name: str
    dimensions: list
    modeling_realm: str
    long_name: str
    flag_values: str
    flag_meanings: str

    def table_name(self):
        """
        return the table name to be used for this variable
        """
        return self.modeling_realm.split(" ")[0]
    
    def json_for_table(self):
        """
        Return dictionary needed for MIP table entry
        """
        cmordict = asdict(self)
        del cmordict['branded_variable_name']
        # flags only used for one variable
        for field in ['flag_values', 'flag_meanings']:
            if not cmordict[field]:
                del cmordict[field]

        return cmordict


def set_checksum(dictionary, overwrite=True):
    """
    Calculate the checksum for the ``dictionary``, then add the
    value to ``dictionary`` under the ``checksum`` key. ``dictionary``
    is modified in place.
    Parameters
    ----------
    dictionary: dict
        The dictionary to set the checksum to.
    overwrite: bool
        Overwrite the existing checksum (default True).
    Raises
    ------
    RuntimeError
        If the ``checksum`` key already exists and ``overwrite`` is
        False.
    """
    if 'checksum' in dictionary['Header']:
        if not overwrite:
            raise RuntimeError('Checksum already exists.')
        del dictionary['Header']['checksum']
    checksum = _checksum(dictionary)
    dictionary['Header']['checksum'] = checksum


def validate_checksum(dictionary):
    """
    Validate the checksum in the ``dictionary``.
    Parameters
    ----------
    dictionary: dict
        The dictionary containing the ``checksum`` to validate.
    Raises
    ------
    KeyError
        If the ``checksum`` key does not exist.
    RuntimeError
        If the ``checksum`` value is invalid.
    """
    if 'checksum' not in dictionary['Header']:
        raise KeyError('No checksum to validate')
    dictionary_copy = copy.deepcopy(dictionary)
    written_checksum = dictionary['Header']['checksum']
    del dictionary_copy['Header']['checksum']
    checksum = _checksum(dictionary_copy)
    if written_checksum != checksum:
        msg = ('Expected checksum   "{}"\n'
               'Calculated checksum "{}"').format(written_checksum, checksum)
        raise RuntimeError(msg)


def _checksum(obj):
    obj_str = json.dumps(obj, sort_keys=True)
    checksum_hex = hashlib.md5(obj_str.encode('utf8')).hexdigest()
    return 'md5: {}'.format(checksum_hex)


def write_table(tables, destination):
    """
    Construct tables as dictionary objects and write them as 
    """
    for realm in tables:
        # copy template and update relevant fields
        template = copy(TABLE_TEMPLATE)
        template['Header'].update(
            {
                "generic_levels": GENERIC_LEVELS[realm],
                "realm": realm,
                "table_id": realm,
            }
        )

        # construct variable_entry section
        template["variable_entry"] = {}
        for bvname, cmorvar in tables[realm].items():
            template['variable_entry'][bvname] = cmorvar.json_for_table()
        
        # checksum
        set_checksum(template)

        # write out
        with open(os.path.join(destination, 'CMIP7_{}.json'.format(realm)), 'w') as fh:
            json.dump(template, fh, indent=4, sort_keys=True)
    

def dr_coord_to_cmor_dict(coord):
    """
    Construct a coordinate entry for the CMOR coordinates.json file from a 
    data request coordinate object
    """
    name = coord.name
    cmor_coord = {}    
    
    for cmor_key, dr_key in DR_TO_CMOR_COORDINATE_KEY_MAPPING.items():
        if dr_key is None:
            value = ''
        else:
            value = getattr(coord, dr_key, '')
        if isinstance(value, str):
            value = value.replace(',', '')
        cmor_coord[cmor_key] = value
    
    # deal with yes/no fields
    if cmor_coord['must_have_bounds']:
        cmor_coord['must_have_bounds'] = "yes"
    else:
        cmor_coord['must_have_bounds'] = "no"
    # deal with lists
    if cmor_coord['requested']:
        try:
            cmor_coord['requested'] = ['{:.1f}'.format(float(i)) for i in cmor_coord['requested'].split()]
        except ValueError:
            cmor_coord['requested'] = ''
    if cmor_coord['requested_bounds']:
        cmor_coord['requested_bounds'] = ['{:.1f}'.format(float(i)) for i in cmor_coord['requested_bounds'].split()]

    # convert numbers to strings (even if they are zero)
    for i in ['tolerance', 'valid_max', 'valid_min']:
        if cmor_coord[i] != "":
            cmor_coord[i] = str(cmor_coord[i])

    return name, cmor_coord    


def construct_coordinates(dr_coords, reference_coordinate_file):
    """
    Construct coordinate file for CMOR based on data request coordinate info
    and a reference coordinate file
    """
    coordinates = {'axis_entry': {}}

    for dr_coord in dr_coords.records.values():
        name, cmor_coord = dr_coord_to_cmor_dict(dr_coord)
        coordinates['axis_entry'][name] = cmor_coord

    with open(reference_coordinate_file) as fh:
        reference = json.load(fh)

    # coordinates that are built based on formula terms
    keys_to_drop_from_dr = ['alevel', 'alevhalf', 'olevel', 'olevhalf']
    # keys that should be removed (remove from data request)?
    keys_that_cause_cmor_failure = ['xant','yant','xgre','ygre']

    # remove unwanted keys
    for k in keys_to_drop_from_dr + keys_that_cause_cmor_failure:
        if k in coordinates['axis_entry']:
            del coordinates['axis_entry'][k]

    # import entries from old CMOR tables
    keys_to_import = [
        'alternate_hybrid_sigma',
        'alternate_hybrid_sigma_half',
        'depth_coord',
        'depth_coord_half',
        'hybrid_height',
        'hybrid_height_half',
        'ocean_sigma',
        'ocean_sigma_half',
        'ocean_sigma_z',
        'ocean_sigma_z_half',
        'standard_hybrid_sigma',
        'standard_hybrid_sigma_half',
        'standard_sigma',
        'standard_sigma_half']

    for k in keys_to_import:
        coordinates['axis_entry'][k] = reference['axis_entry'][k]

    return coordinates


def check_field(field_name, field_dict):
    """
    Check a field for conflicts between values with the same table, branded variable name combination
    """
    for table, bv_dict in field_dict.items():
        bv_names = list(bv_dict.keys())
        for bv_name in bv_names:
            bv_fieldname = set(list(field_dict[table][bv_name].values()))
            if len(bv_fieldname) == 1:
                del field_dict[table][bv_name]

    if sum([len(i) for i in field_dict.values()]) > 0:
        print(f"Issues found with {field_name} conflicts. writing details to {field_name}.json")
        with open(f'{field_name}.json', 'w') as fh:
            json.dump(field_dict, fh, indent=4)


def load_overrides(reference_dir, dr_version, suffix):
    """
    Read in a dictionary of overrides if it exists for a particular version
    """
    overrides = {}
    overrides_file = os.path.join(reference_dir, f"dr_{dr_version}_{suffix}.json")

    if os.path.exists(overrides_file):
        with open(overrides_file) as fh:
            overrides = json.load(fh)
    
    return overrides


def collect_cell_measures(output_dir, all_var_info):
    """
    Write out cell measures info to a separate file and replace "::OPT" and "::MODEL" with 
    "--OPT" and "--MODEL"
    """
    cell_measures_info = {'cell_measures':{}}
    for variable in all_var_info.values():
        cell_measures_info['cell_measures'][variable.cmip7_compound_name] = variable.cell_measures
    
    write_ancil(
        cell_measures_info, 
        os.path.join(output_dir, "CMIP7_cell_measures.json"),
        'cell_measures')


def construct_all_ancil_files(output_dir, reference_dir, coords):
    """
    Construct the ancillary files (coordinates, formula_terms, grids)
    """
    coordinate_file = os.path.join(reference_dir,'MIP_coordinate.json')
    coordinates = construct_coordinates(coords, coordinate_file)
    coordinates_file = os.path.join(output_dir, 'CMIP7_coordinate.json')

    write_ancil(coordinates, coordinates_file,'coordinates')
    
    # formula terms
    with open(os.path.join(reference_dir, 'MIP_formula_terms.json')) as fh:
        formula_terms = json.load(fh)
    
    write_ancil(formula_terms,
                    os.path.join(output_dir, 'CMIP7_formula_terms.json'),
                    'forumula_terms')
    
    # grids    
    with open(os.path.join(reference_dir, 'MIP_grids.json')) as fh:
        grids = json.load(fh)
    
    write_ancil(grids,
                os.path.join(output_dir, 'CMIP7_grids.json'),
                'grids')
    
    # cell measures

    # long_name overrides    
    with open(os.path.join(reference_dir, 'MIP_long_name_overrides.json')) as fh:
        grids = json.load(fh)
    
    write_ancil(grids,
                os.path.join(output_dir, 'CMIP7_long_name_overrides.json'),
                'long_name_overrides')
    

def write_ancil(data, output_file, table_id):
    """
    write an ancil file
    """
    data.update(TABLE_TEMPLATE)
    data['Header']['table_id'] = table_id
    set_checksum(data)
    with open( output_file, 'w') as fh:
        json.dump(data, fh, indent=4, sort_keys=True)


def parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description="Generate CMIP7 tables for CMOR from the data request")
    parser.add_argument('data_request_version', type=str, help='Data Request version, e.g. v1.2.2.1')
    parser.add_argument('output_dir', type=str, help='Directory to output to')
    default_reference_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'reference'))
    parser.add_argument('--reference_file_path', default=default_reference_dir, help=f'Location of reference files')

    return parser.parse_args()


def main():
    """
    Main routine
    """

    args = parse_args()
    dr_version = args.data_request_version
    output_dir = args.output_dir
    reference_dir = args.reference_file_path
    
    if not os.path.exists(output_dir):
        print(f'Directory "{output_dir}" not found. creating')
        os.mkdir(output_dir)

    print(f'Loading Data Request version "{dr_version}"')
    # load data request and construct cmor variable list
    content = dc.load(dr_version)#, offline=True)
    all_var_info = dq.get_variables_metadata(content, dr_version)
    # convert to dataclass
    for k, v in all_var_info.items():
        drv = DataRequestVariable(**v)
        all_var_info[k] = drv

    #collect cell measures information and write to CMIP7_cell_measures.json keyed by CMIP7 compound_name
    collect_cell_measures(output_dir, all_var_info)
    
    # apply agreed overrides to the data request informatoin
    print('WARNING: all comments have been set to blank strings while we homogenise the contents')
    print('WARNING: all cell_measures have been set to blank strings. Users will need to explicitly set cell_measures')
    for variable in all_var_info.values():
        variable.comment = ""
        variable.cell_measures = ""  #CELL MEASURES OVERRIDE

    # dictionary to hold tables
    tables = defaultdict(dict)
    # for checking consistency
    longname = defaultdict(lambda:defaultdict(dict))
    realm = defaultdict(lambda:defaultdict(dict))
    measures = defaultdict(lambda:defaultdict(dict))
    # dictionaries to hold  overrides
    long_name_overrides = load_overrides(reference_dir, dr_version, 'long_name_overrides')
    realm_overrides = load_overrides(reference_dir, dr_version, 'realm_overrides')
    
    for variable in all_var_info.values():
        # apply overrides to data request info
        if variable.cmip7_compound_name in long_name_overrides:
            variable.long_name = long_name_overrides[variable.cmip7_compound_name]
        if variable.cmip7_compound_name in realm_overrides:
            variable.modeling_realm = realm_overrides[variable.cmip7_compound_name]

        # convert to info in CMOR variable
        cmorvar = variable.to_cmorvar()
        table_name = cmorvar.table_name()
        bv_name = cmorvar.branded_variable_name
        tables[table_name][bv_name] = cmorvar
        # build dictionaries for checking consistency
        longname[table_name][bv_name][variable.cmip7_compound_name] = cmorvar.long_name
        realm[table_name][bv_name][variable.cmip7_compound_name] = cmorvar.modeling_realm
        # for the following to be useful comment the line #CELL MEASURES OVERRIDE above
        measures[table_name][bv_name][variable.cmip7_compound_name] = cmorvar.cell_measures

    # check consistency
    check_field('long_name', longname)
    check_field('modeling_realm', realm)
    check_field('cell_measures', measures)

    #write out tables
    write_table(tables, output_dir)

    # write out ancillary files
    construct_all_ancil_files(output_dir, reference_dir, content['Data Request']['Coordinates and Dimensions'])


if __name__ == '__main__':
    main()