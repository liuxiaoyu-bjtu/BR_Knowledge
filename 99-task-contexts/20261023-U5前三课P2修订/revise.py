"""按用户2026-10-23反馈逐格修订；保留真机输出，不连接机器人。"""
from pathlib import Path
import ast
import copy
import hashlib
import json
import re
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
BASE = ROOT / '05-internal-materials/vocational-planning'
PROJ = BASE / '03_X课程项目'
NB = PROJ / 'notebooks'

def read(p):
    return p.read_text(encoding='utf-8')

def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8', newline='\n')

def src(c):
    return c['source'] if isinstance(c['source'], str) else ''.join(c['source'])

def backup(p):
    b = TASK / 'before' / p.relative_to(ROOT)
    if not b.exists():
        b.parent.mkdir(parents=True, exist_ok=True)
        b.write_bytes(p.read_bytes())

def setcell(nb, index, s):
    nb['cells'][index-1]['source'] = (s.strip()+'\n').splitlines(keepends=True)

def replace(nb, index, old, new):
    s = src(nb['cells'][index-1])
    if old not in s:
        raise ValueError((index, old))
    setcell(nb, index, s.replace(old, new))

def generator(p, cells):
    body = [f'"""{p.stem}：按 2026-10-23 修订后的学生 Notebook 反向同步。',
            'Notebook 为主稿；重建将清空输出，不用于覆盖用户真机记录。"""',
            'import json', 'from pathlib import Path',
            f'OUT = Path(__file__).resolve().parent / "notebooks" / {p.name!r}',
            'def md(s):', '    return {"cell_type": "markdown", "metadata": {}, "source": s.splitlines(keepends=True)}',
            'def code(s):', '    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.splitlines(keepends=True)}',
            'cells = []']
    for c in cells:
        body.append(f'cells.append({"md" if c["cell_type"] == "markdown" else "code"}({src(c)!r}))')
    body += ['if __name__ == "__main__":',
             '    notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}',
             f'    OUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + {chr(10)!r}, encoding="utf-8")',
             '    print(OUT)', '']
    return '\n'.join(body)

def listen_code(start, setup=''):
    return setup + '''if "task" in globals() and not task.done():
    print("上一项语音任务尚未结束，状态：", task.status)
    print("先运行 task.cancel()，再运行 task.wait(timeout=5.0)，确认 task.done() 为 True 后重试。")
else:
    task = speech.recognize_stream(on_result=on_text)
    print(START_MESSAGE)
    try:
        time.sleep(6)  # 留出6秒供观察文字回调，不代表识别一句话需要6秒
    finally:
        accepted = task.cancel()
        print("取消请求已提交：", accepted)
        task.wait(timeout=5.0)
    print("当前状态：", task.status, "；是否已结束：", task.done())
    if not task.done():
        print("任务尚未结束，保留 task，继续检查；暂不启动下一次识别或对话。")
    elif task.status == "FAILED":
        print("任务失败：", task.error)
'''.replace('START_MESSAGE', repr(start))

def chat_code(call, pre=''):
    # 每格保留显式wait和KeyboardInterrupt，不隐藏为学生尚未学习的会话框架。
    return pre + '''if "task" in globals() and not task.done():
    print("上一项语音任务尚未结束，状态：", task.status)
    print("先运行 task.cancel()，再运行 task.wait(timeout=5.0)，确认 task.done() 为 True 后重试。")
else:
CALL
    try:
        print("语音对话已启动，按 Ctrl+C 或 Notebook 的中断按钮结束本次会话。")
        task.wait()  # 等待整个会话结束，不是只等机器人回答一句话
    except KeyboardInterrupt:
        accepted = task.cancel()
        print("取消请求已提交：", accepted)
        task.wait(timeout=5.0)
    print("当前状态：", task.status, "；是否已结束：", task.done())
    if not task.done():
        print("任务尚未结束，保留 task 并继续检查；暂不启动下一段对话。")
    elif task.status == "FAILED":
        print("会话失败：", task.error)
'''.replace('CALL', '\n'.join('    '+s if s else '' for s in call.splitlines()))

def build():
    paths = [next(NB.glob(f'U5-L{i}_*.ipynb')) for i in range(1,4)]
    duplicate = NB / 'U5-L2/U5-L2_语音合成.ipynb'
    extra = NB / 'U5-L2/sound_lab.py'
    shared = [ROOT/'AGENTS.md', ROOT/'INDEX.md', ROOT/'CHANGELOG.md', BASE/'README.md',
              PROJ/'X课程开发计划-v4.md', BASE/'02_共创规则与上下文/notebook开发规则.md',
              NB/'_外挂附件清单.md']
    for p in paths+[duplicate, extra]+shared+[PROJ/f'_gen_L{i}.py' for i in (17,18,19)]+[
        PROJ/'实验验证/U5-L1-L2-L3_P2复核与修改方案.md', PROJ/'实验验证/U5_语音SDK能力核验记录.md']:
        backup(p)
    books = [json.loads(read(p)) for p in paths]
    b = books[0]
    setcell(b, 1, '''# U5-L1：语音识别

**课程目标**

1. 能区分录音与语音识别的输入、输出：录音得到声音的采样数据，语音识别将语音转成文字；转成文字后还需要结合语境理解意思。
2. 能说明采样率、声道数和采样格式的含义，并用它们估算 PCM 数据量与音频长度。
3. 能说明播放队列如何暂存声音块，比较不同队列容量下的写入等待与播放现象。
4. 能比较整句识别与流式识别的适用场景，并启动、观察和停止流式识别任务。''')
    setcell(b, 2, '''## 一、本课要解决的问题

前面我们用视觉和运动接口，让机器人发现来宾、转向来宾，并尝试接近来宾。

如果还要与来宾交流，程序就需要取得来宾说话的内容。本课先研究麦克风采到什么，再让机器人把一句话转成文字。

> **装上麦克风后，机器人怎样把声音变成文字？**''')
    setcell(b, 3, '''## 二、麦克风采集的声音

麦克风可以比作机器人的耳朵。它感知空气中声压的变化，音频采集系统再把这些变化转换为数字数据。说话声、脚步声、周围的噪声，都可能被采集下来。

程序通过录音接口取得这些数据。麦克风本身不会判断一句话说了什么。''')
    setcell(b, 4, '''### 2.1 麦克风采集声音数据的原理

声音在空气中传播时会引起声压变化，麦克风把这种变化转为电信号。音频采集系统每隔一小段时间量一次信号，按顺序记录数值，就得到一段音频数据。这种按时间取数的过程叫**采样**。

读懂这段数据，需要看三个参数：

- **采样率（sample_rate）**：每个声道一秒采样多少次。16000 Hz 表示每个声道每秒采样16000次，是语音处理中常见的设置。
- **声道数（channels）**：同时记录几路声音数据。单声道记录一路；三声道记录三路，每一路都有自己的采样数值。
- **采样格式（sample_format）**：每个采样数值怎么存。`S16LE` 表示用16位有符号整数、小端顺序存储，每个数占2字节。

先按**单声道**来算：一秒采样16000次、每次记2字节，共 `16000 × 1 × 2 = 32000` 字节。

本课使用的K1有环形三麦克风阵列，后面的采音代码设置 `channels=3`。同样的一秒声音需要记录三路数据，因此是 `16000 × 3 × 2 = 96000` 字节。声道增加不会把这段声音变长，增加的是同一段时间内记录的数据量。

对于本课使用的未压缩 `S16LE PCM` 数据：

```text
数据量（字节） = 时长（秒） × 采样率 × 声道数 × 2
音频长度（秒） = 数据量（字节） ÷（采样率 × 声道数 × 2）
```

这个公式计算音频采样数据，不包含WAV等文件的文件头，也不适用于MP3等压缩数据。采样数据记录的是声音变化，其中还没有文字。''')
    setcell(b, 5, '''### 2.2 实践：调用麦克风采集一段声音

1. 调用 `start_recording()` 开始录音，采到的数据暂存在内存里。
2. 调用 `stop_recording()` 停止录音，返回一个 `AudioData` 对象，包含音频数据及其格式信息。
3. 需要保存为文件时，再调用这个对象的 `save(path)`。

如果已经调用 `start_recording()`，但尚未调用 `stop_recording()`，再次开始录音会出错。可用 `is_recording()` 检查当前状态；若上一次还在录音，先停止，再运行下一次录音。

录制过程中，`get_recording_duration()` 可查询已经录了多少秒。''')
    replace(b, 6, '连接机器人，确认音量，让它站好', '连接机器人，确认音量')
    setcell(b, 10, '''### 2.3 录制的音频数据里有什么

`stop_recording()` 返回的 `AudioData` 把声音数据和格式信息放在一起：

- `data`：音频字节数据，本次录音为PCM数据；
- `duration`：音频时长，类型是 `Duration`，用 `duration.seconds` 取秒数；
- `sample_rate`、`channels`、`sample_format`：采样率、声道数、采样格式。

调用 `audio.save(path)` 可以保存到文件，`path` 是文件路径字符串，支持 `.wav`、`.pcm` 或 `.mp3` 后缀。本课保存为WAV文件。''')
    setcell(b, 13, '''### 2.4 放出来听听

调用 `robot.play_sound(audio, volume=0.5)` 可以启动播放，`volume` 要用参数名指定，范围为 `0.0`～`1.0`。

本课会使用两种常见输入：内存里的 `AudioData`，或已保存的音频文件路径。下面先播放刚保存的文件。

`play_sound()` 会立即返回任务句柄，声音在后台播放。调用这个句柄的 `wait()`，当前代码才会等待播放任务结束。声音可以在没有 `wait()` 时播放；等待的作用是让后续操作按顺序进行。还要查看任务状态，才能区分播放成功、失败或取消。''')
    setcell(b, 15, '''playback = robot.play_sound(save_path)
playback_status = playback.wait()
if playback_status == "SUCCEEDED":
    print(f"文件 {save_path} 播放完成")
else:
    print("播放未成功，状态：", playback_status, "；错误：", playback.error)''')
    setcell(b, 16, '''## 三、声音数据的分块读取

刚才先录3秒，再取得整段声音。如果要持续接收声音，一直等到录音结束才处理，就无法及时显示字幕。

可以把持续输入的声音比作水龙头流出的水：用杯子一杯杯接，每接好一杯就处理一杯。程序也可以每次取得一小块声音，逐块处理，不必等整段录音结束。''')
    setcell(b, 17, '''### 3.1 分块读取

`record_stream()` 返回一个迭代器。在 `for` 循环中，每次取得一个 `AudioData` 声音块，就像接好的一杯水。

`chunk_bytes` 指定每块的字节数。本课保持 `sample_rate=16000`、`channels=3`、`sample_format="S16LE"`，每秒共96000字节。因此，3200字节约对应 `3200 ÷ 96000 ≈ 0.033` 秒的声音。这里要把三路数据一起计算，不能套用单声道的0.1秒。

`stop_event` 接收一个停止标志。下面用 `threading.Event()` 建立标志，调用它的 `set()` 通知采音循环停止。本课只把它当作停止开关使用。

块的实际长度可用 `len(chunk.data)` 查看。将所有块的字节数相加，再按格式换算，得到的是这些数据所包含的音频长度；程序运行时间还包括启动、传输和输出等时间。''')
    setcell(b, 18, '''**STEP 05：** 一块一块地读麦克风

这一格取得20块声音。按每块3200字节估算，音频长度约0.67秒；它与代码格运行时间可能不同。声音片段很短，说一个字或轻拍一下手，观察块数和字节数。''')
    setcell(b, 19, '''import threading

stop_flag = threading.Event()
count = 0
total_bytes = 0

for chunk in robot.audio_manager.record_stream(channels=3, chunk_bytes=3200, stop_event=stop_flag):
    count += 1
    total_bytes += len(chunk.data)
    if count % 5 == 0:
        print(f"第 {count} 块，本块 {len(chunk.data)} 字节")
    if count >= 20:
        stop_flag.set()

audio_seconds = total_bytes / (16000 * 3 * 2)
print(f"读完，共 {count} 块、{total_bytes} 字节，约含 {audio_seconds:.3f} 秒音频")''')
    setcell(b, 20, '''### 3.2 流式播放与队列

`record_stream()` 一块块读入声音，`play_stream()` 则允许一块块写入声音并播放。

- `play_sound()`：把已有的整段音频交给它播放。
- `play_stream()`：创建播放流，再用 `write(chunk)` 逐块交入格式一致的音频。

继续用接水作比喻：输入端负责把一杯杯水送来，播放端按自己的速度取走。送来得快了，需要先放在一排暂存位置上。这些位置就是**队列**，每个位置暂存一个声音块。

- `queue_size`：队列最多暂存几块，默认64，必须大于0。
- `overflow`：队列满后的处理方式。`"block"` 让当前写入等待空位；`"drop_oldest"` 丢弃队列里最旧的块；`"drop_newest"` 丢弃新送来的块。

一次写入返回，只能说明这次提交已处理，声音可能仍在队列里等待播放。''')
    setcell(b, 21, '''### 3.3 队列的深浅

暂存位置多，可以容纳更多声音块；位置少，较快就会排满。

- **浅队列**：暂存量较少。选择 `overflow="block"` 时，输入较快就可能需要等待；选择丢弃策略时，可能损失声音块。
- **深队列**：可以吸收更大的一阵输入。若输入持续快于播放，仍会排满；已经排在前面的声音越多，新块等待播放的时间通常越长。

例如本课每块约0.033秒，队列里若已有30块待播放，单是这些声音就约有1秒。队列容量大，并不表示每次都会填满，也不能仅凭容量推算实际延迟。

队列容量和溢出策略共同影响等待与数据完整性。这类选择属于 **QoS（服务质量）** 的设置。实时字幕和完整录音对“及时”和“保留数据”的要求可能不同，要按任务选择。''')
    setcell(b, 22, '''**STEP 06：** 采集一段声音，把声音块存到列表

本次先录后放，便于分别观察采集和播放。下面存60块，按当前参数约含2秒音频，可以说一句简短的话。录音结束后，用同一批块比较两种队列容量。''')
    replace(b, 23, 'if count >= 60:                   # 约 6 秒', 'if count >= 60:                   # 三声道下约含2秒音频')
    replace(b, 23, 'print(f"录制完成，共 {count} 块")', '''total_bytes = sum(len(chunk.data) for chunk in chunks)
audio_seconds = total_bytes / (16000 * 3 * 2)
print(f"录制完成，共 {count} 块、{total_bytes} 字节，约含 {audio_seconds:.3f} 秒音频")''')
    old24 = src(b['cells'][23])
    examples = re.findall(r'```markdown\n(.*?)```', old24, re.S)
    historical = '\n\n'.join('```text\n'+e.strip()+'\n```' for e in examples)
    setcell(b, 24, '''**STEP 07：** 用同一批声音块比较队列容量

先用 `queue_size=4` 运行下一格，确认播放任务结束后，再改成64重跑；录音块保持不变，`overflow` 都设为 `"block"`。

记录全部块写入所用的总时间，并听声音是否完整、有无卡顿。小队列通常更容易出现明显的写入等待；大队列可能较快接收完这批块，但接收完不等于播放完。每次函数调用都有开销，不能把微小的非零耗时直接当作队列阻塞。

写完后按以下顺序收尾：

```python
stream.close()                 # 后面不再写入，已排队的声音继续播放
status = stream.wait(timeout=10.0)  # 等待整个播放任务结束，或超时返回当前状态
```

`close()` 可以比作通知播放端“这是最后一杯，后面没有了”，不表示把已排队的声音倒掉。若先 `wait()`，流仍可能等待后续输入，不能据此确认整段播放完成。需要立即中止并清空队列时，用 `cancel()`。

`wait()` 返回后，`SUCCEEDED` 才表示播放成功；`FAILED`、`CANCELLED` 分别表示失败和取消；其余状态表示还没有结束。超时不会自动取消任务。若仍未结束，可运行 `stream.cancel()`，再用 `stream.wait(timeout=5.0)` 检查，暂不创建下一条播放流。

下面保留原真机实验的两组输出，分别对应容量4和64，仅供比较写入耗时。原输出末行“播放结束”是旧程序直接打印的，不能作为任务成功的证据；修订后的代码会显示等待返回的真实状态。

'''+historical)
    setcell(b, 25, '''import time

queue_size = 4  # 第一组为4；播放结束后改为64，再运行本格
terminal_states = ("SUCCEEDED", "FAILED", "CANCELLED")

if "stream" in globals() and stream.wait(timeout=0.0) not in terminal_states:
    print("上一条播放流尚未结束。请保留 stream，先取消并等待结束，再重试。")
else:
    stream = robot.audio_manager.play_stream(channels=3, queue_size=queue_size, overflow="block")
    print("开始写入播放流...")
    start_time = time.perf_counter()
    try:
        for i, chunk in enumerate(chunks):
            write_start = time.perf_counter()
            stream.write(chunk)
            write_time = time.perf_counter() - write_start
            if (i + 1) % 10 == 0:
                print(f"  已写入 {i + 1}/{len(chunks)} 块，本次写入耗时 {write_time * 1000:.1f} ms")
        print(f"全部块写入耗时：{time.perf_counter() - start_time:.3f} 秒")
    finally:
        stream.close()  # 结束输入，排队的音频继续播放
    playback_status = stream.wait(timeout=10.0)
    if playback_status == "SUCCEEDED":
        print("播放完成，状态：", playback_status)
    elif playback_status in terminal_states:
        print("播放未成功，状态：", playback_status)
    else:
        print("等待超时，播放任务尚未结束，状态：", playback_status)
        print("保留 stream 继续检查；暂不运行下一组。")''')
    setcell(b, 26, '''## 四、从声音到文字

录音得到了声音的采样数据。如果里面有人说话，程序还需要把语音转成文字，才能继续处理提问的内容。''')
    setcell(b, 27, '''### 4.1 语音识别

把语音转成文字叫**语音识别**，英文缩写 ASR。

可以把它理解为给录音配字幕：模型根据声音的特征和上下文，生成可能对应的文字。模型通常通过大量语音和文字资料学习这种对应关系；不同模型的内部做法会有差别。

在本课中，主要看接口的输入和输出：

- 输入：包含人类语音的音频；
- 输出：识别出的文字，可能存在误识别。

写出“几点开门”只完成了转写。要知道来宾在询问开放时间，并给出回答，还需要后续处理。''')
    setcell(b, 28, '''### 4.2 流式与整句

按照音频交入和文字返回的方式，可以比较两种常见用法：

| 方式 | 怎样取得结果 | 应用中的需要 |
|---|---|---|
| 整句（整段）识别 | 一句话或一段录音准备好后，整段交入，再取得文字 | 已录好的语音留言转写，可以等完整录音准备好再处理 |
| 流式识别 | 声音持续分块交入，在说话过程中陆续返回文字 | 会议实时字幕、边说边输入，希望讲话过程中就看到文字 |

两种方式都把音频转成文字。同一个产品也可以组合使用：例如语音助手先持续接收声音，在判断用户说完后再整理结果。不能只凭“智能音箱”或“会议软件”的名称判断内部用了哪种接口。

流式识别很像一边听一边写字幕，前面显示的文字可能随着后面的声音修正。本课 `recognize_stream()` 的回调只给出 `text`，没有“本句最终结果”的标志，因此不能把最后一次回调直接当作已经确认的完整句子。''')
    replace(b, 30, '识别任务发出去之后会一直“监听”声音，它不会自己停，调用 `cancel()` 来停止。', '''这是持续任务，不以一句话识别完成为结束条件，也可能因错误退出。本实验留6秒观察窗口，再调用 `cancel()` 请求停止，并用 `wait(timeout=5.0)` 等待收尾。

`cancel()` 的返回值只表示取消请求是否提交成功。`done()` 为 `True` 才说明任务已结束，成功、失败、取消都属于结束状态；`running()` 为假还可能是等待或取消中。若仍未结束，保留句柄继续检查，不能覆盖它另开一次识别。''')
    setcell(b, 31, listen_code('开始识别，请说一句话', '''from boosteros.brain import Speech

speech = Speech(robot)

def on_text(text):
    print("识别到：", text)

'''))
    setcell(b, 33, listen_code('再说一遍刚才那句话'))
    setcell(b, 34, '''## 六、观察与记录

### 6.1 录到的这段数据

| 项目 | 记录 |
| :--- | :--- |
| 音频时长（秒） | 　　　　 |
| 采样率 / 声道数 / 采样格式 | 　　　　 |
| PCM数据长度（字节） | 　　　　 |
| 按“时长 × 采样率 × 声道数 × 2”估算（字节） | 　　　　 |

### 6.2 同一批声音块的播放对照

声音块数：________；总字节数：________；换算的音频长度：________秒。

| 队列容量 | 全部块写入耗时（秒） | 是否观察到明显写入等待 | 声音是否完整、有无卡顿 | 等待返回的状态 |
|---|---|---|---|---|
| 4 |  |  |  |  |
| 64 |  |  |  |  |

按实际结果填写。若两组差别不明显，记录现象和运行条件，不必凑出预设结论。本实验先录后放，不能用它测量边说边播的实时延迟。

### 6.3 两次识别的结果

每次可能收到多条文字回调，可按出现顺序记录，注明有没有修正。

| 次数 | 观察到的文字与变化 | 与说话内容是否一致 | 取消后的状态 / done() |
| :---: | :--- | :--- | :--- |
| 第1次 |  |  |  |
| 第2次 |  |  |  |

### 6.4 检查点

- 是否能区分采样数据、转写文字和理解提问的含义。
- 是否能解释相同时长下，三声道的数据量为什么是单声道的三倍。
- 是否能说明队列满时三种溢出策略的区别，并根据记录解释两组写入现象。
- 是否能用返回状态判断播放是否成功，以及识别任务是否已经结束。

### 6.5 思考题

- 两次说同一句话，识别结果不一样。哪些输入条件可能变了？怎样比较才更公平？
- 输入的声音块比播放快时，多出的块暂存在哪里？队列满后会怎样？挑一种 `overflow` 设定说明。
- 语音留言转写和会议实时字幕，分别适合怎样的识别方式？说出理由。''')

    b = books[1]
    replace(b, 1, '并说出 `synthesize()` 与 `play_sound()` 各属于哪一类、理由是什么。', '并说明SDK的 `synthesize()` 与 `robot.play_sound()` 如何返回句柄、怎样等待结果或播放完成。')
    setcell(b, 2, '''## 一、本课要解决的问题

上节课将语音转成了文字。要让机器人说出一段已知的文字，还需要生成对应的声音，再交给扬声器播放。

本课先用程序构造提示音，观察声音数据怎样影响听感；再调用语音合成接口，让机器人用指定音色说出一段文字。''')
    replace(b, 4, '它跟上节课麦克风采集的数据是同一种格式，因此也包含采样率、声道数、采样格式三个参数。', '扬声器可以播放上节课使用的PCM采样数据；数据同样需要注明采样率、声道数和采样格式。')
    replace(b, 5, '每个采样点 2 字节，所以「时长 × 采样率 × 2」就是总字节数。', '本课附件构造的是单声道 `S16LE PCM`，每个采样数值占2字节，因此数据量为“时长 × 采样率 × 1 × 2”。上节课K1采音用三声道；本次合成提示音只生成一路数据，播放流也设为单声道。声道数要与实际数据一致。')
    replace(b, 8, '这一格会持续响 1.5 秒，是一段「嘀」的声音，不是说话声。音量别开太大。', '请将本课Notebook与附件 sound_lab.py、fonts/ 文件夹放在同一目录，保持字体文件的位置。这一格会响约1.5秒提示音，音量先调低。')
    setcell(b, 10, '''**知识总结：本实验使用的声音参数**

- **采样率**：每个声道每秒记录多少个数值。附件默认使用16000 Hz。
- **声波频率**：声音每秒振动多少次，影响音调高低。标准音A4的频率为440 Hz。
- **持续时间**：这段声音有多长，单位是秒。

采样率和声波频率都用Hz表示，但数的对象不同：一个数采样次数，一个数振动次数。这里每秒取16000个采样数值，用它们描述每秒振动440次的正弦波，生成约1.5秒的提示音。''')
    setcell(b, 13, '''**STEP 04：** 比较声音的波形

运行下面的程序，观察两种设置在最初10毫秒内的波形。在相同时间内，哪一种设置的波峰更多？将图上的变化与刚才听到的音调高低对应起来。''')
    setcell(b, 15, '''**STEP 05：** 比较不同波形的音色

频率相同的钢琴、笛子和蜂鸣器，听起来仍有差别，这与**音色**有关。声音中有哪些频率成分，各成分有多强，以及声音如何逐渐增强、衰减，都会影响音色。这里不展开计算，先试听几种合成方式：

- `sine`（正弦波）：较纯净的单音。
- `square`（方波）：听感接近一些早期电子游戏的提示音。
- `sawtooth`（锯齿波）：听起来较明亮、尖锐。
- `bell`（钟琴声）：多个频率成分叠加后逐渐衰减，模拟敲击后的声音。

下面先画波形示意，再试听。图是依据配置重新计算的示意，不是从本次播放数据中抽出的测量图；尤其 `bell` 的绘图与试听采用不同的简化表达式，用于观察叠加与衰减的特点。''')
    replace(b, 16, '# 1. 绘制 4 种典型波形的数学形态', '# 1. 绘制4种波形的示意图（不是本次播放数据的逐点测量）')
    for i, old, new in [(18,'03','06'), (20,'04','07'), (23,'05','08'), (25,'06','09'), (31,'07','10')]:
        replace(b,i,f'STEP {old}',f'STEP {new}')
    replace(b, 26, '在 STEP 05 选择一个音色', '在 STEP 08 选择一个音色')
    for i in (19,26):
        replace(b,i,'合成完成: {audio.duration.seconds:.2f}s', '生成音频时长：{audio.duration.seconds:.2f} 秒')
    setcell(b, 21, '''playback = robot.play_sound(save_path)
playback_status = playback.wait()
if playback_status == "SUCCEEDED":
    print("播放完成")
else:
    print("播放未成功，状态：", playback_status, "；错误：", playback.error)''')
    replace(b, 26, 'robot.play_sound(audio).wait()\nprint("播放结束")', '''playback = robot.play_sound(audio)
playback_status = playback.wait()
if playback_status == "SUCCEEDED":
    print("播放完成")
else:
    print("播放未成功，状态：", playback_status, "；错误：", playback.error)''')
    setcell(b, 28, '''### 3.1 同步调用

同步调用会在当前代码里等待，直到本次调用返回，才执行下一行。例如查询音量、列出音色，都要先取得返回值才能继续。

“同步”描述的是调用和返回的关系，并不保证很快。如果服务或网络响应较慢，同步调用也会等待较久。''')
    setcell(b, 29, '''### 3.2 异步调用

调用 `synthesize()` 时，合成工作可能还没有完成，函数就先返回一个**任务句柄**。可以把句柄想成办理业务的取号单：凭它查看任务是否结束，或取得结果。

本课常用的句柄操作：

| 操作 | 含义 |
|---|---|
| `status` | 当前任务状态，例如等待、运行、成功、失败或取消；不显示内部识别、推理、合成的步骤 |
| `done()` | 是否已进入成功、失败或取消这三种终态之一 |
| `running()` | 是否处于 `RUNNING`；为假还可能在等待或取消中 |
| `wait(timeout=...)` | 等待任务结束；超时返回当前状态，任务可能仍在运行 |
| `result()` | 等待有具体结果的任务，成功后取得结果；合成任务得到 `AudioData` |
| `cancel()` | 请求取消，返回请求是否成功提交；还需等待并检查是否结束 |

异步接口允许程序在任务执行期间继续做其他事；也可以立即等待。本课先调用 `synthesize()`，再用 `result()` 取得合成音频：

```python
handle = speech.synthesize("欢迎来到实训室。")
audio = handle.result()
```

SDK的 `robot.play_sound(audio)` 也返回句柄；调用 `.wait()` 可以等播放任务结束。两者都是异步接口，后面加等待不会改变接口本身的类型。

本课附件中的 `play_sound(robot, pcm_data)` 是教学封装，内部依次写入声音、`close()`结束输入、`wait()`等待播放；成功后才返回，供我们按顺序试听。它与SDK的 `robot.play_sound()` 名称相似，调用方式和返回行为不同。

`close()`只结束播放流的输入，队列里的声音会继续播放，因此之后仍需要 `wait()`。持续识别或对话则没有预定的结束时长，`wait()`等待的是整个任务结束，不能用来判断用户的一句话是否已经处理完。''')
    setcell(b, 31, '''**STEP 10：** 主动提问的智能助手

先合成并播放一句提问，成功播放后，再留6秒观察人的语音转写。这里暂不生成回答，也不查询外部信息。取消识别后检查 `done()`；若仍未结束，先处理原任务，再重新运行。''')
    setcell(b, 32, '''from boosteros.brain import Speech
import time

speech = Speech(robot)

if "task" in globals() and not task.done():
    print("上一项语音任务尚未结束，状态：", task.status)
    print("先运行 task.cancel()，再运行 task.wait(timeout=5.0)，确认 task.done() 为 True 后重试。")
else:
    welcome_msg = "你好，欢迎来到实训室，请问你想了解机器人的哪一项功能？"
    handle = speech.synthesize(welcome_msg)
    audio = handle.result()
    print(f"生成音频时长：{audio.duration.seconds:.2f} 秒")

    playback = robot.play_sound(audio)
    playback_status = playback.wait()
    if playback_status != "SUCCEEDED":
        print("播放未成功，暂不开始识别。状态：", playback_status, "；错误：", playback.error)
    else:
        def on_text(text):
            print("识别到：", text)

        task = speech.recognize_stream(on_result=on_text)
        print("开始识别，请回答刚才的问题")
        try:
            time.sleep(6)  # 观察窗口，不是识别处理耗时
        finally:
            accepted = task.cancel()
            print("取消请求已提交：", accepted)
            task.wait(timeout=5.0)
        print("当前状态：", task.status, "；是否已结束：", task.done())
        if not task.done():
            print("任务尚未结束，保留 task 继续检查，暂不再次运行。")
        elif task.status == "FAILED":
            print("识别失败：", task.error)''')
    replace(b, 33, '### 5.1 自己造的声音数据', '### 5.2 自己造的声音数据')
    replace(b, 33, '采样率 / 采样格式', '采样率 / 声道数 / 采样格式')
    replace(b, 33, '实际时长（秒）', '音频时长（秒）')
    replace(b, 33, '- 是否知道说话为什么要 `wait()` 或 `cancel()`，不加会出什么事。', '- 是否能区分等待有限任务完成，与请求取消持续任务；是否知道取消后还要确认终态。')
    replace(b, 34, '这就是音色 ID 的来历。', '服务再用音色ID标识可选声音；ID本身不一定就是训练时的说话人编号。')
    replace(b, 34, '三种方法有个共同点：**输出的都是同样的数据类型**。不管中间多复杂，最后交给扬声器的都是同一类型的数据。换音色不影响程序流程，变的只是模型生成采样点时偏向的目标。', '这些方法都要生成可播放的声音。在本课的SDK接口中，合成结果统一表示为 `AudioData`，因此换音色后，取结果和播放的程序流程可以保持一致。')

    b = books[2]
    setcell(b, 1, '''# U5-L3：LLM 对话

**课程目标**

1. 能说明大语言模型怎样利用训练所得和当前上下文生成回答，并指出流畅的回答仍可能有事实错误。
2. 能区分模型与角色提示词：换提示词可以影响回答的身份、语气、长度和范围，不能凭空增加实时信息或工具。
3. 能按身份、语气、知识范围、不能做什么编写提示词，用同一个问题比较不同设定的表现。
4. 能启动持续语音对话，用 `wait()` 等待会话，并在中断后请求取消、检查任务是否结束。''')
    setcell(b, 2, '''## 一、本课要解决的问题

前两课已经把语音转成文字，也让机器人说出了指定文字。要与来宾交流，还需要根据问题组织回答。

大语言模型可以生成回答。回答内容受模型训练所得、当前设定和对话内容影响；同一个问题多问几次，措辞可能不同，也可能出现事实错误。

本课用同一个问题比较不同角色提示词，观察回答的语气、长度和范围，并尝试把它配置成适合实训室或展厅的讲解员。''')
    setcell(b, 3, '''## 二、大语言模型在做什么

语音对话通常要经过语音识别、回答生成和语音合成。大语言模型主要参与其中的回答生成：根据输入的文字及上下文，生成后续内容。

`chat()` 把这些环节组织在一个持续会话中。本课通过接口使用它，重点观察角色设定怎样影响回答。''')
    setcell(b, 4, '''### 2.1 用“文字接龙”理解生成过程

可以把大语言模型生成回答的过程，初步想成“接着前文往下写”。例如“欢迎来到实训室，请先……”后面，可以接“阅读操作要求”，也可以接其他内容；选择与当前问题、前文和模型训练所得有关。

模型通常逐步生成文本，每次处理的单位叫 **token**，可能对应一个字、一个词或词的一部分。生成出的内容加入上下文后，再影响后面的内容。大语言模型的英文缩写是 **LLM**。

“文字接龙”只是帮助理解逐步生成的比喻。模型在训练中也学习了语言、知识及解决问题的模式，能够完成解释、写作和代码等任务；不能因此认定它只会检查句子是否通顺。它的回答可以很流畅，同时仍有事实错误。''')
    setcell(b, 5, '''### 2.2 它的知识从哪来

模型在训练时从大量资料中学习语言和知识。当前提示词、对话历史或额外提供的资料，也能影响这次回答。

使用时要注意信息从哪里来：

- **训练资料有时间范围**。例如训练资料截止到2022年，模型可能已经知道巴黎将举办2024年奥运会，因为主办城市早已公布；但赛后才产生的某场比赛结果，不能只靠这批训练资料得知。是否能回答，还取决于后来是否更新过模型、提供过资料，或接入了检索工具。
- **本地信息需要提供**。学校的最新开放时间、本节课安排、这台机器人昨天的实验记录，不能假定模型已经知道。

例如询问“我们实训室今天几点开放”，需要有本校的有效安排。只在提示词里写“你知道开放时间”，不会自动取得这份资料。''')
    setcell(b, 6, '''### 2.3 流畅的回答也可能有错

模型在资料不足或判断错误时，仍可能生成语气肯定、细节完整的回答。这类缺乏依据或与事实不符的生成内容，常被称为**幻觉**。

例如题目把人物或事件混在一起，模型可能顺着错误前提编下去，也可能指出错误。不同模型和提问方式的表现会有差别，不能要求某个旧例子每次都能复现。

检查回答时，要将人名、数字、时间等与可靠资料核对。核对可以由人完成，也可以借助检索和专门工具；不能只看回答是否通顺、有无自信。''')
    replace(b, 7, '下面，尝试应用默认配置开始一次对话。', '`chat()` 返回 `TaskHandle[None]`，代表整个持续会话。下面使用默认配置体验。')
    setcell(b, 10, '''**STEP 02：** 初体验：开始一段问答

1. 向机器人问一个简单问题。
2. 说“停一下”“先别说”或“stop”，尝试打断它当前的回答。
3. 再问一个问题，观察会话是否继续。

打断当前回答与退出整个会话不同。体验结束时，按 Ctrl+C 或 Notebook 的中断按钮，让代码进入取消流程。`wait()` 等的是整个会话结束，用户问完一句、机器人答完一句都不代表会话已结束。

下一格只在上一项语音任务已结束时新建任务。取消后等待最多5秒，并查看 `done()`。若仍未结束，保留 `task`，运行 `task.cancel()`、`task.wait(timeout=5.0)` 继续检查，暂不开始下一项任务。''')
    setcell(b, 11, chat_code('''task = speech.chat(
    config=ChatConfig(volume=0.6),
    enable_subtitle_log=True,
)'''))
    replace(b, 12, '为了增加聊天友好型，可以进一步给机器人进行参数配置，比如配置「音色、身份、欢迎语」。', '可以通过音色、角色提示词和欢迎语，让对话更符合使用场景。')
    replace(b, 14, '设置音色、欢迎语、角色提示词', '设置欢迎语和角色提示词')
    setcell(b, 15, chat_code('''task = speech.chat(
    config=ChatConfig(
        system_prompt="你是实训室讲解员。已知资料：本实训室使用K1机器人练习视觉检测、运动控制和语音交互。只根据这些资料回答，其他信息请说明暂不清楚。每次回答不超过两句。",
        welcome_msg="你好，欢迎来到实训室，你想了解哪项练习？",
        volume=0.5,
    ),
    enable_subtitle_log=True,
)'''))
    replace(b, 16, '- `参数：interrupt_keywords`', '- 参数：`interrupt_keywords`')
    setcell(b, 17, '''当前回答通常受角色提示词、已有对话和新提问共同影响。角色提示词描述身份与要求，对话历史提供前面谈过的内容，新提问说明这次要回答什么。

上面的讲解员提示词还给了一小段实训室资料，便于回答有依据。提示词可以提供资料和要求，但不会凭空给机器人增加天气查询、数据库访问等工具。''')
    setcell(b, 18, '''### 3.2 同一模型的不同“人设”

保持模型不变，只换角色提示词，回答的语气、长度和侧重点就可能变化。这类角色设定常被称为**人设**。

提示词是在本次使用中提出要求，不会重新训练模型，也不保证模型每次都完全遵守。需要通过实际问答检查，再调整设定。''')
    replace(b, 19, '天气预报助手', '实训室讲解员')
    replace(b, 19, '**知识范围**：哪些事你懂（这个展厅的展项）；', '**知识范围**：允许依据哪些资料回答（例如给出的展项资料）；')
    replace(b, 20, '胡说霸道', '编造内容')
    replace(b, 20, '所以人设写完一定要不断测试、修改直至满意。', '因此需要用具体问题测试，记录偏离要求的地方，再修改提示词。')
    setcell(b, 22, '''### 4.1 固定问题，测试语音识别效果

机器人接收的是现场说出的声音。语速、音量和环境噪声都会影响转写结果。

先用同一句问题试几次，练习稳定地说出问句。下面仍留6秒观察窗口，显示回调中最近一次文字；接口没有最终结果标志，这条文字只能作为本次观察记录。确认识别任务已结束后，再开始对话。''')
    setup = '''import time

QUESTION = "请用一句话介绍一下机器人。"  # 后面几次都问同一句

'''
    # 不在旧任务仍活跃时清空其回调使用的变量。
    listener = listen_code('请说出固定问题：' + '请用一句话介绍一下机器人。', '')
    listener = listener.replace('    task = speech.recognize_stream', '''    last_text = ""

    def on_text(text):
        global last_text
        last_text = text
        print("文字回调：", text)

    task = speech.recognize_stream''')
    listener += '    print("最近一次收到的文字（不保证为最终整句）：", last_text)\n'
    setcell(b, 24, setup+listener)
    replace(b, 25, '### 4.3', '### 4.2')
    setcell(b, 26, chat_code('''task = speech.chat(config=ChatConfig(volume=0.5), enable_subtitle_log=True)''', 'print("请对着机器人说出这句话：", QUESTION)\n\n'))
    replace(b, 27, '### 4.4', '### 4.3')
    replace(b, 27, '每种人设对话结束后，切换人设再运行程序。', '每次选择一种人设运行。体验后中断会话，确认 `task.done()` 为 `True`，再改 `name` 切换下一种人设；不按固定秒数猜测回答是否结束。')
    old = src(b['cells'][27])
    pre = old.split('print(f"=== 人设：')[0]
    setcell(b, 28, chat_code('''task = speech.chat(
    config=ChatConfig(system_prompt=prompt, volume=0.5),
    enable_subtitle_log=True,
)''', pre+'print(f"人设：{name}；请说出：{QUESTION}")\n\n'))
    replace(b, 29, '### 4.5', '### 4.4')
    setcell(b, 30, chat_code('''task = speech.chat(
    config=ChatConfig(system_prompt=MY_PROMPT, volume=0.5),
    enable_subtitle_log=True,
)''', '''MY_PROMPT = """你是展厅迎新讲解员，说话简短、语气友好。
已知展项：视觉检测演示、运动控制演示、语音交互演示。
只根据以上资料讲解，最多介绍三个展项，每项不超过一句话。
资料中没有的内容请说明暂不清楚；涉及报价或活动时间，请转给现场工作人员。"""

print("请对着机器人问同一个问题：", QUESTION)

'''))
    replace(b, 31, '| 自己写的那一版 | 　　　　 | 　　　　 | 　　　　 | 　　　 |　　　　　　　　　　　　　　　　 |', '| 自己写的那一版 | 　　　　 | 　　　　 | 　　　　 | 　　　 |')
    replace(b, 31, '- 是否知道人设写得含糊会带来什么后果。', '- 是否知道人设写得含糊会带来什么后果，并能根据观察修改。\n- 是否确认前一项语音任务已结束，再切换人设；是否能区分打断一句回答与结束整个会话。')
    setcell(b, 32, '''## 六、扩展阅读：怎样减少缺乏依据的回答

模型生成回答时，流畅程度和事实准确性可能不一致。训练资料不足、提问带有错误前提、当前资料缺失等，都可能影响结果。

在实训室讲解这类任务中，可以这样处理：

- **提供有效资料**：给出本校实训室或展项说明，要求回答与资料相符。
- **约定回答范围**：只谈已给资料覆盖的内容，报价、开放时间等交由工作人员确认。
- **核对事实**：对人名、数字、日期等查阅原始资料；可由人完成，也可由程序调用专门工具辅助。
- **允许回答不知道**：资料没有说明时明确告知用户，而不是补出一个看似完整的答案。

这些方法可以降低错误风险，但提示词、检索工具和核查程序本身也有局限。模型能力、资料质量和使用流程都会影响结果。课堂上应把实际回答与已给资料对照，记录它是否遵守要求。''')

    for i, (p, nb) in enumerate(zip(paths, books),17):
        for c in nb['cells']:
            if c['cell_type']=='code':
                ast.parse(src(c))
        write(p,json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
        write(PROJ/f'_gen_L{i}.py',generator(p,nb['cells']))
    dup = json.loads(read(duplicate))
    if len(dup['cells']) != len(books[1]['cells']):
        raise ValueError('L2副本单元格数不同，需人工核对')
    for c, master in zip(dup['cells'],books[1]['cells']):
        if c['cell_type'] != master['cell_type']:
            raise ValueError('L2副本类型不同')
        c['source']=copy.deepcopy(master['source'])
    write(duplicate,json.dumps(dup,ensure_ascii=False,indent=1)+'\n')

    s=read(extra)
    s=s.replace('def play_sound(robot, pcm_data:', '_playback_stream = None  # 保留未结束的播放流，防止下一次调用覆盖它\n\n\ndef play_sound(robot, pcm_data:')
    s=s.replace('    """向机器人发送 PCM 流并完成播放"""', '''    """按顺序播放单声道PCM；成功后返回，失败或超时则报告异常。"""
    global _playback_stream
    terminal_states = ("SUCCEEDED", "FAILED", "CANCELLED")
    if _playback_stream is not None and _playback_stream.wait(timeout=0.0) not in terminal_states:
        raise RuntimeError("上一次播放尚未结束，请保留sound_lab模块中的_playback_stream检查状态，暂不重复播放。")''')
    s=s.replace('    try:\n        chunk_bytes', '    _playback_stream = stream\n\n    try:\n        chunk_bytes')
    s=s.replace('    stream.wait(timeout=10.0)', '''    status = stream.wait(timeout=10.0)
    if status not in terminal_states:
        accepted = stream.cancel()
        status = stream.wait(timeout=5.0)
        raise RuntimeError(f"播放等待超时；取消请求提交：{accepted}，当前状态：{status}。声音可能未完整播放。")
    if status != "SUCCEEDED":
        raise RuntimeError(f"播放未成功，状态：{status}")''')
    ast.parse(s)
    write(extra,s)
    print('三课、L2发放副本、附件和生成器已修订；真机输出与执行次数保留。')

def inspect():
    for p in (ROOT/'CHANGELOG.md', BASE/'README.md', PROJ/'X课程开发计划-v4.md',
              BASE/'02_共创规则与上下文/notebook开发规则.md', NB/'_外挂附件清单.md'):
        lines=read(p).splitlines()
        print('\nFILE',p.relative_to(ROOT).as_posix())
        if p.name=='CHANGELOG.md':
            print('\n'.join(lines[:28]))
        for i,l in enumerate(lines,1):
            if ('U5-L1' in l or 'U5-L2' in l or 'U5前三' in l or '语音SDK' in l) and len(l)<2000:
                print(i,l)
    print('\n局部AGENTS:', [p.relative_to(ROOT).as_posix() for p in BASE.rglob('AGENTS.md')])
    def git(*args):
        return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8').stdout
    print('已暂存',git('diff','--cached','--name-only'))
    print('目标文件工作区差异',git('diff','--numstat','--',*[p.relative_to(ROOT).as_posix() for p in NB.glob('U5-L[1-3]_*.ipynb')],(NB/'U5-L2').relative_to(ROOT).as_posix()))
    for p in sorted(NB.glob('U5-L[1-3]_*.ipynb')):
        b=json.loads(read(p))
        print(p.name,'STEP',[(i,re.findall(r'STEP \d+',src(c))) for i,c in enumerate(b['cells'],1) if 'STEP' in src(c) and c['cell_type']=='markdown'])

if __name__=='__main__':
    if sys.argv[1]=='build':
        build()
    elif sys.argv[1]=='inspect':
        inspect()
