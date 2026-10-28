"""静态检查及替身分支测试；不导入真实SDK、不连接机器人。"""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
COURSE = ROOT/'05-internal-materials/vocational-planning/03_X课程项目'
NB = COURSE/'notebooks'
sys.path.insert(0,str(NB))
from x_lab import ball_position as geo, flows


def calibration():
    return geo.build_calibration([[20,20,.7,.3],[80,20,.7,-.3],
                                  [80,80,1.3,-.3],[20,80,1.3,.3]], [100,100], '替身测试姿态')


def verified():
    c=calibration()
    geo.verify_calibration(c,[[40,40,.9,.1],[60,50,1.,-.1],[50,60,1.1,0]],.001)
    return c


class Clock:
    def __init__(self): self.now=0
    def monotonic(self): self.now+=.01; return self.now
    def sleep(self,seconds): self.now+=seconds


class Manager:
    instances=[]
    fail_start=False
    fail_stop=False
    def __init__(self,robot): self.updates=[];self.stops=0;self.started=False;self.instances.append(self)
    def start(self):
        self.started=True
        if self.fail_start: raise RuntimeError('start失败替身')
    def update_command(self,**kwargs): self.command=kwargs
    def update_ball(self,x,y): self.updates.append((x,y))
    def stop(self):
        self.stops+=1
        if self.fail_stop: raise RuntimeError('stop失败替身')


def robot():
    count=[123]
    def get_image(**kwargs):
        count[0]+=1
        return types.SimpleNamespace(width=100,height=100,header=types.SimpleNamespace(timestamp=count[0]),to_numpy=lambda:None)
    return types.SimpleNamespace(get_mode=lambda:'walk',get_image=get_image,
                                 get_fall_down_state=lambda:types.SimpleNamespace(is_normal=True))


def target(name='Ball',score=.9):
    return types.SimpleNamespace(class_name=name,confidence=score,
                                 bbox=types.SimpleNamespace(center_x=50,center_y=45,height=10))


class GeometryChecks(unittest.TestCase):
    def test_independent_points(self):
        c=verified();self.assertTrue(c['verified'])
        x,y=geo.pixel_to_robot(c,50,50,[100,100])
        self.assertAlmostEqual(x,1);self.assertAlmostEqual(y,0)
    def test_left_positive(self):
        c=calibration();self.assertGreater(geo.pixel_to_robot(c,30,50,[100,100])[1],0)
    def test_outside_rejected(self):
        with self.assertRaises(ValueError):geo.pixel_to_robot(calibration(),5,50,[100,100])
    def test_resolution_rejected(self):
        with self.assertRaises(ValueError):geo.pixel_to_robot(calibration(),50,50,[200,100])
    def test_collinear_rejected(self):
        with self.assertRaises(ValueError):geo.build_calibration([[10,10,1,0],[20,20,2,0],[30,30,3,0],[40,40,4,0]],[100,100],'test')
    def test_reused_check_rejected(self):
        with self.assertRaises(ValueError):geo.verify_calibration(calibration(),[[20,20,.7,.3]]*3,.01)
    def test_three_copies_are_not_three_positions(self):
        with self.assertRaises(ValueError):geo.verify_calibration(calibration(),[[40,40,.9,.1]]*3,.01)
    def test_failure_resets_approval(self):
        c=verified();geo.verify_calibration(c,[[40,40,1.1,.1],[60,50,1.2,-.1],[50,60,1.3,0]],.01)
        self.assertFalse(c['verified'])
    def test_missing_does_not_become_center(self):self.assertIsNone(geo.select_ball([target('person')]))
    def test_best_of_same_class(self):
        good=target(score=.7)
        self.assertIs(geo.select_ball([target('person',.99),target(score=.3),good]),good)


class FlowChecks(unittest.TestCase):
    def setUp(self):
        Manager.instances=[];Manager.fail_start=False;Manager.fail_stop=False
        module=types.ModuleType('boosteros.robots.booster');module.SoccerKickManager=Manager
        self.sdk=patch.dict(sys.modules,{'boosteros.robots.booster':module});self.sdk.start()
        self.clock=patch.object(flows,'time',Clock());self.clock.start()
        self.session=flows.new_session(robot(),None)
        self.detector=types.SimpleNamespace(detect=lambda data:[target()])
    def tearDown(self):self.sdk.stop();self.clock.stop()
    def test_no_motion_without_calibration(self):
        reason,rows=flows.kick_window(self.session,self.detector,calibration())
        self.assertEqual(len(Manager.instances),0);self.assertEqual(rows,[])
    def test_ball_lost_before_start(self):
        self.detector.detect=lambda data:[]
        reason,_=flows.kick_window(self.session,self.detector,verified())
        self.assertIn('未检出',reason);self.assertFalse(Manager.instances)
    def test_window_and_release(self):
        reason,rows=flows.kick_window(self.session,self.detector,verified(),seconds=.5)
        self.assertGreater(len(rows),0);self.assertNotEqual(reason,'完成')
        self.assertEqual(Manager.instances[0].stops,1);self.assertFalse(self.session['kick_active'])
    def test_start_failure_still_stops(self):
        Manager.fail_start=True
        with self.assertRaises(RuntimeError):flows.kick_window(self.session,self.detector,verified())
        self.assertEqual(Manager.instances[0].stops,1);self.assertFalse(self.session['kick_active'])
    def test_stop_failure_keeps_flag(self):
        Manager.fail_stop=True
        with self.assertRaises(RuntimeError):flows.kick_window(self.session,self.detector,verified(),seconds=.2)
        self.assertTrue(self.session['kick_active']);self.assertFalse(flows.idle(self.session))
        self.assertTrue(flows.cleanup(self.session))
    def test_detection_error_stops(self):
        calls=[]
        def detect(data):
            calls.append(1)
            if len(calls)>1:raise RuntimeError('推理异常替身')
            return [target()]
        self.detector.detect=detect
        with self.assertRaises(RuntimeError):flows.kick_window(self.session,self.detector,verified())
        self.assertEqual(Manager.instances[0].stops,1)
    def test_loss_after_start_stops(self):
        calls=[]
        def detect(data):calls.append(1);return [target()] if len(calls)==1 else []
        self.detector.detect=detect
        reason,_=flows.kick_window(self.session,self.detector,verified())
        self.assertIn('未检出',reason);self.assertEqual(Manager.instances[0].stops,1)
    def test_existing_motion_blocks(self):
        self.session['motion_task']=types.SimpleNamespace(done=lambda:False)
        reason,_=flows.kick_window(self.session,self.detector,verified())
        self.assertIn('旧任务',reason);self.assertFalse(Manager.instances)
    def test_repeated_source_stops(self):
        frozen=robot().get_image()
        self.session['robot'].get_image=lambda **kwargs:frozen
        reason,rows=flows.kick_window(self.session,self.detector,verified())
        self.assertIn('时间戳未更新',reason);self.assertEqual(rows,[])
        self.assertEqual(Manager.instances[0].stops,1)
    def test_wait_timeout_not_success(self):
        class Task:
            status='RUNNING'
            def wait(self,timeout):return self.status
            def done(self):return self.status=='CANCELLED'
            def cancel(self):self.status='CANCELLED'
        reason=flows._wait_task(Task(),.1)
        self.assertIn('等待上限',reason);self.assertNotEqual(reason,'完成')


class ProjectChecks(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('team_test',NB/'u8_team_template.py')
        self.team=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.team)
        self.team.THEME='导览';self.team.STEPS=['观察','介绍','再观察','致意']
        self.team.INTRODUCTION='测试文字';self.team.GREET_ID='真实ID由现场填写'
    def test_unfilled_template_refuses(self):
        self.team.STEPS=[];self.assertTrue(self.team.validate())
    def test_invalid_order(self):
        self.team.STEPS=['介绍','观察','再观察','致意'];self.assertTrue(self.team.validate())
    def test_failure_blocks_later_steps(self):
        with patch.object(self.team,'idle',return_value=True),patch.object(self.team,'observe',return_value='未检出'):
            rows=self.team.run_project({}, {}, None)
        self.assertEqual(rows[0]['result'],'未检出')
        self.assertEqual([r['result'] for r in rows[1:]],['未执行']*3)
    def test_exception_keeps_partial_log(self):
        with patch.object(self.team,'idle',return_value=True),patch.object(self.team,'observe',side_effect=RuntimeError('调用异常')):
            rows=self.team.run_project({}, {}, None)
        self.assertIn('本步异常',rows[0]['result']);self.assertEqual(rows[-1]['result'],'未执行')
    def test_configuration_failure_keeps_external_log(self):
        self.team.STEPS=[]
        log=[]
        self.assertIs(self.team.run_project({}, {}, None, log), log)
        self.assertEqual(log[0]['step'],'配置检查')
    def test_transport_error_is_logged_and_blocks_later_steps(self):
        with patch.object(self.team,'idle',return_value=True),patch.object(self.team,'observe',side_effect=OSError('连接异常')):
            rows=self.team.run_project({}, {}, None)
        self.assertIn('连接异常',rows[0]['result'])
        self.assertEqual(rows[-1]['result'],'未执行')


def static_checks():
    manifest=[]
    for number in range(25,33):
        gen=COURSE/f'_gen_L{number}.py'
        tree=ast.parse(gen.read_text(encoding='utf-8'))
        payload=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='NOTEBOOK' for x in node.targets))
        name=''.join(payload['cells'][0]['source']).splitlines()[0].replace('# ','').replace('：','_',1)
        # 文件实际名称允许标题和主题略有差别，直接按课程编号定位主稿。
        candidates=list(NB.glob(f'U{7 if number<29 else 8}-L{(number-25)%4+1}_*.ipynb'))
        if len(candidates)!=1:raise AssertionError(('主稿数量',number,[p.name for p in candidates]))
        p=candidates[0];nb=json.loads(p.read_text(encoding='utf-8'))
        assert nb==payload,('生成器不一致',p.name)
        assert len({c['id'] for c in nb['cells']})==len(nb['cells'])
        for i,c in enumerate(nb['cells'],1):
            assert isinstance(c['source'],list)
            if c['cell_type']=='code':
                assert c['outputs']==[] and c['execution_count'] is None
                ast.parse(''.join(c['source']),filename=f'{p.name}:cell{i}')
        manifest.append({'file':p.name,'cells':len(nb['cells']),
                         'code_cells':sum(c['cell_type']=='code' for c in nb['cells'])})
    baseline=json.loads((Path(__file__).parent/'基线.json').read_text(encoding='utf-8'))
    for rel,h in baseline['protected'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h,rel
    for p in (NB/'x_lab').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
    return manifest


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    manifest=static_checks()
    out={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
         'notebooks':manifest,'protected_unchanged':True,'robot_executed':False}
    (Path(__file__).parent/'离线核查结果.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if not result.wasSuccessful():raise SystemExit(1)
