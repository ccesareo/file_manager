"""
Example template that imports images that are already suitable for thumbnails
"""

import os


def is_valid(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    return ext in ('.jpg', '.png')


def get_thumbnail(file_path):
    return file_path
