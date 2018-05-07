"""
import sys
sys.path.append(r'C:\Users\craig\PycharmProjects\file_manager')
sys.path.append(r'C:\Python27\Lib\site-packages\psycopg2-2.7.4-py2.7-win-amd64.egg')
from file_manager.fm_maya import run_maya
run_maya()
"""

import maya.cmds as cmds
from PySide2.QtWidgets import qApp

from file_manager import FileManagerApp

# Window title and object names
WINDOW_TITLE = 'FileManager'
WINDOW_OBJECT = 'fileManager'

DOCK_WITH_MAYA_UI = False
DOCK_WITH_NUKE_UI = False


def _maya_delete_ui():
    if cmds.window(WINDOW_OBJECT, q=True, exists=True):
        cmds.deleteUI(WINDOW_OBJECT)  # Delete window
    if cmds.dockControl('MayaWindow|' + WINDOW_TITLE, q=True, ex=True):
        cmds.deleteUI('MayaWindow|' + WINDOW_TITLE)  # Delete docked window


def _maya_main_window():
    for obj in qApp.topLevelWidgets():
        if obj.objectName() == 'MayaWindow':
            return obj
    raise RuntimeError('Could not find MayaWindow instance')


def run_maya():
    _maya_delete_ui()  # Delete any existing existing UI

    app = FileManagerApp(parent=_maya_main_window())
    app.setProperty("saveWindowPref", True)
    app.show()  # Show the UI
