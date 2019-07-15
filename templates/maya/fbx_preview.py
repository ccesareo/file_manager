import glob
import hashlib
import os
import subprocess
import sys
import tempfile

# Initialize
import maya.standalone

try:
    maya.standalone.initialize()
except RuntimeError:
    pass

import maya.cmds as cmds

cmds.loadPlugin("fbxmaya")

import maya.cmds as mc


def convert_skeleton():
    group_name = mc.group(empty=True, name="PrimitiveSkeleton")

    parents = [j for j in mc.ls(type='joint') if not mc.listRelatives(j, p=True, type='joint')]
    for joint in parents:
        convert_joint(joint, group_name)


def convert_joint(curr_joint, group_name, root_jnt=True):
    scale_size = mc.jointDisplayScale(q=True) * 1.0

    _children = mc.listRelatives(curr_joint, c=True)
    if _children is not None:
        for node in _children:
            if mc.nodeType(node) == 'joint':
                convert_joint(node, group_name, root_jnt=False)

    parent = mc.listRelatives(curr_joint, p=True)
    if parent is None or root_jnt:
        return

    _name_ball = curr_joint + group_name + "_ball"
    new_ball = mc.sphere(n=_name_ball)

    _name_cone = curr_joint + group_name + "_joint"
    new_cone = mc.cone(p=(0, 0, 0), ax=(1, 0, 0), ssw=0, esw=360, r=0.5,
                       hr=4, d=1, ut=0, tol=0.01, s=8, nsp=4, ch=1,
                       n=_name_cone)
    mc.move(-1, 0, 0,
            _name_cone + ".scalePivot",
            _name_cone + ".rotatePivot",
            r=True)

    mc.parent(new_cone, group_name)
    mc.parent(new_ball, group_name)
    xform1 = mc.xform(curr_joint, q=True, ws=True, t=True)
    xform2 = mc.xform(parent[0], q=True, ws=True, t=True)
    dist = 0.0
    for i in range(len(xform1)):
        dist += (xform1[i] - xform2[i]) * (xform1[i] - xform2[i])
    dist = (dist ** 0.5) / 2.0
    mc.scale(scale_size, scale_size, scale_size, new_ball, r=True)
    bbox = mc.exactWorldBoundingBox(new_ball)
    bbox_size = ((((bbox[3] - bbox[0]) ** 2 +
                   (bbox[4] - bbox[1]) ** 2 +
                   (bbox[5] - bbox[2]) ** 2) ** 0.5) / 4.0) * 2.0
    mc.scale(dist, bbox_size, bbox_size, new_cone, r=True)
    mc.pointConstraint(parent[0], new_cone, weight=1)
    mc.pointConstraint(parent[0], new_ball, weight=1)
    mc.aimConstraint(curr_joint, new_cone, aim=(1, 0, 0), u=(0, 1, 0), wu=(0, 1, 0), weight=1)
    create_node(group_name, new_ball[0], 'ball')
    create_node(group_name, new_cone[0], 'edge')


def _create_ball(joint, group, size):
    name = joint + group + '_ball'  # Use for referencing, leading pipe when creating sphere
    assert name != 'Bip01FBXASC032HeadNubPrimitiveSkeleton_ball'
    _end_ball = mc.sphere(n=name)
    mc.parent(_end_ball, group)
    mc.scale(size, size, size, name, r=True)
    mc.pointConstraint(joint, name, weight=1)
    create_node(group, name, 'ball')


def create_node(group_name, obj_name, obj_type):
    if obj_type == 'ball':
        mult_name = obj_name + group_name + "_ballMultiply"
        mc.createNode('multiplyDivide', n=mult_name)
        mc.setAttr(mult_name + ".input1X", 1)
        mc.setAttr(mult_name + ".input2X", mc.getAttr(obj_name + '.scaleX'))
        mc.connectAttr(mult_name + '.outputX', obj_name + '.scaleX')
        mc.connectAttr(mult_name + '.outputX', obj_name + '.scaleY')
        mc.connectAttr(mult_name + '.outputX', obj_name + '.scaleZ')
    elif obj_type == 'edge':
        mult_name = obj_name + group_name + "_edgeMultiply"
        cone_shape_node = mc.listConnections(obj_name + 'Shape', s=True, d=False)
        mc.createNode('multiplyDivide', n=mult_name)
        mc.setAttr(mult_name + ".input1X", 1)
        mc.setAttr(mult_name + ".input2X", mc.getAttr(obj_name + '.scaleY'))
        mc.setAttr(mult_name + ".input1Z", 8)
        mc.setAttr(mult_name + ".input2Z", 1)
        mc.connectAttr(mult_name + '.outputX', obj_name + '.scaleY')
        mc.connectAttr(mult_name + '.outputX', obj_name + '.scaleZ')
        mc.connectAttr(mult_name + '.outputZ', cone_shape_node[0] + '.sections')


def main(input_name, output_name):
    output_dir = os.path.dirname(output_name)
    output_prefix = os.path.basename(output_name).rsplit('.', 1)[0]

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # File path setup
    pb_name = hashlib.sha1(input_name).hexdigest()
    tmp_path = os.path.join(tempfile.gettempdir(), pb_name)
    if not os.path.isdir(tmp_path):
        os.makedirs(tmp_path)

    # Import File
    cmds.file(input_name, i=True, importTimeRange='override')
    convert_skeleton()

    # Setup Camera
    cam_name, cam_shape = cmds.camera()
    cmds.setAttr(cam_name + '.translateX', 90)
    cmds.setAttr(cam_name + '.translateY', 40)
    cmds.setAttr(cam_name + '.translateZ', 140)
    cmds.setAttr(cam_name + '.rotateX', 0)
    cmds.setAttr(cam_name + '.rotateY', 32)
    cmds.setAttr(cam_name + '.rotateZ', 0)
    cmds.setAttr(cam_shape + '.backgroundColor', 0, 0, 0, type='double3')
    cmds.setAttr(cam_shape + '.renderable', True)
    cmds.setAttr(cam_shape + '.mask', 0)

    # Generate preview
    cmds.workspace(fileRule=['images', output_dir])
    cmds.setAttr('defaultRenderGlobals.currentRenderer', 'mayaSoftware', type='string')
    cmds.setAttr('defaultRenderGlobals.outFormatControl', 0)
    cmds.setAttr('defaultRenderGlobals.animation', 1)
    cmds.setAttr('defaultRenderGlobals.putFrameBeforeExt', 1)
    cmds.setAttr('defaultRenderGlobals.extensionPadding', 4)

    cmds.setAttr('defaultRenderGlobals.imageFilePrefix', output_prefix, type='string')
    cmds.setAttr('defaultRenderGlobals.imageFormat', 32)  # png
    s = cmds.playbackOptions(q=True, min=True)
    e = cmds.playbackOptions(q=True, max=True)
    cmds.setAttr('defaultRenderGlobals.startFrame', s)
    cmds.setAttr('defaultRenderGlobals.endFrame', e)

    cmds.render(cam_name, x=320, y=240)

    final_output = os.path.join(output_dir, cam_name, output_prefix + '.%04d.png')

    # Convert preview to gif

    _args = [
        r'D:\ffmpeg.exe',
        '-i', final_output,
        '-f', 'gif',
        '-y',
        output_name,
    ]
    subprocess.Popen(_args).wait()

    # Cleanup

    for path in glob.glob(final_output.replace('%04d', '*')):
        os.remove(path)


main(sys.argv[1], sys.argv[2])
