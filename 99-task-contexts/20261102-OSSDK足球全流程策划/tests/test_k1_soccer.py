"""只使用合成数据和模拟SDK，不连接机器人。"""
import importlib.util
import math
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace as NS
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划/k1_soccer.py'
spec = importlib.util.spec_from_file_location('k1_soccer', MODULE)
s = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = s
spec.loader.exec_module(s)


def calibration(**kwargs):
    values = dict(body_from_trunk=np.eye(4).tolist(), tf_direction_verified=True,
                  control_origin_verified=True, clocks_verified=True, ball_radius_m=0.09,
                  evidence='SYNTHETIC_TEST_ONLY', geometry_verified=True,
                  ground_plane_body=(0, 0, 1, 0), motion_profile_verified=True)
    values.update(kwargs)
    return s.Calibration(**values)


def capture(**kwargs):
    transform = np.array([[0, 0, 1, 0.08], [-1, 0, 0, 0.04], [0, -1, 0, 1], [0, 0, 0, 1]], float)
    values = dict(sequence=1, generation=1, sensor_time=10, received_mono=10,
                  size=(320, 240), camera_frame='optical', info_frame='optical',
                  k=np.array([[100, 0, 160], [0, 100, 120], [0, 0, 1]], float),
                  distortion=(0, 0, 0, 0, 0), trunk_from_camera=transform,
                  tf_time=10, odom_pose=(0, 0, 0), odom_time=10, stationary=True)
    values.update(kwargs)
    return s.Capture(**values)


def ball(**kwargs):
    values = dict(valid=True, reason='ok', sequence=1, generation=1, capture_time=10,
                  received_mono=10, x=1.2, y=0, z=0.09, method='depth_sphere',
                  ball_odom=(1.2, 0), age_s=0.1)
    values.update(kwargs)
    return s.BallEstimate(**values)


def observation(planner, now, x=1.2, **kwargs):
    b = ball(generation=planner.generation, received_mono=now, x=x, ball_odom=(x, 0), **kwargs)
    cap = capture(generation=planner.generation, received_mono=now, sequence=b.sequence)
    return s.Observation(cap, s.BallTarget((150, 200, 20, 20), .9), b)


class SelectionTests(unittest.TestCase):
    def result(self, label='Ball', confidence=.9, bbox=(100, 100, 20, 20)):
        return NS(class_name=label, confidence=confidence,
                  bbox=NS(**dict(zip(('x', 'y', 'width', 'height'), bbox))))

    def test_not_first_item(self):
        chosen = s.select_ball([self.result('Person'), self.result(confidence=.8)], (320, 240), s.SoccerConfig())
        self.assertEqual(chosen.confidence, .8)

    def test_bad_numeric_and_clipped_box(self):
        bad = [self.result(confidence=math.nan), self.result(bbox=(310, 100, 20, 20)), self.result(confidence=.1)]
        self.assertIsNone(s.select_ball(bad, (320, 240), s.SoccerConfig()))

    def test_lock_rejects_other_ball(self):
        previous = s.BallTarget((10, 100, 20, 20), .8)
        self.assertIsNone(s.select_ball([self.result(bbox=(250, 100, 20, 20))], (320, 240), s.SoccerConfig(), previous))


class GeometryTests(unittest.TestCase):
    def test_nonzero_ground_height(self):
        cap = capture()
        center = s.ray_ground_center(160, 220, cap.k, cap.trunk_from_camera, (0, 0, 1, -.2), .09)
        np.testing.assert_allclose(center, [.88, .04, .29], atol=1e-8)

    def test_horizon_rejected(self):
        cap = capture()
        with self.assertRaisesRegex(ValueError, 'horizon'):
            s.ray_ground_center(160, 120, cap.k, cap.trunk_from_camera, (0, 0, 1, 0), .09)

    def test_scaled_transform_rejected(self):
        cap = capture()
        matrix = cap.trunk_from_camera.copy()
        matrix[:3, :3] *= 2
        result = s.locate_ball(s.replace(cap, trunk_from_camera=matrix),
                              s.BallTarget((150, 200, 20, 20), .9), calibration(), s.SoccerConfig())
        self.assertEqual(result.reason, 'non_rigid_capture_transform')

    def test_geometry_fallback_has_known_center(self):
        estimate = s.locate_ball(capture(), s.BallTarget((150, 200, 20, 20), .9), calibration(), s.SoccerConfig())
        self.assertTrue(estimate.valid, estimate.reason)
        np.testing.assert_allclose([estimate.x, estimate.y, estimate.z], [1.08, .04, .09], atol=1e-8)

    def test_unverified_origin_not_metric(self):
        result = s.locate_ball(capture(), s.BallTarget((150, 200, 20, 20), .9), s.Calibration(), s.SoccerConfig())
        self.assertFalse(result.valid)
        self.assertIsNone(result.x)

    def test_latest_pose_cannot_replace_capture_pose(self):
        result = s.locate_ball(capture(tf_time=12), s.BallTarget((150, 200, 20, 20), .9), calibration(), s.SoccerConfig())
        self.assertIn('time_mismatch', result.reason)

    def test_moving_capture_cannot_use_fixed_plane(self):
        result = s.locate_ball(capture(stationary=False), s.BallTarget((150, 200, 20, 20), .9), calibration(), s.SoccerConfig())
        self.assertFalse(result.valid)

    def test_nonzero_distortion_rejected(self):
        result = s.locate_ball(capture(distortion=(.1, 0, 0, 0, 0)), s.BallTarget((150, 200, 20, 20), .9), calibration(), s.SoccerConfig())
        self.assertEqual(result.reason, 'image_requires_undistortion')

    def test_sphere_fit_recovers_center(self):
        k = np.array([[250, 0, 160], [0, 250, 120], [0, 0, 1]], float)
        vv, uu = np.mgrid[:240, :320]
        rays = np.stack([(uu - 160) / 250, (vv - 120) / 250, np.ones_like(uu)], axis=-1)
        center, radius = np.array([0, 0, 1.2]), .09
        a = np.sum(rays * rays, axis=-1)
        b = rays @ center
        disc = b * b - a * (center @ center - radius * radius)
        depth = np.where(disc > 0, (b - np.sqrt(np.maximum(disc, 0))) / a, 0) / .001
        cap = capture(k=k, depth=depth, depth_time=10, depth_frame='optical')
        cal = calibration(depth_verified=True, rgb_depth_registered=True, depth_scale_m=.001)
        actual = s.depth_sphere_center(cap, s.BallTarget((140, 100, 40, 40), .9), cal, s.SoccerConfig())
        np.testing.assert_allclose(actual, center, atol=1e-8)

    def test_equal_dimensions_do_not_prove_registration(self):
        cap = capture(depth=np.full((240, 320), 1000), depth_time=10, depth_frame='optical')
        with self.assertRaisesRegex(ValueError, 'unverified'):
            s.depth_sphere_center(cap, s.BallTarget((150, 100, 20, 20), .9),
                                  calibration(depth_verified=True, depth_scale_m=.001), s.SoccerConfig())

    def test_odom_translation_and_rotation(self):
        p = s.to_odom((1, .2), (2, 3, math.pi / 2))
        np.testing.assert_allclose(p, [1.8, 4], atol=1e-8)
        np.testing.assert_allclose(s.from_odom(p, (2, 3, math.pi / 2)), [1, .2], atol=1e-8)

    def test_delayed_ball_reprojected(self):
        actual = s.current_ball(ball(), (.4, 0, 0), 11, 11, s.SoccerConfig())
        self.assertTrue(actual.valid)
        self.assertAlmostEqual(actual.x, .8)
        self.assertEqual(actual.capture_time, 10)

    def test_kick_age_stricter_than_static_observation(self):
        self.assertFalse(s.current_ball(ball(), (0, 0, 0), 12, 12, s.SoccerConfig(), kicking=True).valid)

    def test_clock_reset_rejected(self):
        self.assertFalse(s.current_ball(ball(), (0, 0, 0), 9, 10.1, s.SoccerConfig()).valid)

    def test_measured_zero_x_not_rejected_by_localization(self):
        cap = capture()
        target = s.BallTarget((150, 210, 20, 10), .9)
        profile = calibration()
        point = s.ray_ground_center(160, 220, cap.k, cap.trunk_from_camera,
                                    profile.ground_plane_body, profile.ball_radius_m)
        transform = cap.trunk_from_camera.copy()
        transform[0, 3] -= point[0]
        actual = s.locate_ball(s.replace(cap, trunk_from_camera=transform), target,
                               profile, s.SoccerConfig())
        self.assertTrue(actual.valid, actual.reason)
        self.assertAlmostEqual(actual.x, 0, places=10)

    def test_zero_x_is_current_coordinate_but_stale_zero_is_rejected(self):
        b = ball(x=0, ball_odom=(0, 0))
        cfg = s.SoccerConfig()
        actual = s.current_ball(b, (0, 0, 0), 10.1, 10.1, cfg, kicking=True)
        self.assertTrue(actual.valid)
        self.assertEqual((actual.x, actual.y), (0, 0))
        expired = s.current_ball(b, (0, 0, 0), 10.5, 10.5, cfg, kicking=True)
        self.assertFalse(expired.valid)


class PlannerTests(unittest.TestCase):
    def test_head_scan_precedes_body_turn(self):
        p = s.SoccerPlanner(s.SoccerConfig(head_yaws=(0, -.5), observation_wait_s=.2, head_settle_s=.1))
        first = p.step(0, None, s.BallEstimate(), (0, 0, 0))
        self.assertEqual(first[-1].kind, 'head')
        p.step(.31, None, s.BallEstimate(), (0, 0, 0))
        second = p.step(.32, None, s.BallEstimate(), (0, 0, 0))
        self.assertEqual(second[-1].values[-1], -.5)
        third = p.step(.63, None, s.BallEstimate(), (0, 0, 0))
        self.assertEqual(p.state, 'BODY_TURN')
        self.assertEqual(third[-1].kind, 'velocity')
        self.assertGreater(third[-1].values[2], 0)

    def prepare_localize(self, cfg=None, x=1.2):
        p = s.SoccerPlanner(cfg or s.SoccerConfig())
        p.step(0, None, s.BallEstimate(), (0, 0, 0))
        o = observation(p, 1, x)
        p.step(1, o, o.ball, (0, 0, 0))
        return p, o

    def test_step_ends_without_new_detection(self):
        p, o = self.prepare_localize()
        actions = p.step(1.1, o, o.ball, (0, 0, 0))
        self.assertGreater(actions[0].values[0], 0)
        actions = p.step(1.41, None, s.BallEstimate(), (0, 0, 0))
        self.assertEqual(actions[0].values, (0, 0, 0))

    def test_prior_generation_cannot_drive_again(self):
        p, o = self.prepare_localize()
        p.step(1.1, o, o.ball, (0, 0, 0))
        p.step(1.41, None, s.BallEstimate(), (0, 0, 0))
        p.step(2.2, None, s.BallEstimate(), (0, 0, 0))
        self.assertEqual(p.step(2.3, o, o.ball, (0, 0, 0)), [])

    def test_handoff_does_not_enable_kick_by_default(self):
        p, o = self.prepare_localize(x=.6)
        actions = p.step(1.1, o, o.ball, (0, 0, 0))
        self.assertEqual(p.reason, 'ready_for_kick_without_activation')
        self.assertNotIn('kick_begin', [a.kind for a in actions])

    def test_kick_loss_is_not_success(self):
        p, o = self.prepare_localize(s.SoccerConfig(allow_kick=True), x=.6)
        p.step(1.1, o, o.ball, (0, 0, 0))
        actions = p.step(1.2, None, s.BallEstimate(), (0, 0, 0))
        self.assertEqual(actions[0].kind, 'kick_end')
        self.assertEqual(p.state, 'VERIFY')
        p.step(7, None, s.BallEstimate(), (0, 0, 0))
        self.assertEqual(p.reason, 'unconfirmed:kick_ball_feed_lost')

    def test_robot_motion_not_ball_motion(self):
        p, o = self.prepare_localize(s.SoccerConfig(allow_kick=True), x=.6)
        p.step(1.1, o, o.ball, (0, 0, 0))
        o2 = observation(p, 3, .3, sequence=2)
        b = s.replace(o2.ball, ball_odom=(.6, 0))
        actions = p.step(3, o2, b, (.3, 0, 0))
        self.assertEqual(p.state, 'KICK')
        self.assertEqual(actions[0].kind, 'kick_update')

    def test_continuous_current_ball_updates_reach_zero(self):
        p, o = self.prepare_localize(s.SoccerConfig(allow_kick=True), x=.6)
        p.step(1.1, o, o.ball, (0, 0, 0))
        for index in range(1, 101):
            x = .6 * (100 - index) / 100
            now = 1.1 + index / 30
            o = observation(p, now, x, sequence=index + 1)
            # 球在 odom 中未移动；机器人接近，身体坐标逐渐减至零。
            b = s.replace(o.ball, ball_odom=(.6, 0))
            actions = p.step(now, o, b, (.6 - x, 0, 0))
            self.assertEqual(p.state, 'KICK')
            self.assertEqual(actions[0].kind, 'kick_update')
            self.assertEqual(actions[0].values, (x, 0))

    def test_fast_republishing_does_not_renew_old_visual_observation(self):
        p, o = self.prepare_localize(s.SoccerConfig(allow_kick=True), x=.6)
        p.step(1.1, o, o.ball, (0, 0, 0))
        for index in range(1, 7):
            now = 10 + index / 20
            b = s.current_ball(o.ball, (0, 0, 0), now, 1 + index / 20, p.cfg, kicking=True)
            self.assertEqual(p.step(1.1 + index / 20, o, b, (0, 0, 0))[0].kind, 'kick_update')
        b = s.current_ball(o.ball, (0, 0, 0), 10.4, 1.4, p.cfg, kicking=True)
        actions = p.step(1.5, o, b, (0, 0, 0))
        self.assertEqual(actions[0].kind, 'kick_end')
        self.assertEqual(p.reason, 'kick_ball_feed_lost')

    def test_total_timeout_stops(self):
        p = s.SoccerPlanner(s.SoccerConfig(max_total_time_s=1))
        p.step(0, None, s.BallEstimate(), (0, 0, 0))
        a = p.step(2, None, s.BallEstimate(), (0, 0, 0))
        self.assertEqual(p.reason, 'total_timeout')
        self.assertEqual(a[-1].values, (0, 0, 0))


class FakeRobot:
    def __init__(self):
        self.callbacks, self.actions, self.unsubscribed = {}, [], 0

    def get_mode(self):
        return 'walk'

    def list_joints(self):
        return [NS(name='aahead_pitch_joint', limits=NS(min=-.2967, max=.7505)),
                NS(name='aahead_yaw_joint', limits=NS(min=-1.0297, max=1.0297))]

    def subscribe_image(self, callback, **kwargs):
        self.callbacks[kwargs['img_type']] = callback
        return NS(unsubscribe=lambda: setattr(self, 'unsubscribed', self.unsubscribed + 1))

    def get_camera_info(self, **kwargs):
        return NS(width=320, height=240, header=NS(frame_id='optical'), k=capture().k, d=[0] * 5)

    def get_transform(self, **kwargs):
        return NS(timestamp=time.time(), to_matrix=lambda: capture().trunk_from_camera)

    def get_odom(self):
        return NS(timestamp=time.time(), pose_2d=(0, 0, 0))

    def set_velocity(self, *values):
        self.actions.append(('velocity', values))

    def set_head_angle(self, **values):
        self.actions.append(('head', values))

    def send(self):
        t = time.time()
        image = NS(width=320, height=240, timestamp=t, header=NS(frame_id='optical'),
                   to_numpy=lambda: np.zeros((240, 320, 3), np.uint8))
        self.callbacks['rgb'](image)


class ApplicationTests(unittest.TestCase):
    def test_readonly_has_no_robot_actions(self):
        robot = FakeRobot()
        detected = threading.Event()
        def detect(*args, **kwargs):
            detected.set()
            return []
        app = s.SoccerApp(robot, NS(detect=detect))
        app.start()
        robot.send()
        self.assertTrue(detected.wait(1))
        app.stop()
        self.assertEqual(robot.actions, [])
        self.assertEqual(robot.unsubscribed, 2)

    def test_unverified_profile_rejects_live_before_subscribing(self):
        robot = FakeRobot()
        with self.assertRaises(ValueError):
            s.SoccerApp(robot, NS()).start(enable_motion=True)
        self.assertEqual(robot.callbacks, {})
        self.assertEqual(robot.actions, [])

    def test_actual_joint_names_and_limits_checked(self):
        app = s.SoccerApp(FakeRobot(), NS(), calibration(), s.SoccerConfig(head_pitch=.9))
        with self.assertRaisesRegex(ValueError, 'out_of_limits'):
            app.start(enable_motion=True)

    def test_control_stops_while_inference_blocked(self):
        robot = FakeRobot()
        entered, release = threading.Event(), threading.Event()
        def detect(*args, **kwargs):
            entered.set()
            release.wait(2)
            return []
        cfg = s.SoccerConfig(head_settle_s=.03, observation_wait_s=1, control_period_s=.01)
        app = s.SoccerApp(robot, NS(detect=detect), calibration(), cfg)
        app.start(enable_motion=True)
        time.sleep(.06)
        robot.send()
        self.assertTrue(entered.wait(1))
        status = app.stop(.15)
        self.assertEqual(status['state'], 'STOPPING')
        self.assertEqual(robot.actions[-1], ('velocity', (0, 0, 0)))
        with self.assertRaisesRegex(RuntimeError, 'still_running'):
            app.start()
        count = len(robot.actions)
        release.set()
        status = app.stop(1)
        self.assertFalse(any(status['workers_alive'].values()))
        self.assertEqual(len(robot.actions), count)
        self.assertFalse(status['physical_kick_confirmed'])

    def test_command_conflict_rejected(self):
        app = s.SoccerApp(FakeRobot(), NS())
        app._motion, app._manager_may_be_active = True, True
        with self.assertRaisesRegex(RuntimeError, 'conflicts'):
            app._execute(s.Action('velocity', (.1, 0, 0)))

    def test_kick_update_forwards_zero_without_changing_command(self):
        app = s.SoccerApp(FakeRobot(), NS())
        received = []
        app._motion, app._manager_may_be_active = True, True
        app._manager = NS(update_ball=lambda **values: received.append(values))
        app._execute(s.Action('kick_update', (0, 0)))
        self.assertEqual(received, [{'x': 0, 'y': 0}])
        self.assertEqual(app.robot.actions, [])

    def test_shutdown_failure_still_requests_zero_and_blocks_restart(self):
        robot = FakeRobot()
        app = s.SoccerApp(robot, NS())
        def fail():
            raise RuntimeError('shutdown_failed')
        app._manager, app._motion, app._manager_may_be_active = NS(stop=fail), True, True
        app._stop.set()
        app._control_loop()
        self.assertEqual(robot.actions[-1], ('velocity', (0, 0, 0)))
        self.assertEqual(app.status()['state'], 'ERROR')
        with self.assertRaisesRegex(RuntimeError, 'shutdown_unconfirmed'):
            app.start()

    def test_missing_metadata_still_allows_pixel_detection(self):
        robot = FakeRobot()
        def bad_info(**kwargs):
            raise RuntimeError('not_ready')
        robot.get_camera_info = bad_info
        app = s.SoccerApp(robot, NS(detect=lambda *args, **kwargs: []))
        app.start()
        robot.send()
        limit = time.monotonic() + 1
        while app.status()['last_observation'] is None and time.monotonic() < limit:
            time.sleep(.01)
        app.stop()
        self.assertIn('capture_unavailable', app.status()['last_observation']['reason'])

    def test_log_json_does_not_write_infinity(self):
        app = s.SoccerApp(FakeRobot(), NS())
        app._observation = s.Observation(capture(), None, s.BallEstimate())
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'log.json'
            app.save_log(f)
            self.assertNotIn('Infinity', f.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
