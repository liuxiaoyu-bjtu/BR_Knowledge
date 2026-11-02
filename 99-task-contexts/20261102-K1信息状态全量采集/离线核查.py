"""用模拟只读对象核查采集器；不创建真实BoosterRobot，不执行真机接口。"""
from dataclasses import dataclass, field
from contextlib import redirect_stdout
from enum import Enum
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / '04-shared/sdk-tests/probe_k1_info_state.py'
spec = importlib.util.spec_from_file_location('k1_probe_offline', SCRIPT)
probe = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = probe
spec.loader.exec_module(probe)


class SensorKind(str, Enum):
    CAMERA = 'camera'


@dataclass
class Limits:
    lower: float = -1.0
    upper: float = 1.0


@dataclass
class Info:
    name: str
    limits: Limits = field(default_factory=Limits)
    extra: dict = field(default_factory=lambda: {'kind': SensorKind.CAMERA, 'enabled': False})


class FakeRobot:
    def __init__(self, fail=None, empty_frames=False):
        self.calls = []
        self.fail = fail
        self.empty_frames = empty_frames

    def value(self, name, result):
        self.calls.append(name)
        if name == self.fail:
            raise RuntimeError('离线模拟的接口异常')
        return result

    @property
    def robot_info(self):
        return self.value('robot_info', {'model': 'Booster K1', 'extra': {'unknown_field': 42}})

    def get_mode(self):
        return self.value('get_mode', 'prepare')

    def list_gaits(self):
        return self.value('list_gaits', ['default', 'soccer'])

    def get_gait(self):
        return self.value('get_gait', 'default')

    def list_frames(self):
        first = self.calls.count('list_frames') == 0
        return self.value('list_frames', [] if first and self.empty_frames else [f'frame_{i}' for i in range(150)])

    def list_joints(self):
        return self.value('list_joints', [Info('joint_' + str(i)) for i in range(30)])

    def list_sensors(self):
        return self.value('list_sensors', [Info('head')])

    def list_actions(self):
        return self.value('list_actions', [{'id': 'action_' + str(i), 'duration': -1} for i in range(80)])


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_robot = probe._SESSION_ROBOT
        probe._SESSION_ROBOT = None

    def tearDown(self):
        probe._SESSION_ROBOT = self.old_robot
        self.temp.cleanup()

    def collect(self, robot=None, **kwargs):
        with redirect_stdout(io.StringIO()):
            path = probe.collect(robot=robot, output_root=self.temp.name,
                                 tester='离线模拟', note='不是真机记录', **kwargs)
        return path, json.loads((path / '原始记录.json').read_text(encoding='utf-8'))

    def test_full_values_nested_fields_and_bundle(self):
        robot = FakeRobot()
        path, report = self.collect(robot)
        self.assertEqual(robot.calls, list(probe.INTERFACES))
        self.assertTrue(report['completed'])
        frames = report['interfaces']['list_frames']['attempts'][0]['value']
        self.assertEqual(len(frames), 150)
        self.assertEqual(frames[-1], 'frame_149')
        joint = report['interfaces']['list_joints']['attempts'][0]['value'][0]
        self.assertEqual(joint['limits'], {'lower': -1.0, 'upper': 1.0})
        self.assertEqual(joint['extra']['kind']['value'], 'camera')
        self.assertIs(joint['extra']['enabled'], False)
        self.assertEqual(report['interfaces']['robot_info']['attempts'][0]['value']['extra']['unknown_field'], 42)
        self.assertEqual(len(report['interfaces']['list_actions']['attempts'][0]['value']), 80)
        text = (path / '采集汇总.md').read_text(encoding='utf-8')
        self.assertIn('frame_149', text)
        with zipfile.ZipFile(next(path.glob('*.zip'))) as bundle:
            self.assertIn('原始记录.json', bundle.namelist())
            self.assertEqual(len([n for n in bundle.namelist() if n.startswith('分接口/')]), 8)
            saved = json.loads(bundle.read('原始记录.json'))
            self.assertEqual(saved, report)

    def test_one_interface_error_does_not_skip_following(self):
        robot = FakeRobot(fail='list_sensors')
        _, report = self.collect(robot)
        self.assertEqual(robot.calls, list(probe.INTERFACES))
        bad = report['interfaces']['list_sensors']['attempts'][0]
        self.assertEqual(bad['status'], 'error')
        self.assertIn('RuntimeError', bad['traceback'])
        self.assertEqual(report['interfaces']['list_actions']['attempts'][0]['status'], 'returned')

    def test_empty_frames_retry_preserves_first_and_last(self):
        robot = FakeRobot(empty_frames=True)
        with patch.object(probe.time, 'sleep', return_value=None):
            _, report = self.collect(robot)
        row = report['interfaces']['list_frames']
        self.assertEqual(len(row['attempts']), 2)
        self.assertEqual(row['attempts'][0]['value'], [])
        self.assertEqual(row['attempts'][1]['item_count'], 150)
        self.assertEqual(row['selected_attempt'], 1)

    def test_empty_list_is_returned_and_not_api_error(self):
        robot = FakeRobot(empty_frames=True)
        _, report = self.collect(robot, frames_wait=0)
        row = report['interfaces']['list_frames']['attempts'][0]
        self.assertEqual(row['status'], 'returned')
        self.assertEqual(row['item_count'], 0)

    def test_cached_connection_and_distinct_directories(self):
        probe._SESSION_ROBOT = FakeRobot()
        first, report = self.collect()
        second, _ = self.collect()
        self.assertNotEqual(first, second)
        self.assertEqual(report['connection']['source'], '本模块缓存')
        self.assertEqual(len(probe._SESSION_ROBOT.calls), 16)

    def test_export_nonfinite_and_cycles_are_explicit(self):
        value = {'nonfinite': float('inf')}
        value['self'] = value
        warnings = []
        data = probe.normalize(value, warnings)
        json.dumps(data, allow_nan=False)
        self.assertEqual(data['nonfinite']['__float__'], 'inf')
        self.assertIn('__cycle__', data['self'])
        self.assertEqual(len(warnings), 2)

    def test_interrupt_saves_partial_result(self):
        robot = FakeRobot()
        with patch.object(robot, 'list_joints', side_effect=KeyboardInterrupt):
            path, report = self.collect(robot)
        self.assertFalse(report['completed'])
        self.assertTrue(report['interrupted'])
        self.assertEqual(report['interfaces']['list_joints']['attempts'][0]['status'], 'interrupted')
        self.assertNotIn('list_sensors', report['interfaces'])
        self.assertTrue((path / '分接口/list_joints.json').exists())
        self.assertTrue(list(path.glob('*.zip')))

    def test_connection_failure_saves_a_record_and_bundle(self):
        fake = types.ModuleType('boosteros.robots.booster')
        def fail():
            raise RuntimeError('离线模拟连接失败')
        fake.BoosterRobot = fail
        with patch.dict(sys.modules, {'boosteros.robots.booster': fake}):
            path, report = self.collect()
        self.assertFalse(report['completed'])
        self.assertEqual(report['connection']['status'], 'error')
        self.assertEqual(report['interfaces'], {})
        self.assertIn('连接失败', report['fatal_traceback'])
        self.assertTrue(list(path.glob('*.zip')))


if __name__ == '__main__':
    unittest.main()
