"""
Example template that imports images that are already suitable for thumbnails
"""

import os
import subprocess
import tempfile


def is_valid(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    return ext in ('.fbx',)


def get_thumbnail(file_path):
    print 'processing', file_path
    tmp = tempfile.gettempdir()
    dir_path = os.path.dirname(__file__)
    fbx_prev = os.path.join(dir_path, 'maya', 'fbx_preview.py')
    gif_path = os.path.join(tmp, 'output.gif')

    _args = [
        r'C:\Program Files\Autodesk\Maya2018\bin\mayapy.exe',
        fbx_prev,
        file_path,
        gif_path,
    ]
    p = subprocess.Popen(_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        p.stdout.readline()
        if p.poll() is not None:
            break
    return gif_path
