import os


def is_valid(file_path):
    """
    Determine if the given file_path is valid for processing through this template.

    Args:
        file_path (str): Path to the file being proessed

    Returns:
        bool: True if the path is valid for processing
    """
    return True


def get_asset_name(file_path):
    """
    Determine the name of the asset given the file_path

    Args:
        file_path (str): Path to the file being proessed

    Returns:
        str: Name of the asset to be assigned
    """
    _fname = os.path.basename(file_path)
    return os.path.splitext(_fname)[0]


def get_tags(file_path):
    """
    Determine a list of tags to auto assign to the given file_path

    Args:
        file_path (str): Path to the file being proessed

    Returns:
        list of str: List of tags to assign (Returning None will skip)
    """
    return ['new']


def get_thumbnail(file_path):
    """
    Determine the thumbnail to be used for the given file_path

    Args:
        file_path (str): Path to the file being proessed

    Returns:
        str: Path to a thumbnail image to be copied into the thumbnail repo area (Returning None will skip)
    """
    return
