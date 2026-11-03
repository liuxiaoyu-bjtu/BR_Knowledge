"""原算法对照、坐标约定及只读SDK接线检查。无需机器人/ROS。"""
import ast
from dataclasses import dataclass
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
from typing import Any, Dict, Optional, Tuple
import unittest

import numpy as np

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
SOURCE = ROOT / "04-shared/sdk-tests/足球坐标只读测试/geometry_ball_coordinates.py"
spec = importlib.util.spec_from_file_location("geometry_probe", SOURCE)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

# 只载入旧文件中的纯数学部分，避免导入ROS；算法原句不改写。
tree = ast.parse((TASK / "legacy_sources/ball_localization_utils.py").read_text(encoding="utf-8"))
names = {"DEFAULT_T_CAM_TO_HEAD", "CameraModel", "choose_ball_pixel", "pixel_to_ray_camera", "ray_to_ground_base"}
nodes = [node for node in tree.body if getattr(node, "name", None) in names
         or isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets)]
old = dict(np=np, dataclass=dataclass, Any=Any, Dict=Dict, Optional=Optional, Tuple=Tuple)
exec(compile(ast.Module(body=nodes, type_ignores=[]), "original_chapter12_math", "exec"), old)

K = np.array([[207.4547727507004, 0, 280.23952732086184],
              [0, 207.4547727507004, 214.98355865478516], [0, 0, 1]])
OPTICAL_TO_FORWARD = np.array([[0, 0, 1], [-1, 0, 0], [0, -1, 0]], dtype=float)


def pose(height=.8, yaw=0., pitch=0.):
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    matrix = np.eye(4)
    matrix[:3, :3] = rz @ ry @ OPTICAL_TO_FORWARD
    matrix[:3, 3] = [.07, .04, height]
    return matrix


class GeometryTests(unittest.TestCase):
    def test_legacy_pixel_selection_exact(self):
        for box in ([289, 263, 19, 18], [100, 200, 50, 60]):
            x, y, w, h = box
            expected = old["choose_ball_pixel"]({"bbox_xyxy": [x, y, x+w, y+h]},
                use_bottom_center=True, bbox_bottom_offset_ratio=.1, fallback_cx=0, fallback_cy=0)
            self.assertEqual(g.choose_ball_pixel(box), expected)

    def test_actual_pixel(self):
        np.testing.assert_allclose(g.choose_ball_pixel([289,263,19,18]), [298.5,279.2])

    def test_old_ray_exact(self):
        model = old["CameraModel"](fx=K[0,0], fy=K[1,1], cx=K[0,2], cy=K[1,2])
        for pixel in [(298.5,279.2), (100,300), (400,400)]:
            np.testing.assert_allclose(g.pixel_to_ray_camera(*pixel,K),
                old["pixel_to_ray_camera"](*pixel,model), atol=1e-12)

    def test_old_intersection_exact_across_poses(self):
        model = old["CameraModel"](fx=K[0,0], fy=K[1,1], cx=K[0,2], cy=K[1,2])
        for height in (.65,.8,.88):
            for yaw,pitch in [(0,0),(.4,.15),(-.5,.3)]:
                camera_pose = pose(height,yaw,pitch)
                head_pose = camera_pose @ np.linalg.inv(model.T_cam_to_head)
                expected = old["ray_to_ground_base"](298.5,279.2,camera_model=model,
                    T_head_to_base=head_pose,T_compensation=np.eye(4))
                actual = g.ray_to_ground_base(298.5,279.2,k=K,T_base_camera=camera_pose)["point_base_m"]
                np.testing.assert_allclose(actual, expected, atol=1e-8)

    def test_legacy_composition_with_compensation(self):
        from scipy.spatial.transform import Rotation
        head=np.eye(4); head[:3,3]=[.1,.03,.85]
        comp=np.eye(4); comp[:3,:3]=Rotation.from_euler('zy',[.1,.2]).as_matrix(); comp[2,3]=.02
        np.testing.assert_allclose(g.legacy_camera_pose(head,T_compensation=comp),
                                  head @ comp @ old['DEFAULT_T_CAM_TO_HEAD'])

    def test_x_forward_y_left(self):
        right=g.ray_to_ground_base(330,300,k=K,T_base_camera=pose())['point_base_m']
        left=g.ray_to_ground_base(230,300,k=K,T_base_camera=pose())['point_base_m']
        self.assertGreater(right[0],0); self.assertLess(right[1],0); self.assertGreater(left[1],0)

    def test_target_origin_and_height(self):
        body_pose=pose(.34)
        ground,body_height=g.ground_pose_from_body_tf(body_pose,.84)
        self.assertAlmostEqual(body_height,.5)
        np.testing.assert_allclose(ground[:2,3],body_pose[:2,3])
        self.assertAlmostEqual(ground[2,3],.84)

    def test_height_changes_scale_not_yaw(self):
        first=g.ray_to_ground_base(298.5,279.2,k=K,T_base_camera=pose(.8))['point_base_m']
        second=g.ray_to_ground_base(298.5,279.2,k=K,T_base_camera=pose(.4))['point_base_m']
        np.testing.assert_allclose(np.array(first[:2])-[.07,.04],2*(np.array(second[:2])-[.07,.04]))

    def test_horizontal_ray_rejected(self):
        with self.assertRaisesRegex(ValueError,'平行'):
            g.ray_to_ground_base(K[0,2],K[1,2],k=K,T_base_camera=pose())

    def test_upward_ray_rejected(self):
        with self.assertRaisesRegex(ValueError,'上方'):
            g.ray_to_ground_base(298,100,k=K,T_base_camera=pose())

    def test_bad_matrix_or_height(self):
        for height in (0,-.8,float('nan')):
            with self.assertRaises(ValueError): g.ground_pose_from_body_tf(np.eye(4),height)
        bad=pose(); bad[0,0]=4
        with self.assertRaises(ValueError): g.rigid_matrix(bad)

    def test_nonzero_distortion(self):
        import cv2
        d=np.array([.03,-.01,0,0,0])
        xy=cv2.undistortPoints(np.array([[[298.5,279.2]]]),K,d).reshape(2)
        expected=np.r_[xy,1]; expected/=np.linalg.norm(expected)+1e-9
        np.testing.assert_allclose(g.pixel_to_ray_camera(298.5,279.2,K,distortion=d),expected)

    def test_no_silent_height_or_double_extrinsics(self):
        with self.assertRaisesRegex(ValueError,'先设置'): g.run_geometry_probe()
        with self.assertRaisesRegex(ValueError,'重复'): g.run_geometry_probe(camera_height_m=.8,T_cam_to_head=np.eye(4))
        with self.assertRaisesRegex(ValueError,'同时'): g.run_geometry_probe(camera_height_m=.8,head_to_ground=np.eye(4))


class Image:
    width,height=544,448
    header=NS(frame_id='head_color_optical_frame',timestamp=100.)
    timestamp=100.
    encoding='bgr8'
    def to_numpy(self): return np.zeros((448,544,3),dtype=np.uint8)
    def save(self,path):
        from PIL import Image as PILImage
        PILImage.fromarray(self.to_numpy()).save(path)


class Robot:
    def __init__(self,frames=None):
        self.frames=frames if frames is not None else ['head_color_optical_frame','trunk']
        self.unsubscribed=False; self.tf_calls=0
    def subscribe_image(self,callback,**kwargs):
        assert kwargs['img_type']=='rgb'
        callback(Image())
        return NS(unsubscribe=lambda: setattr(self,'unsubscribed',True))
    def get_camera_info(self,**kwargs):
        return NS(width=544,height=448,header=Image.header,k=K,d=[0]*5,distortion_model='plumb_bob')
    def list_frames(self): return self.frames
    def get_transform(self,*,target_frame,source_frame):
        assert (target_frame,source_frame)==('trunk','head_color_optical_frame')
        self.tf_calls+=1
        return NS(to_matrix=lambda: pose(.34),timestamp=100.,source_frame='trunk',target_frame=source_frame)


class Detector:
    def __init__(self,results=None):
        self.results=results if results is not None else [NS(class_name='Ball',confidence=.86,
            bbox=NS(x=289,y=263,width=19,height=18))]
    def detect(self,*args,**kwargs): return self.results
    def plot(self,*args,**kwargs):
        from PIL import Image as PILImage
        return PILImage.new('RGB',(544,448))


class IntegrationTests(unittest.TestCase):
    def run_probe(self,robot=None,detector=None,**kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            robot=robot or Robot()
            report=g.run_geometry_probe(robot,detector or Detector(),output_root=tmp,**kwargs)
            p=Path(report['output_dir'])
            stored=json.loads((p/'原始记录.json').read_text(encoding='utf-8'))
            self.assertEqual(stored['status'],report['status'])
            self.assertTrue(p.with_suffix('.zip').exists())
            self.assertTrue(robot.unsubscribed)
            return report,robot

    def test_sdk_tf_readonly_snapshot(self):
        result,robot=self.run_probe(camera_height_m=.84)
        self.assertEqual(result['status'],'geometry_candidate')
        self.assertFalse(result['control_input_verified'])
        self.assertLess(result['kick_input_preview']['y'],0)
        self.assertAlmostEqual(result['point_body_m'][2],-.5)
        self.assertEqual(robot.tf_calls,1)

    def test_five_head_frames_do_not_imply_body(self):
        robot=Robot(['aahead_pitch_link','head_booster_stereo_rgb_link','head_color_optical_frame',
                     'head_point','head_realsense_rgb_link'])
        result,robot=self.run_probe(robot=robot,camera_height_m=.84)
        self.assertEqual(result['status'],'error'); self.assertEqual(robot.tf_calls,0)
        self.assertIsNone(result['kick_input_preview'])

    def test_explicit_original_head_pose_needs_no_body_tf(self):
        camera_pose=pose(.84)
        head=camera_pose @ np.linalg.inv(g.LEGACY_T_CAM_TO_HEAD)
        result,robot=self.run_probe(robot=Robot([]),head_to_ground=head)
        self.assertEqual(result['status'],'geometry_candidate'); self.assertEqual(robot.tf_calls,0)

    def test_no_ball_not_zero_ball(self):
        result,_=self.run_probe(camera_height_m=.84,detector=Detector([]))
        self.assertEqual(result['status'],'no_ball'); self.assertIsNone(result['kick_input_preview'])

    def test_measured_reference_never_changes_result(self):
        first,_=self.run_probe(camera_height_m=.84,known_xy=[2.5,0])
        second,_=self.run_probe(camera_height_m=.84,known_xy=[99,99])
        self.assertEqual(first['kick_input_preview'],second['kick_input_preview'])

    def test_capture_timeout_unsubscribes(self):
        robot=Robot()
        robot.subscribe_image=lambda *a,**k:NS(unsubscribe=lambda:setattr(robot,'unsubscribed',True))
        result,robot=self.run_probe(robot=robot,camera_height_m=.84,timeout_s=.001)
        self.assertEqual(result['status'],'error')

    def test_only_public_read_calls(self):
        calls={n.func.attr for n in ast.walk(ast.parse(SOURCE.read_text(encoding='utf-8')))
               if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
               and isinstance(n.func.value,ast.Name) and n.func.value.id=='robot'}
        self.assertEqual(calls,{'subscribe_image','get_camera_info','list_frames','get_transform'})
        self.assertNotIn('SoccerKickManager', {n.id for n in ast.walk(ast.parse(SOURCE.read_text(encoding='utf-8')))
                                            if isinstance(n,ast.Name)})


if __name__=='__main__':
    unittest.main(verbosity=2)
