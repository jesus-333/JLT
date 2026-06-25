"""

@author: Alberto Zancanaro (Jesus)
@organization: Luxembourg Centre for Systems Biomedicine (LCSB)
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

import os

from . import support

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class scrapper() :
    """
    Class to scrape a repository and convert the text chunk files to be used in a Rag
    """

    def __init__(self, path_repo : str, file_extension_filter : list = None, paths_to_ignore_list : list = None, chunking_function = None) :
        """
        Parameters
        ----------
        path_repo : str
            Path to the repository to be scraped
        file_extension_filter : list
            List of file extensions to be considered (e.g. ['.md', '.txt']). If None, all files are considered.
            Default is None.
        paths_to_ignore_list : list
            List of paths to ignore (e.g. ['.git', 'data']). If None, no paths are ignored.
            Note that also subfolders could be specified (e.g. ['folder1/subfolder1', 'folder2']).
            Default is None.
        chunking_function : function
            Function to be used to chunk the files. If None, no chunking is performed and the whole file is considered as a single chunk.
            Default is None.
        """
        
        # Chunking function
        self.chunking_function = chunking_function

        # Get the files list and create chunks
        self.update_files_list_and_create_chunks(path_repo, file_extension_filter, paths_to_ignore_list)

    def __getitem__(self, idx : int) :
        """
        Get the file at index idx in the files_list attribute.

        Parameters
        ----------
        idx : int
            Index of the file to be retrieved. Must be a valid index in the files_list.

        Returns
        -------
        file_path : str
            Path of the file at index idx in the files_list.
        """

        self.check_idx(idx)

        return self.get_file_content(idx)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # File handling functions

    def update_files_list(self, path_repo : str, file_extension_filter : list = None, paths_to_ignore_list : list = None) :
        """
        Update the attribute files_list. The original list of files is deleted and replaced with a list of files from path_repo.
        The files with extensions present in file_extension_filter will be ignored.
        The files in the path present in paths_to_ignore_list will be ignored.
        """
        # Get all files from the repository
        tmp_files_list = support.get_all_files_from_path(path_repo, file_extension_filter)
        
        # Attribute to store the list of files
        self.files_list = []
    
        # Remove files in the paths to ignore
        if paths_to_ignore_list is not None :
            for tmp_file in tmp_files_list :
                tmp_file_path = os.path.dirname(tmp_file)
        
                if not any(path_to_ignore in tmp_file_path for path_to_ignore in paths_to_ignore_list) :
                    self.files_list.append(tmp_file)
        else :
            self.files_list = tmp_files_list

    def update_files_list_and_create_chunks(self, path_repo : str, file_extension_filter : list = None, paths_to_ignore_list : list = None) :
        """
        Update the attribute files_list and create chunks from the files in the list.
        The original list of files is deleted and replaced with a list of files from path_repo.
        The files with extensions present in file_extension_filter will be ignored.
        The files in the path present in paths_to_ignore_list will be ignored.
        """

        self.update_files_list(path_repo, file_extension_filter, paths_to_ignore_list)
        self.create_chunk()

    def check_idx(self, idx : int) :
        """
        Check if the index idx is valid for the files_list attribute. If idx is not valid, raise an IndexError.
        I know that the function is "stupid", but sicne I use it multiple times, I prefer to have it as a compact function to call.

        Parameters
        ----------
        idx : int
            Index to be checked. Must be a valid index in the files_list.
        """

        if idx < 0 or idx >= len(self.files_list) :
            raise IndexError(f"Index {idx} is out of range for the files list with length {len(self.files_list)}.")

    def get_file_content(self, idx : int) -> str :
        """
        Read the file at index idx in the files_list attribute and return its content as a string.

        Parameters
        ----------
        idx : int
            Index of the file to be read. Must be a valid index in the files_list.

        Returns
        -------
        content : str
            Content of the file read.
        """

        self.check_idx(idx)
        
        file_path = self.files_list[idx]
        with open(file_path, 'r', encoding = 'utf-8') as file:
            file_content = file.read().strip()
            return file_content

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Chunking functions

    def create_chunk(self) :
        """
        Create chunks from the files in the files_list attribute using the chunking_function attribute, if specified.
        Otherwise, the whole contents of all files are merged into a single chunk.
        """

        self.chunks = []

        if self.chunking_function is not None :
            for idx in range(len(self.files_list)) :
                file_chunks = self.get_chunks_from_file(idx)
                self.chunks += file_chunks
        else :
            merged_content = ""
            for idx in range(len(self.files_list)) :
                file_content = self.get_file_content(idx)
                merged_content += file_content + "\n\n"
            self.chunks.append(merged_content)

    def get_chunks_from_file(self, idx : int) -> list :
        """
        Read the file at index idx in the files_list attribute and return a list of chunks created using the chunking_function attribute.

        Parameters
        ----------
        idx : int
            Index of the file to be read. Must be a valid index in the files_list.

        Returns
        -------
        file_chunks : list
            List of chunks created from the file content using the chunking_function.
            If chunking_function is None, return None.
        """

        self.check_idx(idx)

        file_content = self.get_file_content(idx)

        if self.chunking_function is not None :
            file_chunks = self.chunking_function(file_content)
            return file_chunks

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Print functions

    def print_file(self, idx : int, extended_output : bool = False) :
        """
        Print the content of the file at index idx in the files_list attribute.

        Parameters
        ----------
        idx : int
            Index of the file to be printed. Must be a valid index in the files_list.
        extended_output : bool
            If True, print also the file path before the content and add separators.
            Default is False.
        """

        if extended_output :
            self.check_idx(idx)

            file_path = self.files_list[idx]
            print("\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            print(f"File {idx}: {file_path}\n")
            print(self.get_file_content(idx))
            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")

        else :
            print(self.get_file_content(idx))

    def print_all_files(self, extended_output : bool = False) :
        """
        Print the content of all files in the files_list attribute.

        Parameters
        ----------
        extended_output : bool
            If True, print also the file path before the content and add separators.
            Default is False.
        """
        for idx, file_path in enumerate(self.files_list) : self.print_file(idx, extended_output)


