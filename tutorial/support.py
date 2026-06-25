"""
Support function

@author: Alberto Zancanaro (Jesus)
@organization: Luxembourg Centre for Systems Biomedicine (LCSB)
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

import os

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def get_all_files_from_path(path_to_explore : str, filetype_filter_list : list = None) :
    """
    Given a path to explore, return a list with all files in the folder and subfolders
    If the argument filetype_filter  is passed, only the files with that specified extension are returned
    """

    file_path_list = []
    for path, subdirs, files in os.walk(path_to_explore):
        for name in files:
            file_path = os.path.join(path, name)
            
            if filetype_filter_list is not None :
                _, file_extension = os.path.splitext(file_path)
                if file_extension in filetype_filter_list : file_path_list.append(file_path)
            else :
                file_path_list.append(file_path)

    return file_path_list



