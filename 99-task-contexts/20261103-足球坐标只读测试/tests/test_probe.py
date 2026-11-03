"""合成球面和模拟SDK检查；不连接机器人。"""
import ast
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
import zipfile

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "04-shared/sdk-tests/足球坐标只读测试/probe_ball_coordinates.py"
spec = importlib.util.spec_from_file_location("probe_ball_coordinates", SCRIPT)
p = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = p
spec.loader.exec_module(p)

K = np.array([[100., 0, 160], [0, 100, 120], [0, 0, 1]])
M = np.array([[0, 0, 1, .05], [-1, 0, 0, .02], [0, -1, 0, .7], [0, 0, 0, 1]])


def sphere_depth(scale=.001):
    u, v = np.meshgrid(np.arange(320), np.arange(240))
    ray = np.stack([(u - 160) / 100, (v - 120) / 100, np.ones_like(u)], axis=-1)
    center, radius = np.array([0, 0, 1.2]), .12
    a = (ray ** 2).sum(axis=-1)
    b = -2 * (ray * center).sum(axis=-1)
    c = center @ center - radius ** 2
    disc = b * b - 4 * a * c
    valid = disc >= 0
    raw = np.zeros((240, 320))
    raw[valid] = (-b[valid] - np.sqrt(disc[valid])) / (2 * a[valid]) / scale
    return raw


class FakeImage:
    def __init__(self, depth=False, skew=0):
        self.width, self.height, self.timestamp = 320, 240, 100 + skew
        self.header = NS(timestamp=self.timestamp, frame_id="head_optical")
        self.encoding = "mono16" if depth else "bgr8"
        self.array = sphere_depth() if depth else np.zeros((240, 320, 3), np.uint8)

    def to_numpy(self):
        return self.array

    def save(self, path):
        Image.fromarray(self.array.astype(np.uint8)).save(path)


class FakeRobot:
    def __init__(self, no_depth=False, skew=0):
        self.calls, self.cancelled = [], []
        self.no_depth, self.skew = no_depth, skew

    def subscribe_image(self, callback, *, img_type, **kwargs):
        self.calls.append("subscribe_" + img_type)
        if img_type == "rgb" or not self.no_depth:
            callback(FakeImage(img_type == "depth", self.skew if img_type == "depth" else 0))
        return NS(unsubscribe=lambda: self.cancelled.append(img_type))

    def get_camera_info(self, **kwargs):
        self.calls.append("info")
        return NS(width=320, height=240, header=NS(frame_id="head_optical"), k=K,
                  d=[0, 0, 0, 0, 0], distortion_model="plumb_bob")

    def get_transform(self, *, target_frame, source_frame):
        self.calls.append("tf_" + target_frame)
        matrix = M if target_frame == "trunk" else np.linalg.inv(M)
        # 模拟本机返回标签与请求方向看似颠倒，矩阵仍按请求约定。
        return NS(timestamp=100, source_frame=target_frame, target_frame=source_frame,
                  to_matrix=lambda: matrix)


class FakeDetector:
    def __init__(self, robot, ball=True):
        self.robot, self.ball = robot, ball

    def detect(self, *args, **kwargs):
        self.robot.calls.append("detect")
        if not self.ball:
            return []
        return [NS(class_name="Person", confidence=.99, distance_m=None,
                   bbox=NS(x=20, y=20, width=40, height=60)),
                NS(class_name="Ball", confidence=.9, distance_m=None,
                   bbox=NS(x=147, y=107, width=26, height=26))]

    def plot(self, *args, **kwargs):
        return Image.new("RGB", (320, 240))


class GeometryTests(unittest.TestCase):
    def fit(self, data=None, **kwargs):
        return p.sphere_from_depth(sphere_depth() if data is None else data, (320, 240),
            kwargs.get("box", [147, 107, 26, 26]), K, kwargs.get("d", [0] * 5),
            kwargs.get("model", "plumb_bob"), kwargs.get("scale", .001))

    def test_sphere_center_and_surface_are_distinct(self):
        fit = self.fit()
        np.testing.assert_allclose(fit["center_camera_m"], [0, 0, 1.2], atol=1e-8)
        self.assertAlmostEqual(fit["fitted_radius_m"], .12)
        self.assertLess(fit["sphere_rms_m"], 1e-8)
        self.assertLess(fit["surface_sample_median_camera_m"][2], 1.15)

    def test_scale_is_explicit_not_inferred_from_dtype(self):
        fit = self.fit(scale=.002)
        np.testing.assert_allclose(fit["center_camera_m"], [0, 0, 2.4], atol=1e-8)
        self.assertAlmostEqual(fit["fitted_radius_m"], .24)

    def test_optical_to_trunk_rotation_and_translation(self):
        np.testing.assert_allclose(p.transform_point(M, [.2, .1, 1.2]), [1.25, -.18, .6])

    def test_inverse_roundtrip_does_not_remove_translation(self):
        point = [.2, -.3, 1.2]
        np.testing.assert_allclose(p.transform_point(np.linalg.inv(M), p.transform_point(M, point)), point)

    def test_scaled_tf_rejected(self):
        m = M.copy()
        m[0, :3] *= 2
        with self.assertRaisesRegex(ValueError, "刚体"):
            p.transform_point(m, [0, 0, 1])

    def test_different_resolution_not_rescaled(self):
        with self.assertRaisesRegex(ValueError, "尺寸不同"):
            self.fit(sphere_depth()[:, :160])

    def test_invalid_depth_does_not_produce_center(self):
        with self.assertRaisesRegex(ValueError, "不足"):
            self.fit(np.full((240, 320), 65535))

    def test_planar_depth_preserves_surface_without_fake_ball_center(self):
        fit = self.fit(np.full((240, 320), 1000))
        self.assertIsNone(fit["center_camera_m"])
        self.assertIn("sphere_error", fit)
        self.assertAlmostEqual(fit["surface_sample_median_camera_m"][2], 1)

    def test_nonzero_distortion_processed(self):
        fit = self.fit(d=[1e-5, 0, 0, 0, 0])
        np.testing.assert_allclose(fit["center_camera_m"], [0, 0, 1.2], atol=1e-4)

    def test_unknown_distortion_model_rejected(self):
        with self.assertRaisesRegex(ValueError, "不支持"):
            self.fit(d=[.1, 0, 0, 0], model="unknown")


class RunTests(unittest.TestCase):
    def run_fake(self, root, robot=None, **kwargs):
        robot = robot or FakeRobot()
        with redirect_stdout(io.StringIO()):
            report = p.run_probe(robot, FakeDetector(robot, kwargs.pop("ball", True)),
                                 output_root=root, timeout_s=.02, **kwargs)
        return report, robot

    def test_full_record_uses_tf_before_inference_and_reports_measured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, robot = self.run_fake(tmp, known_xy=(1.25, .02), ball_radius_m=.12)
            self.assertEqual(report["status"], "candidate_only")
            np.testing.assert_allclose(report["candidate_center_target_m"], [1.25, .02, .7], atol=1e-8)
            self.assertLess(report["measurement_comparison"]["planar_error_m"], 1e-8)
            self.assertFalse(report["control_input_verified"])
            self.assertLess(robot.calls.index("tf_trunk"), robot.calls.index("detect"))
            self.assertCountEqual(robot.cancelled, ["rgb", "depth"])
            folder = Path(report["output_dir"])
            saved = json.loads((folder / "原始记录.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["selected_detection_index"], 1)
            self.assertIsNone(saved["selected_ball"]["distance_m"])
            self.assertEqual(saved["transform"]["requested_source"], "head_optical")
            self.assertEqual(saved["transform"]["returned_source_label"], "trunk")
            with zipfile.ZipFile(folder.with_suffix(".zip")) as archive:
                self.assertTrue(any(n.endswith("depth_raw.npy") for n in archive.namelist()))

    def test_no_ball_keeps_source_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, _ = self.run_fake(tmp, ball=False)
            self.assertEqual(report["status"], "no_ball")
            self.assertTrue((Path(report["output_dir"]) / "depth_raw.npy").exists())

    def test_missing_depth_reports_error_but_still_detects(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, robot = self.run_fake(tmp, FakeRobot(no_depth=True))
            self.assertEqual(report["status"], "error")
            self.assertIn("缺少深度", report["error"])
            self.assertIn("detect", robot.calls)
            self.assertIsNone(report["candidate_center_target_m"])
            self.assertCountEqual(robot.cancelled, ["rgb", "depth"])

    def test_sensor_skew_saved_as_static_diagnostic_not_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, _ = self.run_fake(tmp, FakeRobot(skew=.4))
            self.assertAlmostEqual(report["rgb_depth_skew_s"], .4)
            self.assertTrue(any("RGB/深度时间差" in text for text in report["warnings"]))
            self.assertFalse(report["control_input_verified"])

    def test_sdk_error_cancels_subscriptions_and_packages_partial_data(self):
        robot = FakeRobot()
        def fail(**kwargs):
            raise RuntimeError("TF unavailable")
        robot.get_transform = fail
        with tempfile.TemporaryDirectory() as tmp:
            report, _ = self.run_fake(tmp, robot)
            self.assertEqual(report["status"], "error")
            self.assertIn("TF unavailable", report["error"])
            self.assertCountEqual(robot.cancelled, ["rgb", "depth"])
            self.assertTrue(Path(report["output_dir"]).with_suffix(".zip").exists())

    def test_code_has_no_motion_or_private_robot_calls(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        calls = {node.func.attr for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                 and isinstance(node.func.value, ast.Name) and node.func.value.id == "robot"}
        self.assertEqual(calls, {"subscribe_image", "get_camera_info", "get_transform"})
        imports = [n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertFalse(any("SoccerKickManager" in [a.name for a in n.names] for n in imports))


if __name__ == "__main__":
    unittest.main(verbosity=2)
