from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划/图示'
OUT.mkdir(exist_ok=True)

STYLE = '''
graph [bgcolor="white", pad="0.35", nodesep="0.35", ranksep="0.48", fontname="Microsoft YaHei", fontsize=18, labelloc=t];
node [fontname="Microsoft YaHei", fontsize=13, shape=box, width=3.7, height=0.85, fixedsize=true, style="filled", fillcolor="#EFF6FC", color="#3C6485", penwidth=1.4, margin="0.18,0.10"];
edge [fontname="Microsoft YaHei", fontsize=11, color="#536C7D", arrowsize=0.7, penwidth=1.2];
'''


def sub(name, text):
    # 预定义过程：外框内增加两条竖线；不使用双重完整边框冒充。
    return f'''{name} [shape=plain, fixedsize=false, label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="9" BGCOLOR="#EAF6F3" COLOR="#3C7C6E"><TR><TD WIDTH="8" BORDER="1" SIDES="R"></TD><TD WIDTH="240" HEIGHT="62">{text}</TD><TD WIDTH="8" BORDER="1" SIDES="L"></TD></TR></TABLE>>];'''


diagrams = {}
diagrams['01_主流程'] = '''digraph main {
''' + STYLE + '''
label="K1 足球应用主流程｜先转头，再转身";
start [shape=oval, fillcolor="#DCEEEA", label="开始"];
read [shape=parallelogram, label="读取教师配置与任务参数"];
ready [shape=diamond, fillcolor="#FFF4DC", label="启用运动且\n条件已核实？"];
observe [shape=parallelogram, label="只输出检测和定位状态"];
prep [label="停止普通移动\n设置本轮头部观察点"];
''' + sub('head', '转头、等待停稳<BR/>取得新图并检测') + '''
seen [shape=diamond, fillcolor="#FFF4DC", label="检测到\n所选足球？"];
points [shape=diamond, fillcolor="#FFF4DC", label="本轮头部\n观察点已用完？"];
next [label="选择下一个头部观察点"];
budget [shape=diamond, fillcolor="#FFF4DC", label="仍有搜索时间\n和转身次数？"];
turn [label="按里程计转过一个扇区\n停止、等待停稳，重置观察点"];
''' + sub('locate', '计算当前身体球位<BR/>详见球位处理子流程') + '''
valid [shape=diamond, fillcolor="#FFF4DC", label="球位有效\n且足够新？"];
retry [shape=diamond, fillcolor="#FFF4DC", label="定位等待\n尚未超时？"];
near [shape=diamond, fillcolor="#FFF4DC", label="进入已核实的\n踢球交接范围？"];
step [label="发送一次有期限的接近指令\n到时零速度，停稳后重新观察"];
kickok [shape=diamond, fillcolor="#FFF4DC", label="本次启用踢球且\n持续供数已核实？"];
hold [shape=parallelogram, label="记录：到达交接范围\n未启用自动踢球"];
''' + sub('kick', '停止普通速度发送<BR/>开启管理器并持续更新球位') + '''
''' + sub('verify', '关闭管理器、请求停止<BR/>重新观察并判断结束原因') + '''
record [shape=parallelogram, label="保存状态、输入来源和现场结果"];
end [shape=oval, fillcolor="#DCEEEA", label="结束"];
start -> read -> ready;
ready -> observe [label="否"]; observe -> record;
ready -> prep [label="是"]; prep -> head -> seen;
seen -> points [label="否"];
points -> next [label="否"]; next -> prep;
points -> budget [label="是"];
budget -> turn [label="是"]; turn -> prep;
budget -> record [label="否"];
seen -> locate [label="是"]; locate -> valid;
valid -> retry [label="否"]; retry -> head [label="是：保持当前观察点"];
retry -> prep [label="否：重新搜索"];
valid -> near [label="是"];
near -> step [label="否"]; step -> head;
near -> kickok [label="是"];
kickok -> hold [label="否"]; hold -> record;
kickok -> kick [label="是"]; kick -> verify -> record -> end;
note [shape=note, fillcolor="#FAFAFA", color="#A9B4BC", fontsize=11,
label="任意活动阶段收到停止请求、异常或达到总时限/累计里程限制：\n进入统一退出；活动中的踢球管理器先关闭。\n图中双侧竖线表示子流程；菱形分支标明条件结果。"];
{rank=same; record; note;}
}
'''

diagrams['02_球位处理子流程'] = '''digraph locate {
''' + STYLE + '''
label="球位处理子流程｜保留拍摄时刻，输出当前身体坐标";
start [shape=oval, fillcolor="#DCEEEA", label="进入球位处理"];
read [shape=parallelogram, label="读取原图、检测框、匹配深度\n内参、拍摄时TF和里程计"];
check [shape=diamond, fillcolor="#FFF4DC", label="坐标、时钟、内参与\n数据对应关系有效？"];
depth [shape=diamond, fillcolor="#FFF4DC", label="已配准深度可用\n且球面拟合通过？"];
deproject [label="反投影并估计相机球心\n变换到拍摄时身体坐标"];
geometry [shape=diamond, fillcolor="#FFF4DC", label="已核实几何模型\n且处于停稳观察？"];
ray [label="接地点射线与真实地面求交\n按半径、地面法向修正到球心"];
odom [label="球位转换到odom\n按当前机器人位姿重新表达"];
age [shape=diamond, fillcolor="#FFF4DC", label="年龄、范围和\n使用场景均允许？"];
ok [shape=parallelogram, fillcolor="#EAF6F3", label="输出 valid=true\nx、y：当前身体坐标，单位米\n保留原始拍摄时间与方法"];
bad [shape=parallelogram, fillcolor="#FFF0ED", label="输出 valid=false 与原因\n禁止生成可控制的假坐标"];
end [shape=oval, fillcolor="#DCEEEA", label="返回调用方"];
start -> read -> check;
check -> depth [label="是"]; check -> bad [label="否"];
depth -> deproject [label="是"]; depth -> geometry [label="否"];
geometry -> ray [label="是"]; geometry -> bad [label="否"];
deproject -> odom; ray -> odom; odom -> age;
age -> ok [label="是"]; age -> bad [label="否"];
ok -> end; bad -> end;
note [shape=note, fillcolor="#FAFAFA", color="#A9B4BC", fontsize=11,
label="固定地面模型只供已核实的停稳观察。\n本版自动踢球要求已核实的动态深度供数。\nodom只补偿自身运动；原始观测年龄不归零。"];
{rank=same; age; note;}
}
'''

diagrams['03_模块框架'] = '''digraph architecture {
''' + STYLE + '''
rankdir=TB;
label="应用框架｜机器人访问统一经过公开OS SDK";
student [label="U7 Notebook / 后续U8应用\n选择参数 · 启停 · 查看状态 · 解释结果", fillcolor="#E8F0FC"];
profile [shape=note, label="教师配置JSON\n坐标定义、定位条件、实测依据", fillcolor="#FFF4DC"];
subgraph cluster_module {
 label="课程附件 k1_soccer.py（单个运行文件）"; fontsize=14; color="#77A89C"; style="rounded";
 api [label="SoccerApp\nstart / status / stop / save_log", fillcolor="#EAF6F3"];
 subgraph cluster_read {label="采集与推理线程"; fontsize=14; color="#D2DFE8";
 buffer [label="有界图像缓存\n按原图时间匹配元数据"];
 target [label="目标筛选与连续性选择"];
 math [label="球位几何 / 深度球心\n时间补偿与有效性判断"];
 buffer -> target -> math;
 }
 subgraph cluster_control {label="独立控制线程"; fontsize=14; color="#D2DFE8";
 state [label="SoccerPlanner 状态机\n先头后身 · 观察后短步接近"];
 owner [label="唯一身体命令出口\n普通速度 / 踢球管理器互斥"];
 exit [label="退出处理与结果记录\nSDK返回与物理结果分别保存"];
 state -> owner -> exit;
 }
 api -> buffer; api -> state; math -> state [label="有效球位快照"];
}
sdk [width=4.6, height=1.45, label="BoosterOS SDK（现有公开接口）\n图像、内参、TF、里程计、关节信息\nDetection / set_head_angle\nset_velocity / SoccerKickManager", fillcolor="#E8F0FC"];
robot [label="K1传感器、运控与视觉踢球", fillcolor="#EDEFF2"];
student -> api; profile -> api [style=dashed, label="配置"];
buffer -> sdk [dir=both, label="读取"]; target -> sdk [dir=both, label="检测"];
owner -> sdk [label="控制"]; sdk -> robot [dir=both];
}
'''

diagrams['04_状态转换'] = '''digraph states {
''' + STYLE + '''
graph [rankdir=LR, ranksep="0.8", nodesep="0.35"];
label="运行状态转换｜状态图，不套用流程图符号";
node [shape=box, style="rounded,filled"];
initial [shape=point, label="", fillcolor="#263A49", width=.12];
idle [label="IDLE\n已创建，尚未启动"];
observe [label="OBSERVE_ONLY\n只观察，不发送动作"];
head [label="HEAD_SEARCH\n头部定点扫描"];
localize [label="LOCALIZE\n保持视线、确认球位"];
turn [label="BODY_TURN\n按里程计转身"];
approach [label="APPROACH\n一次有期限的接近"];
settle [label="SETTLE\n零速度、等待停稳"];
kick [label="KICK\n管理器拥有身体控制"];
verify [label="VERIFY\n关闭后重新观察"];
finished [label="FINISHED\n有明确结束原因"];
stopping [label="STOPPING\n线程或SDK调用尚未退出", fillcolor="#FFF4DC"];
stopped [label="STOPPED / ERROR\n已退出 / 有调用异常", fillcolor="#FFF0ED"];
terminal [shape=doublecircle, label="", width=.22, fillcolor="#263A49"];
initial -> idle;
idle -> observe [label="start：只观察"];
idle -> head [label="start：运动条件通过"];
head -> localize [label="检测到所选球"];
head -> turn [label="头部扫描完，仍可搜索"];
turn -> settle [label="扇区到位"];
settle -> head [label="转身后停稳"];
localize -> head [label="定位等待超时"];
localize -> approach [label="有效且尚未到交接范围"];
approach -> settle [label="本次动作到时"];
settle -> localize [label="接近后停稳"];
localize -> kick [label="已到范围、启用踢球、供数合格"];
localize -> finished [label="交接条件未满足"];
head -> finished [label="搜索次数或总预算耗尽"];
kick -> verify [label="移动 / 失效 / 超时"];
verify -> finished [label="得到新观察或复核超时"];
observe -> stopping [label="stop / 总时限 / 异常"];
head -> stopping [style=dashed, label="停止或异常"];
kick -> stopping [style=dashed, label="停止请求"];
stopping -> stopped [label="控制与推理线程均退出"];
finished -> terminal; stopped -> terminal;
}
'''

for name, source in diagrams.items():
    # WASM版Graphviz不包含中文字体宽度表，显式给节点留足文字尺寸。
    source = source.replace('shape=diamond,', 'shape=diamond, width=4.8, height=1.45,')
    source = source.replace('shape=oval,', 'shape=oval, width=2.6, height=0.65,')
    source = source.replace('shape=note,', 'shape=note, width=4.6, height=1.4,')
    if name == '04_状态转换':
        source = source.replace('rankdir=LR', 'rankdir=TB')
    (OUT / f'{name}.dot').write_text(source, encoding='utf-8')
print('wrote', len(diagrams), 'DOT sources to', OUT)
