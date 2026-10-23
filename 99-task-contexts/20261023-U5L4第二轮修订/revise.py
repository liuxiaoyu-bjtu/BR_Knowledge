"""以 Notebook 为主稿修订 U5-L4，再反向同步生成器；不连接机器人。"""
import hashlib
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
PROJ = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
NB = PROJ / 'notebooks/U5-L4_语音问答闭环.ipynb'
SHARED = [ROOT / p for p in ('AGENTS.md', 'INDEX.md', 'CHANGELOG.md')]
SHARED += [PROJ / 'X课程大纲-v4.md', PROJ / 'X课程开发计划-v4.md',
           PROJ.parent / 'README.md', PROJ.parent / '02_共创规则与上下文/notebook开发规则.md']
DIRECT = [NB, PROJ / '_gen_L20.py',
          PROJ / '实验验证/U5_语音SDK能力核验记录.md',
          PROJ / '实验验证/U5-L4_真机问题复评与重构建议.md']

def source(s):
    return dedent(s).strip() + '\n'

def backup():
    hashes = {}
    for p in DIRECT + SHARED:
        target = TASK / 'before' / p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(p.read_bytes())
    for p in sorted((PROJ / 'notebooks').glob('U5-L[123]*.ipynb')):
        hashes[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    target = TASK / '前三课基线指纹.json'
    if not target.exists():
        target.write_text(json.dumps(hashes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def build():
    backup()
    original = json.loads((TASK / 'before' / NB.relative_to(ROOT)).read_text(encoding='utf-8'))
    cells = []
    def md(s):
        cells.append(dict(cell_type='markdown', id=f'u5l4-r2-{len(cells)+1:02}', metadata={}, source=source(s).splitlines(True)))
    def code(s):
        cells.append(dict(cell_type='code', id=f'u5l4-r2-{len(cells)+1:02}', metadata={}, execution_count=None, outputs=[], source=source(s).splitlines(True)))

    md('''
    # U5-L4：语音问答闭环

    **课程目标**

    1. 能按输入和输出解释采音、语音转写、回复生成、语音合成与播放，说明 `chat()` 如何支持持续问答。
    2. 能说明任务句柄的用途，读取任务状态，判断任务是否结束。
    3. 能画出会话管理的状态与转换条件，运行并调整程序，完成启动、阻止重复启动、停止和再次启动。
    ''')
    md('''
    ## 一、同一个会话中的连续问答

    L1 观察了录音与语音识别，L2 将文字合成为语音，L3 用 `chat()` 让机器人连续回答问题。机器人说完一个回答后，还可以接着听下一个问题；一轮问答结束时，整个会话通常仍在继续。

    如果用户连续按两次“开始”，程序需要保留正在使用的会话。用户按下“停止”后，程序还要确认旧任务已经结束，才能允许再次启动。本课用“开始、查看、停止”三种操作管理同一个会话。
    ''')
    md('''
    ## 二、从语音问答到任务句柄

    ### 2.1 “听、懂、说”分别处理什么

    例如，学生问“刚才提到的语音识别有什么用途？”。一次语音问答涉及以下功能：

    | 功能 | 处理的输入 | 产生的输出 | 已有的学习经验 |
    |---|---|---|---|
    | 采音 | 麦克风接收到的声音 | 音频采样数据 | L1 录音与声音块 |
    | 语音转写（ASR） | 音频数据 | 识别出的文字 | L1 `recognize_stream()` |
    | 回复生成（LLM） | 提问文字、已有对话与人设要求 | 回复文字 | L3 人设与连续问答 |
    | 语音合成（TTS） | 回复文字 | 语音数据 | L2 `synthesize()` |
    | 播放 | 语音数据 | 扬声器发出的声音 | L1、L2 播放声音 |

    ASR 将声音转为文字，例如转写出“刚才提到的语音识别有什么用途”。其中“刚才提到的”指什么，需要结合前面的对话。LLM 根据这些文字、上下文和人设要求组织回答；TTS 将回答文字合成为声音，最后由扬声器播放。

    “听”主要对应采音与转写，“懂”在这里指模型结合问题和上下文生成相关回答，“说”对应合成与播放。转写错误会影响后续回答；转写正确时，模型也可能答非所问。判断交互是否有效，需要结合提问和实际回答。

    `chat()` 将这些能力组织为持续语音对话。启动一个会话后，学生可以连续提问。本课通过这个接口使用问答能力，无需逐项调用上表中的接口来拼接会话。表格说明功能关系，各功能在实现时也可能边接收边处理。
    ''')
    md('''
    ### 2.2 `chat()` 返回了什么

    L3 中的 `chat_task = speech.chat(...)`，把返回的对象保存在 `chat_task` 中。这个对象叫**任务句柄**：程序凭它查看任务、等待结束或申请取消。可以把句柄理解为这次任务的办理凭据；保留它，才能继续查询和管理这次任务。

    官方将这个返回类型写成 `TaskHandle[None]`：

    - `TaskHandle` 表示返回的是任务句柄。
    - 方括号中的 `None` 表示任务没有一份供程序在结束时领取的结果数据。机器人仍会说话，`chat()` 也确实返回了句柄。

    L2 的 `synthesize()` 会产生音频数据，成功后用 `result()` 取出音频。持续会话则用句柄管理其运行和结束；等待结束使用 `wait()`。本课不通过 `result()` 领取聊天文字。

    句柄的 `trace_id` 是本次任务的追踪标识。后面的程序打印它，便于比较重复“开始”时是否保留旧任务，以及重新启动时是否创建了新任务。
    ''')
    md('''
    ### 2.3 从句柄读取任务状态

    `chat_task.status` 读取这个会话任务的当前状态。状态名称由 SDK 定义，程序会根据任务的实际执行情况更新它。

    | `status` 的取值 | 含义 | `done()` 的返回值 |
    |---|---|---|
    | `PENDING` | 任务已创建，等待执行 | `False` |
    | `RUNNING` | 任务正在执行 | `False` |
    | `CANCELLING` | 任务正在取消 | `False` |
    | `SUCCEEDED` | 任务成功结束 | `True` |
    | `FAILED` | 任务因失败结束 | `True` |
    | `CANCELLED` | 任务已取消 | `True` |

    最后三种状态称为**终态**。`chat_task.done()` 用来判断任务是否已进入终态，适合用作“是否允许重新开始”的条件。`RUNNING` 描述整个会话正在执行；同一个会话里，机器人听问题、回答问题、等待下次提问，都可能保持这个状态。

    | 写法 | 程序执行的操作 |
    |---|---|
    | `chat_task.status` | 读取当前状态；这个属性只读 |
    | `chat_task.done()` | 判断任务是否已结束 |
    | `chat_task.error` | 读取错误信息；任务为 `FAILED` 时用它排查 |
    | `chat_task.cancel()` | 请求取消任务；返回布尔值，表示请求是否成功提交 |
    | `chat_task.wait(timeout=5.0)` | 等待任务结束，最多等五秒；返回结束时或超时时的状态 |

    取消请求提交成功后，任务可能还在结束过程中。有限等待返回后仍要检查 `done()`；达到等待上限只会让本次等待返回，不会自动取消任务。
    ''')
    md('''
    ### 2.4 在 Notebook 中使用持续任务

    L3 在启动后调用不带超时的 `wait()`，当前代码格会一直等待整个会话结束。本课保存 `chat()` 返回的句柄，让启动代码格先执行完，再在其他代码格中查看和停止同一个任务。

    语音任务由 SDK 异步执行：启动调用返回后，任务可以继续运行，Python 也可以执行下一条语句。因此，代码格运行结束时，机器人仍可能继续接收提问。后面的实验将分别观察代码格和会话任务的运行情况。
    ''')
    md('''
    ## 三、观察句柄与任务状态

    ⚠️ **注意**：本课只使用麦克风和扬声器，不发送运动指令。保持适中音量，各组错开说话；开始前结束 L1～L3 留下的录音、识别和聊天任务，不同时运行多个语音 Notebook。

    📌 **前置准备**：完成开机、配网和 IP 确认，电脑与机器人连接同一 WiFi，已能用 BoosterStudio 连接。机器人保持教师确认的稳定姿态，本课不切换运动模式。如果接续行走实验，先按该课流程停止运动、回到 `prepare` 并确认站稳；收起时由人工支撑，再进入 `damping` 并扶坐，严禁从 `walk` 直接切到 `damping`。

    ### 3.1 连接与初始化

    **STEP 01：** 连接机器人，建立保存句柄的变量。

    <font color="red">提示：</font>初始化格只在确认没有遗留任务时运行一次。会话启动后，重新执行 `chat_task = None` 会丢失原句柄，后台任务却可能仍在运行。若已丢失句柄，请教师协助结束旧任务，再继续实验。

    初始化中的 `chat_task = None` 表示这个变量还没有保存任务句柄。它与返回类型 `TaskHandle[None]` 中表示“没有最终结果数据”的 `None` 用途不同。
    ''')
    code('''
    from boosteros.robots.booster import BoosterRobot
    from boosteros.brain import Speech
    from boosteros.brain.speech import ChatConfig

    robot = BoosterRobot()
    speech = Speech(robot)
    robot.audio_manager.set_system_volume(0.5)

    PROMPT = "你是机器人实训课的学习助手。请用简短、清楚的中文回答。"
    chat_task = None

    print("已连接：", robot.robot_info.model, robot.robot_info.serial_number)
    ''')
    md('''
    ### 3.2 启动并查看同一个会话

    **STEP 02：** 发起会话，保存句柄。下一格先检查旧任务；没有旧任务或旧任务已经结束时，才创建新会话。

    代码格执行完后，问“什么是语音识别？”，再问“请举一个刚才这种技术的应用”。听完回答后暂时不说话，再运行 STEP 03。记录能否连续问答，以及等待提问时的任务状态。
    ''')
    code('''
    if chat_task is None or chat_task.done():
        chat_task = speech.chat(
            config=ChatConfig(system_prompt=PROMPT, volume=0.5),
            enable_subtitle_log=True,
        )
        print("已保存新句柄。")
    else:
        print("已有未结束的会话，保留原句柄。")

    print("任务标识：", chat_task.trace_id)
    print("SDK 状态：", chat_task.status)
    ''')
    md('''
    **STEP 03：** 读取状态，并进行一次有限等待。

    `wait(timeout=2.0)` 最多等待任务结束两秒。会话仍在继续时，这次等待达到上限后便返回当前状态；已经结束时则立即返回终态。这里观察的是整个任务是否结束。

    运行后重跑 STEP 02，比较任务标识，检查重复启动是否被拦住。再提一个问题，确认原会话能否继续使用。
    ''')
    code('''
    observed_status = chat_task.wait(timeout=2.0)
    print("本次等待返回的状态：", observed_status)
    print("当前 SDK 状态：", chat_task.status)
    print("任务是否结束：", chat_task.done())
    print("任务标识：", chat_task.trace_id)
    if chat_task.status == "FAILED":
        print("错误信息：", chat_task.error)
    ''')
    md('''
    ### 3.3 用回调观察状态变化

    **STEP 04：** 为当前句柄登记一个状态回调。

    L1 的 `on_text(text)` 在收到识别文字时被调用。下面的 `on_status(task)` 接收任务句柄，用它打印状态。`add_status_change_callback()` 登记后会立即按当前状态调用一次，之后状态发生变化时再调用。

    这一格对当前句柄只运行一次，重复登记会产生重复输出。登记完成后继续提问、暂时保持安静，观察是否出现新的状态输出。短暂状态可能来不及看到，按实际输出记录。这个回调绑定当前任务，重新创建的任务需要另行登记。
    ''')
    code('''
    def on_status(task):
        print("状态回调：", task.trace_id, task.status)

    chat_task.add_status_change_callback(on_status)
    ''')
    md('''
    ### 3.4 打断说话与取消会话

    **STEP 05：** 机器人回答时尝试说“停一下”，随后再提一个问题，并运行 STEP 03 查看状态。语音打断用于打断当前说话；若会话仍在运行，机器人可以继续接收新问题。把听到的现象与状态输出分别记录。

    然后运行下一格，用 `cancel()` 请求结束整个会话。五秒是这次停止操作愿意等待的上限。若还未进入终态，保留句柄，稍后再运行 STEP 03 查看，不另开会话。
    ''')
    code('''
    if chat_task is None:
        print("还没有创建会话。")
    elif chat_task.done():
        print("任务已经结束：", chat_task.status)
    else:
        accepted = chat_task.cancel()
        print("取消请求是否成功提交：", accepted)
        print("等待返回的状态：", chat_task.wait(timeout=5.0))
        print("任务是否结束：", chat_task.done())
        if not chat_task.done():
            print("尚未确认结束，请保留句柄，稍后查看。")

    if chat_task is not None and chat_task.status == "FAILED":
        print("错误信息：", chat_task.error)
    ''')
    md('''
    ## 四、用状态机管理会话

    ### 4.1 应用状态与转换条件

    任务句柄提供实际执行状态，应用还要规定用户在什么时候可以操作。程序用 `app_state` 保存这种管理状态。**状态机**由有限的状态、触发条件和相应动作组成。

    | 应用状态 | 含义 | 操作与转换 |
    |---|---|---|
    | 待机 | 没有任务，或旧任务已确认结束 | “开始”创建新任务、保存句柄，转为“会话已发起” |
    | 会话已发起 | 已保存句柄，尚未确认结束 | 可查看；重复“开始”保留旧任务；取消请求提交成功后转为“停止请求已发出” |
    | 停止请求已发出 | 已请求取消，仍需确认结束 | 可查看或继续等待；暂不允许重开；确认 `done()` 为 `True` 后回到“待机” |

    `app_state` 由本课程序维护，`chat_task.status` 由 SDK 依据实际执行情况更新。例如，程序调用 `cancel()` 并收到 `True` 后，可以把应用状态改为“停止请求已发出”；随后仍要检查 SDK 任务是否已进入终态。读取状态、调用 `wait()` 或改写 `app_state`，都不会自行结束会话。

    任务也可能在用户没有按“停止”时因故障结束。管理程序每次处理操作前都要重新检查句柄；发现 `FAILED` 时显示错误，先请教师核查原因，再决定是否重试。

    依据表格画出状态图，给箭头标出条件。重复“开始”及取消请求未提交成功时，应保留在哪个状态？
    ''')
    md('''
    ### 4.2 用函数执行状态转换

    **STEP 06：** 定义管理函数。函数接收操作文字、旧句柄和应用状态，返回更新后的句柄与状态。

    函数先根据句柄核对应用状态，再按“开始、查看、停止”处理操作。“开始”同时要求应用处于待机、旧任务不存在或已经结束。处于“停止请求已发出”时，再按“停止”会继续等待原任务。

    请在代码中找出创建任务、提交取消、阻止重开和回到待机的位置。下面复用了 STEP 02～05 的接口，把它们放进同一个管理函数。
    ''')
    code('''
    app_state = "待机"  # 函数运行时会按旧句柄重新核对状态

    def manage_chat(command, task, state):
        if task is not None and task.status == "FAILED":
            print("旧任务错误信息：", task.error)
        if task is None or task.done():
            state = "待机"
        elif task.status == "CANCELLING":
            state = "停止请求已发出"
        elif state != "停止请求已发出":
            state = "会话已发起"

        if command == "开始":
            if state == "待机" and (task is None or task.done()):
                task = speech.chat(
                    config=ChatConfig(system_prompt=PROMPT, volume=0.5),
                    enable_subtitle_log=True,
                )
                state = "会话已发起"
            else:
                print("旧会话尚未结束，保留原句柄。")

        elif command == "停止":
            if state == "待机":
                print("当前没有需要停止的任务。")
            elif state == "停止请求已发出":
                print("已请求停止，继续等待原任务。")
                task.wait(timeout=5.0)
            else:
                accepted = task.cancel()
                print("取消请求是否成功提交：", accepted)
                if accepted:
                    state = "停止请求已发出"
                task.wait(timeout=5.0)

        elif command == "查看":
            if task is None:
                print("还没有创建会话。")
        else:
            print("操作文字应为：开始、查看、停止。")

        if task is not None:
            if task.done():
                state = "待机"
            elif task.status == "CANCELLING":
                state = "停止请求已发出"
            print("任务标识：", task.trace_id)
            print("SDK 状态：", task.status, "；是否终态：", task.done())
            if task.status == "FAILED":
                print("错误信息：", task.error)
        print("应用状态：", state)
        return task, state
    ''')
    md('''
    **STEP 07：** 每次修改下一格的 `command`，运行一次，完成下列操作：

    1. “查看”：核对 STEP 05 的旧任务是否已结束。
    2. “开始”：确认旧任务已结束后启动新会话，完成问答。
    3. 再次“开始”：比较任务标识，检查是否保留原会话；继续提问。
    4. “停止”，再“查看”：记录请求结果与任务状态。若仍未结束，继续查看或等待，暂不重开。
    5. 确认终态后再次“开始”，检查任务标识并完成问答。

    <font color="red">提示：</font>`chat_task, app_state = ...` 分别接收函数返回的句柄和应用状态，两者都要保存。失败任务重新启动前，先记录错误并请教师检查。
    ''')
    code('''
    command = "查看"  # 每次改成“开始”“查看”或“停止”，再运行这一格
    chat_task, app_state = manage_chat(command, chat_task, app_state)
    ''')
    md('''
    ### 4.3 补写启动条件

    **STEP 08：** 将下一格的 `False` 替换为允许启动的条件表达式：应用处于“待机”，并且没有旧任务或旧任务已经结束。

    在 STEP 07 中每次运行“查看”以更新应用状态后，再运行本格。分别记录会话使用中、请求停止后、确认结束后的判断结果。取消很快完成时，直接记录实际终态，无需设法让取消停在中间状态。
    ''')
    code('''
    can_start = False  # 请按 §4.3 的要求补写；本格只判断，不创建任务
    print("当前是否允许启动：", can_start)
    ''')
    md('''
    ### 4.4 结束练习

    **STEP 09：** 发送停止操作，再查看结果。离开前确认 `done()` 为 `True`。

    等待后仍未结束时，请保留句柄并联系教师检查。代码格执行完或被中断，都不能单独证明后台会话已经退出。
    ''')
    code('''
    chat_task, app_state = manage_chat("停止", chat_task, app_state)
    chat_task, app_state = manage_chat("查看", chat_task, app_state)
    if chat_task is not None and not chat_task.done():
        print("任务尚未结束，请保留句柄并请教师检查。")
    ''')
    md('''
    ## 五、观察与学习评价

    ### 5.1 操作记录

    第三节先填任务信息，第四节再填写应用状态。

    | 操作或观察时机 | 任务标识（末几位） | SDK 状态 / `done()` | 应用状态 | 实际问答或程序提示 |
    |---|---|---|---|---|
    | 首次开始后 | | | — | |
    | 回答完、暂未继续提问时 | | | — | |
    | 有限等待返回后 | | | — | |
    | 登记状态回调后 | | | — | |
    | 语音打断后继续提问 | | | — | |
    | 第一次取消并等待后 | | | — | |
    | 管理函数开始后 | | | | |
    | 重复开始后 | | | | |
    | 停止并查看后 | | | | |
    | 确认终态后再次开始 | | | | |
    | 最后停止并确认终态 | | | | |

    本次 `cancel()` 返回值：______；最终任务状态：______。
    状态回调实际显示了：______。短暂状态没有显示时，按实际情况记录。

    ### 5.2 检查点

    - 能按输入输出解释“听、懂、说”，区分一轮问答与持续会话。
    - 能说明句柄及 `None` 的含义，通过 `status`、`done()`、`wait()` 判断任务情况。
    - 能给状态图的转换写出条件，保留旧句柄，并在确认终态后重新开始。

    ### 5.3 学习评价

    1. 判断：`TaskHandle[None]` 表示 `chat()` 没有返回对象。（　）
    2. 判断：`RUNNING` 表示整个会话正在执行，不能据此确定此刻正在生成回答。（　）
    3. 判断：`cancel()` 返回 `True`，或有限 `wait()` 已返回，都足以证明任务已结束。（　）
    4. 按“开始 → 重复开始 → 停止 → 查看 → 再次开始”画出应用状态转换；在允许再次开始的箭头上写出判定条件。

    ### 5.4 结合记录解释

    1. 机器人说完一个回答、语音打断、程序取消，对本次会话分别产生了什么影响？用实际问答和任务状态支持你的判断。
    2. 为什么“停止请求已发出”还要保留旧句柄？如果任务因故障结束，下一次操作前应先检查哪些信息？
    ''')
    md('''
    ## 六、拓展：模型放在机器人上还是通过网络使用

    使用语音对话前，应向教师了解当前服务配置：哪些处理在机器人端完成，哪些通过网络调用服务。使用联网模型服务时，机器人需要把相关请求发送给服务端，再接收返回内容。采音、播放和模型计算可以部署在不同位置。

    为什么不把模型都直接装在机器人上？部署时需要权衡以下条件：

    | 条件 | 在机器人端运行模型 | 通过网络使用服务 |
    |---|---|---|
    | 计算与存储 | 受本机处理器、内存和存储限制，需选择适配的模型 | 服务端承担相应模型计算，机器人仍负责采音、播放等本地处理 |
    | 连接条件 | 已部署的本地模型可减少对远端连接的依赖 | 服务调用依赖网络连接和服务可用性 |
    | 安装与更新 | 需要在设备上部署、维护相应模型 | 模型可在服务端维护，设备配置也需匹配服务 |

    两种方式都可能受设备性能、模型能力和实际配置影响。结合教师说明的本课配置，指出一个采用联网服务的理由，以及需要检查的一项连接条件。
    ''')

    # 本轮前稿均为未执行的新设计格；若发现真机输出，停止覆盖。
    assert all(not c.get('outputs') and c.get('execution_count') is None for c in original['cells'] if c['cell_type'] == 'code')
    original['cells'] = cells
    NB.write_text(json.dumps(original, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    gen = '''"""U5-L4 第二轮修订：从学生 Notebook 反向同步。
Notebook 为主稿；重建清空输出，不用于覆盖真机记录。"""
import json
from pathlib import Path
OUT = Path(__file__).resolve().parent / "notebooks" / "U5-L4_语音问答闭环.ipynb"
def md(s, cell_id):
    return {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": s.splitlines(keepends=True)}
def code(s, cell_id):
    return {"cell_type": "code", "id": cell_id, "metadata": {}, "execution_count": None, "outputs": [], "source": s.splitlines(keepends=True)}
cells = []
'''
    for c in cells:
        gen += f"cells.append({'md' if c['cell_type']=='markdown' else 'code'}({''.join(c['source'])!r}, {c['id']!r}))\n"
    gen += '\nif __name__ == "__main__":\n'
    gen += f"    notebook = {{'cells': cells, 'metadata': {original['metadata']!r}, 'nbformat': 4, 'nbformat_minor': 5}}\n"
    gen += "    OUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\\n', encoding='utf-8')\n    print(OUT)\n"
    (PROJ / '_gen_L20.py').write_text(gen, encoding='utf-8')
    print(f'已修订 {len(cells)} 格：{sum(c["cell_type"]=="markdown" for c in cells)} Markdown / {sum(c["cell_type"]=="code" for c in cells)} 代码。')

if __name__ == '__main__':
    build()
