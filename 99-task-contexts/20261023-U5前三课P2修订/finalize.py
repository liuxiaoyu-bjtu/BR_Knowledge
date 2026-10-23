"""本轮收尾：润色、联动记录；不连接机器人，不覆盖真机输出。"""
from pathlib import Path
import copy
import difflib
import json
import re
import sys

from revise import ROOT, TASK, BASE, PROJ, NB, read, write, src, setcell, generator


def change_file(p, old, new):
    s = read(p)
    if old not in s:
        raise ValueError(f'{p}: 未找到待替换文本 {old[:70]!r}')
    write(p, s.replace(old, new))


def polish():
    paths = [next(NB.glob(f'U5-L{i}_*.ipynb')) for i in range(1, 4)]
    books = [json.loads(read(p)) for p in paths]
    b = books[0]
    s = src(b['cells'][23])
    s = s.replace('需要立即中止并清空队列时，用 `cancel()`。',
                  '需要立即中止并清空队列时，用 `cancel()`。这些含义见SDK的[播放流句柄说明](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/common-data-types/tasks-and-subscriptions/audio-playback-stream-handle/)。')
    setcell(b, 24, s)
    b = books[2]
    setcell(b, 7, src(b['cells'][6]).replace('下面使用默认配置体验。', '下面保留默认角色提示词，将音量设为0.6后体验。'))
    setcell(b, 13, src(b['cells'][12]).replace('### 3.1 音色与欢迎语配置', '### 3.1 对话配置').replace('ChatConfig 字段说明：\n-', 'ChatConfig 字段说明：\n\n-'))
    setcell(b, 24, src(b['cells'][23]).replace("print('请说出固定问题：请用一句话介绍一下机器人。')", 'print("请说出固定问题：", QUESTION)'))
    setcell(b, 31, src(b['cells'][30]).replace('| 自己写的那一版 | 　　　　 | 　　　　 | 　　　　 | 　　　 |\n###', '| 自己写的那一版 | 　　　　 | 　　　　 | 　　　　 | 　　　 |\n\n###'))
    for i, (p, b) in enumerate(zip(paths, books), 17):
        write(p, json.dumps(b, ensure_ascii=False, indent=1)+'\n')
        write(PROJ/f'_gen_L{i}.py', generator(p, b['cells']))
    duplicate = NB/'U5-L2/U5-L2_语音合成.ipynb'
    d = json.loads(read(duplicate))
    for c, master in zip(d['cells'], books[1]['cells']):
        c['source'] = copy.deepcopy(master['source'])
    write(duplicate, json.dumps(d, ensure_ascii=False, indent=1)+'\n')
    print('细节核对完成，主稿、发放副本和生成器已同步。')


def records():
    p = PROJ/'实验验证/U5-L1-L2-L3_P2复核与修改方案.md'
    s = read(p)
    s = s.replace('状态：**P2复核已完成，发现问题，待用户确认修改方案；尚未定稿，不进入P3。**',
                  '状态：**已按用户2026-10-23逐项反馈修订三课，待改码部分定向真机补验；P2尚未定稿，不进入P3。**')
    s = s.replace('本轮已从三课真机主稿反向同步生成器，未修改 Notebook 源内容、执行次数或输出；L2 发放目录和字体、脚本保持原状。用户认可下面方案后再改稿；涉及代码的项目另列补验，不把旧确认②延伸到新代码。',
                  '用户已授权直接修订。三课Notebook源内容、L2发放副本及sound_lab.py已修改，三个生成器按主稿反向同步；原执行次数、输出、metadata和cell id保留。L2字体与声音生成、绘图算法未改。下表保留复核问题及本轮处理，涉及代码的项目另列补验，不把旧确认②延伸到新代码。')
    s = s.replace('| 拟修改内容 |', '| 本轮修订内容 |')
    s = s.replace('多次水流类比和导览句增加阅读负担；“队列深，输入快慢都不会出问题”失实；“线路之一段时间”等错字',
                  '“队列深，输入快慢都不会出问题”失实；水流类比未说明暂存和等待条件；存在错字')
    s = s.replace('说明块、队列、输入和播放的关系；大队列只能容纳更多暂存，仍可能满；队列延迟由已积压音频长度等共同决定',
                  '按用户意见保留水流、杯子和暂存位置的比喻，补齐块、队列、输入和播放的对应关系；大队列仍可能满，实际等待与已积压音频有关')
    s = s.replace('说明及注释；不改采音参数或数量，无须为注释重做真机验证',
                  '保留采音参数和数量；增加累计字节与音频长度输出，补验时核对显示值')
    s = s.replace('取消合成任务后未核查终态，后续描述易将请求成功当结束',
                  '流式识别的观察窗口结束后未核查终态，易将取消请求成功当成已停止')
    s = s.replace('输出取消返回值，有限等待后核查`done()`/状态；若已成功完成，说明取消操作时机与实际结果，不能要求每次一定观察到`CANCELLING`',
                  '先合成并成功播放实训室提问，再启动识别；保留6秒观察窗口，取消后有限等待并检查终态；未结束时保留旧句柄并阻止重开')
    s = s.replace('正常完成、取消结果及不重复占用资源', '先播后听、取消结果及不重复启动')
    s = s.replace('第11格天气人设及相关说明', '第15格天气人设及相关说明')
    s = s.replace('示例提示词变化建议与下一项共同补验', '已换为给定资料的实训室讲解员，与下一项共同补验')
    s = s.replace('五处会话格及三人设循环的切换、中断、再次启动', '五处会话格及手动切换三种人设、中断、再次启动')
    s = s.replace('## 四、建议修改顺序与补验清单', '## 四、已完成修订与定向补验清单')
    start = s.index('建议确认上表后')
    end = s.index('## 五、', start)
    s = s[:start] + '''三课的文字、编号、表格、必要代码收尾已修订。无需为文字调整重做整课实验；以下格号按当前稿计数，补验时从前往后运行相应准备格。

| 课程 / 位置 | 补验操作 | 判断依据 |
|---|---|---|
| L1 第19、23格 | 采集20块、60块，查看总字节数与换算音频长度 | 按实际总字节数除以96000；若块均为3200字节，则约0.67秒、2秒。这是数据所含音频长度，不要求等于代码运行时间 |
| L1 第15、25格 | 有限音频播放；同批声音分别用队列4和64播放 | 写完后close再wait；成功才报告完成。记录写入总时间、完整性和返回状态，不预设大队列必然无等待 |
| L1 第31、33格 | 两次6秒识别观察，取消后检查状态，再重跑 | 6秒为观察窗口；检查done及真实状态。未终止时不新建任务，不把最近回调认定为最终整句 |
| L2 第9、12、16格及附件 | 试听自制声音、四种波形，查看中文图 | 正常播放才返回“播放完毕”；字体可用，声音算法不变。若未确认完成，附件报告实际状态 |
| L2 第21、26格 | 播放合成音频，换一个可用于合成的音色 | 成功状态对应完整播放；显示的是生成音频时长，不是合成耗时 |
| L2 第32格 | 提问播放完再识别；窗口结束取消；再次运行 | 前一任务未结束时不重开；播放失败时不进入识别；识别取消后核查终态 |
| L3 第11、15、26、28、30格 | 连续问答后中断；确认终态，再手动切换角色重跑 | 保留wait；口头打断只观察当前回答，中断按钮才进入取消流程。取消超时则保留task，暂不启动下一段会话 |
| L3 第24格 | 固定问题练习；取消识别后进入chat | 显示回调及最近文字；旧识别任务未结束时不能覆盖它开始聊天 |

不必人为制造服务故障。失败、超时等分支已用离线替身检查；真实设备上的正常播放、取消、中断和重开仍由用户补验。历史输出保留，可能与修订后的打印文案不同。

完成补验后再做P2定稿判断。当前未登记确认③通过，未启动P3。

''' + s[end:]
    s = s[:s.index('## 五、')] + '''## 五、同步与离线检查

- `_gen_L17.py`～`_gen_L19.py`按修改后的主稿逐格同步，未运行生成器覆盖Notebook。
- L2发放副本只同步源内容，分别保留两份Notebook各自的输出和执行次数；字体与音频生成、绘图算法保持原样。
- L1、L2用少量`try/finally`保证观察窗口或写入被中断时仍会请求取消或关闭输入；L3保留用户实测的`try/except KeyboardInterrupt`。这些结构只用于资源收尾，不扩展为异常处理课程，不引入U7线程或锁。
- 离线检查覆盖Notebook结构、Python语法、生成器与副本一致性、历史执行信息保留，以及播放成功/失败/超时、取消未终态防重复等分支。结果见[本轮执行记录](../../../../99-task-contexts/20261023-U5前三课P2修订/02-产出清单与状态日志.md)。离线替身只核对程序分支，不证明机器人已运行新代码。
'''
    write(p, s)

    p = PROJ/'实验验证/U5_语音SDK能力核验记录.md'
    s = read(p).replace('这项完善列入 P2 修改方案，不擅改已验证代码。',
                        '三课已按用户授权补上终态核查和防重复启动，保留原执行信息；新代码待定向补验。')
    heading = '## 三、哪些时间可以测，哪些不能这样测'
    section = '''### close与wait的顺序：依据方法定义

官方播放流类型文档明确写明：`close()`“结束写入；已写入的音频会继续播放直至播完”，`wait()`“阻塞等待播放任务进入终态；超时则返回当前状态”。因此，先close再wait有明确分工：前者通知输入结束，后者等待队列里的声音播完并检查结果。仅凭方法名称把close理解为立即停止播放，会误读这个接口。

| 顺序 | 含义与限制 |
|---|---|
| 写入 → close → wait | 没有后续输入，等待播放任务终态；只有SUCCEEDED表示成功播放 |
| 写入 → wait → close | 等待时输入仍开放，可能继续等待后续数据；有限wait返回可能只是超时，不能无条件报告播完 |
| cancel → wait | 请求中止播放并清空队列，再等待和确认终态；声音可能未完整播放 |

这项判断来自方法契约，尚未查看SDK实现源码。若真机行为与契约不一致，需记录SDK版本、调用顺序和返回状态后再核对。本轮不能据“close后还有wait”认定文档写错。

`AudioPlaybackStreamHandle`文档没有公开`status`、`error`或`done()`成员，不能照搬`TaskHandle`的检查写法。本轮通过`stream.wait(timeout=0.0)`取得播放流当前状态，判断旧任务是否进入终态。`TaskStatus`是str字面量类型别名，可直接比较`"SUCCEEDED"`等字符串。

L2附件本来就是close后wait，本轮保留顺序，补上失败和超时判断。L3的chat返回TaskHandle，没有close；继续用wait等待整个会话，中断后cancel并检查done，不用固定sleep猜测单轮结束。

### 单声道算例与三声道采音

按用户提供的K1环形三麦阵列信息，L1保持实测`channels=3`。对16 kHz、S16LE未压缩PCM，单声道为32000 B/s，三声道为96000 B/s；3200字节约含0.0333秒音频，20块约0.67秒，60块约2秒。各格用实际累计字节数换算，不能把代码运行时间当作音频长度。

`chunk_bytes`是总字节切块参数；3200不是三声道完整采样帧6字节的整数倍。文档未进一步说明其内部对齐处理，本轮保留用户实测参数，不擅自改块大小；补验时核对实际块大小、声音完整性和数据格式。L2自制提示音只生成单声道，播放也设channels=1，不因机器人有三麦就改成三声道。

'''
    if '### close与wait的顺序' not in s:
        s = s.replace(heading, section+heading)
    write(p, s)

    old = 'U5-L1～L3的P2复核已完成，发现问题，待用户确认修改方案，尚未定稿；保留确认②历史记录，现稿34/34/32格及L2附件未改，生成器已反向同步。'
    new = 'U5-L1～L3已按用户2026-10-23反馈完成P2修订，现稿34/34/32格；三声道换算、播放收尾、任务终态、表达与编号已调整，L2附件及发放副本、三个生成器已同步。保留确认②历史记录及原执行信息，改码部分待定向真机补验，P2尚未定稿。'
    shared = [ROOT/'AGENTS.md', BASE/'README.md', PROJ/'X课程开发计划-v4.md', BASE/'02_共创规则与上下文/notebook开发规则.md']
    for p in shared:
        change_file(p, old, new)
    change_file(PROJ/'X课程开发计划-v4.md',
                'U5-L1～L3已完成P2复核，具体修改方案待用户确认；保留用户真机稿、执行记录和L3的wait用法。确认后修订、同步并按清单补验，再判断是否定稿。',
                'U5-L1～L3已按用户反馈修订并同步；保留原执行记录及L3的wait用法。待播放收尾、识别取消与会话切换等改码部分定向补验后，再判断P2是否定稿。')
    p = BASE/'02_共创规则与上下文/notebook开发规则.md'
    s = read(p)
    lines = s.splitlines()
    details = {
        1: '单/三声道PCM换算、块与队列比喻、4/64对照、close后wait及识别取消终态已修订；保留三声道采音参数和历史输出。',
        2: '采样率与声波频率、音频时长、同步/异步及STEP编号已修订；附件播放增加终态检查，主稿与发放副本源内容一致，字体与音频算法未改。',
        3: '保留用户实测wait与KeyboardInterrupt收尾，补取消终态及防重复启动；改用给定资料的实训室人设，修订LLM表述、编号与记录表。',
    }
    names = ['语音识别', '语音合成', 'LLM对话']
    counts = [(34, 25, 9), (34, 23, 11), (32, 25, 7)]
    for j, line in enumerate(lines):
        for i in range(1, 4):
            if line.startswith(f'| `03_X课程项目/notebooks/U5-L{i}_'):
                b = json.loads(read(NB/f'U5-L{i}_{names[i-1]}.ipynb'))
                md = sum(c['cell_type']=='markdown' for c in b['cells'])
                code = len(b['cells'])-md
                lines[j] = f'| `03_X课程项目/notebooks/U5-L{i}_{names[i-1]}.ipynb` | U5·L{i} | 🟡 **确认②历史通过；P2修订完成、待定向补验（2026-10-23）** | 现稿{len(b["cells"])}格（{md} md/{code} code），原执行信息保留；`_gen_L{16+i}.py`按主稿同步。{details[i]}具体补验见`实验验证/U5-L1-L2-L3_P2复核与修改方案.md`。未登记③通过，未进入P3。 |'
    s = '\n'.join(lines)+'\n'
    anchor = '  - **QoS 的落点'
    i = s.index(anchor)
    s = s[:i] + '  - **语音与音频复核补充（2026-10-23）**：PCM字节与时长换算必须包含声道数；L1采音三声道，L2自制提示音单声道。播放流`close()`只结束输入，随后`wait()`等待播放终态；立即中止用`cancel()`。不把播放流误当成TaskHandle调用未公开的done/error/status。持续识别/对话取消后须确认终态，未结束时保留旧句柄；L3保留用户已实测的wait和中断收尾。三课本轮已修订，待定向补验。\n' + s[i:]
    write(p, s)

    p = ROOT/'INDEX.md'
    s = read(p).replace('（已复核，有问题待修改方案确认）', '（已按用户反馈修订，改码待定向补验，P2未定稿）')
    s = s.replace('X课程 语音SDK / TaskHandle / 持续会话 / 有限音频识别', 'X课程 语音SDK / TaskHandle / close与wait / PCM声道 / 持续会话 / 有限音频识别')
    write(p, s)
    p = NB/'_外挂附件清单.md'
    change_file(p, '已入库；用户于2026-10-22报告本课真机确认②完成', '已入库；确认②历史通过；2026-10-23补播放终态与超时判断，待定向补验')
    p = ROOT/'CHANGELOG.md'
    s = read(p)
    note = '''## 2026-10-23 · U5前三课按用户反馈完成P2修订

- 修改L1～L3学生Notebook，保留单元格结构、历史输出、执行次数、metadata及cell id；L2发放副本只同步源内容，三个生成器从主稿反向同步。
- L1补声道参数：16 kHz、S16LE的单声道32000 B/s、三声道96000 B/s；保留channels=3和3200字节块，修正音频长度估算。保留接水比喻，说明块与队列；整句/流式识别按语音留言、实时字幕等应用需要比较。
- 按播放流方法定义采用close结束输入、wait等待终态；成功才报告播完，超时保留句柄。L2附件原顺序保留，增加失败与超时判断；字体、生成与绘图算法未改。
- L3保留用户真机验证的wait和中断收尾；三课补取消后终态确认与防重复启动。修订LLM事实表述、给定资料的角色示例、音频时长文案及编号。未引入U7并发内容。
- 更新复核记录、SDK依据、导航与计划。改码部分待定向真机补验，P2未定稿；Git只作本地记录，推送由用户手动完成。

'''
    s = s.replace('# 更新日志\n\n', '# 更新日志\n\n'+note, 1)
    write(p, s)
    print('复核记录、SDK说明、附件清单、导航、计划和变更日志已同步。')


def shared_patch():
    paths = [ROOT/'AGENTS.md', ROOT/'INDEX.md', ROOT/'CHANGELOG.md', BASE/'README.md',
             PROJ/'X课程开发计划-v4.md', BASE/'02_共创规则与上下文/notebook开发规则.md']
    delta = []
    for p in paths:
        rel = p.relative_to(ROOT).as_posix()
        before = TASK/'before'/rel
        delta.extend(difflib.unified_diff(read(before).splitlines(True), read(p).splitlines(True), fromfile='a/'+rel, tofile='b/'+rel))
    write(TASK/'共享文档本轮增量.patch', ''.join(delta))
    print('共享文件本轮增量已保存；补丁用于审阅，不能再次应用到当前工作区。')


if __name__ == '__main__':
    {'polish': polish, 'records': records, 'shared-patch': shared_patch}[sys.argv[1]]()
