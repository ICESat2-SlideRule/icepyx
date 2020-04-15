import requests
from xml.etree import ElementTree as ET

#ICESat-2 specific reference functions
#options to get customization options for ICESat-2 data (though could be used generally)

def _validate_dataset(dataset):
    """
    Confirm a valid ICESat-2 dataset was specified
    """
    if isinstance(dataset, str):
        dataset = str.upper(dataset)
        assert dataset in ['ATL01','ATL02', 'ATL03', 'ATL04','ATL06', 'ATL07', 'ATL08', 'ATL09', 'ATL10', \
                           'ATL12', 'ATL13'],\
        "Please enter a valid dataset"
    else:
        raise TypeError("Please enter a dataset string")
    return dataset
#DevGoal: See if there's a way to dynamically get this list so it's automatically updated
    
#DevGoal: populate this with default variable lists for all of the datasets!
#DevGoal: add a test for this function (to make sure it returns the right list, but also to deal with dataset not being in the list, though it should since it was checked as valid earlier...)
def _default_varlists(dataset):
    """
    Return a list of default variables to select and send to the NSIDC subsetter.
    """
    common_list = ['delta_time','latitude','longitude']
    
    if dataset == 'ATL09':
        return common_list + ['bsnow_h','bsnow_dens','bsnow_con','bsnow_psc','bsnow_od',
                    'cloud_flag_asr','cloud_fold_flag','cloud_flag_atm',
                    'column_od_asr','column_od_asr_qf',
                    'layer_attr','layer_bot','layer_top','layer_flag','layer_dens','layer_ib',
                    'msw_flag','prof_dist_x','prof_dist_y','apparent_surf_reflec']
    
    if dataset == 'ATL07':
        return common_list + ['seg_dist_x',
                                'height_segment_height','height_segment_length_seg','height_segment_ssh_flag',
                                'height_segment_type', 'height_segment_quality', 'height_segment_confidence' ]
    
    if dataset == 'ATL10':
        return common_list + ['seg_dist_x','lead_height','lead_length',
                                'beam_fb_height', 'beam_fb_length', 'beam_fb_confidence', 'beam_fb_quality_flag',
                                'height_segment_height','height_segment_length_seg','height_segment_ssh_flag',
                                'height_segment_type', 'height_segment_confidence']

#DevGoal: add a test to compare the generated list with an existing [checked] one (right now this is done explicitly for keywords, but not for values)?
#DevGoal: use a mock of this ping to test later functions, such as displaying options and widgets, etc.
def _get_custom_options(session, dataset, version):
    """
    Get lists of what customization options are available for the dataset from NSIDC.
    """
    cust_options={}
    
    if session is None:
        raise ValueError("Don't forget to log in to Earthdata using is2_data.earthdata_login(uid, email)")

    capability_url = f'https://n5eil02u.ecs.nsidc.org/egi/capabilities/{self.dataset}.{self._version}.xml'
    response = session.get(capability_url)
    root = ET.fromstring(response.content)

    # collect lists with each service option
    subagent = [subset_agent.attrib for subset_agent in root.iter('SubsetAgent')]
    cust_options.update({'options':subagent})

    # reformatting
    formats = [Format.attrib for Format in root.iter('Format')]
    format_vals = [formats[i]['value'] for i in range(len(formats))]
    format_vals.remove('')
    cust_options.update({'fileformats':format_vals})

    # reprojection only applicable on ICESat-2 L3B products, yet to be available.

    # reformatting options that support reprojection
    normalproj = [Projections.attrib for Projections in root.iter('Projections')]
    normalproj_vals = []
    normalproj_vals.append(normalproj[0]['normalProj'])
    format_proj = normalproj_vals[0].split(',')
    format_proj.remove('')
    format_proj.append('No reformatting')
    cust_options.update({'formatreproj':format_proj})

    #reprojection options
    projections = [Projection.attrib for Projection in root.iter('Projection')]
    proj_vals = []
    for i in range(len(projections)):
        if (projections[i]['value']) != 'NO_CHANGE' :
            proj_vals.append(projections[i]['value'])
    cust_options.update({'reprojectionONLY':proj_vals})

    # reformatting options that do not support reprojection
    no_proj = [i for i in format_vals if i not in format_proj]
    cust_options.update({'noproj':no_proj})

    # variable subsetting
    vars_raw = []        
    def get_varlist(elem):
        childlist = list(elem)
        if len(childlist)==0 and elem.tag=='SubsetVariable': 
            vars_raw.append(elem.attrib['value'])
        for child in childlist:
            get_varlist(child)
    get_varlist(root)
    vars_vals = [v.replace(':', '/') if v.startswith('/') == False else v.replace('/:','')  for v in vars_raw]
    cust_options.update({'variables':vars_vals})

    return cust_options
