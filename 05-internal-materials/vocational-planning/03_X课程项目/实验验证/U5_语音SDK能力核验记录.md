# U5 语音 SDK 能力核验记录

核验日期：2026-10-23。依据为用户指定的官方在线文档及其返回类型链接。本记录核对接口契约，不代表已在机器人上执行新代码。L1～L3 真机确认②沿用用户报告；L4 重构稿待重新审阅和真机验证。

## 一、对课程设计的结论

1. `chat()` 是持续语音会话，返回 `TaskHandle[None]`。所核文档没有公开单轮回答结束事件，也没有单独返回回复文本或 ASR、LLM、TTS 内部阶段。不能用任务结束、任意一条字幕或固定等待时长推断一轮回答已结束。
2. L3 用 `wait()` 保持连续问答，`KeyboardInterrupt` 后取消并有限等待，与官方示例一致。保留用户的实测写法。有限等待之后是否已经结束，仍需根据终态判断；三课已按用户授权补上终态核查和防重复启动，保留原执行信息；新代码待定向补验。
3. L4 已按用户认可方向改为持续会话的启动、查看、取消、终态确认和重新启动。用 `done()` 防重复，不用 `running()` 为假作为可重开的条件。应用状态描述管理操作，不冒充内部“聆听、生成、说话”状态。
4. SDK 确有有限音频识别与文本合成能力。它们可以支持有明确起止的独立任务实验，不能据此认定可以拆解或测量 `chat()` 的内部问答阶段。本轮不把新接口强加进已验证的前三课。

## 二、接口能力与使用条件

| 能力 | 文档明确的输入、输出或行为 | 课程使用注意 |
|---|---|---|
| 音频管理器、音量 | `robot.audio_manager` 访问音频子系统；音量取值0～1 | 调整输出音量不等于调整麦克风灵敏度 |
| 录音 | `start_recording()` 开始；`is_recording()` 查询；`stop_recording()` 返回 `AudioData` | 内存音频需要显式 `save()` 才成为文件；重复开始会报错 |
| 录音时长 | `get_recording_duration()` 返回已录音时长 | 不表示语音识别用时 |
| 分块采音 | `record_stream()` 迭代取得音频块；声道、采样率、采样格式影响每块时长 | 块时长＝字节数÷采样率÷声道数÷每采样字节数；L1 三声道不能照抄单声道换算 |
| 流式播放 | `play_stream()` 返回可写入的 `AudioPlaybackStreamHandle` | `write()` 的音频格式须与播放流一致；队列满时按 `overflow` 等待或丢块，大队列也可能排满 |
| 播放流收尾 | `close()` 结束写入，已写音频继续播放；`wait()` 等待播放任务终态，超时返回当前状态 | 先结束写入，再等待和核查结果；`close()` 本身不表示声音已经播完 |
| 播放流取消 | `cancel()` 请求停止播放并清空队列，返回取消请求提交结果 | 不能把播放流取消当作正常播放完整段音频 |
| 整段播放 | `robot.play_sound()` 接受本地路径、单个 `AudioData` 或有限音频序列，异步返回 `TaskHandle[None]` | `wait()` 后检查成功、失败或取消；不能把 `play_sound()` 归为直接同步播完的接口 |
| 流式识别 | `recognize_stream(on_result=...) -> TaskHandle[None]`；回调参数仅有 `text: str` | 没有 `is_final`；最后一次回调不保证是最终完整句子。固定6秒可以是观察窗口，不能命名为“听清用时” |
| 持续对话 | `chat(config=..., **kwargs) -> TaskHandle[None]` | 任务存续期间可连续问答；任务状态不提供单轮阶段 |
| 对话配置 | `ChatConfig` 有 `voice`、`system_prompt`、`welcome_msg`、`volume` | 人设不自动赋予联网查询、读取本地资料或保证事实正确的能力；官网天气人设属于示例文案，不能单独证明天气查询能力 |
| 语音打断 | `interrupt_speech_duration` 默认800ms；`interrupt_keywords` 默认“停一下”“先别说”“stop” | 打断当前说话与取消整个会话分开观察；不把关键词当作一定结束会话的命令 |
| 其他对话配置 | `enable_face_tracking=False`、`enable_subtitle_log=False` | L4 不启用人脸跟踪；字幕日志可供人工观察，不冒充程序获得的最终回复事件 |
| 音色 | `list_voices()` 返回音色字典，含 `id/name/gender/capabilities` | 根据 `capabilities` 区分聊天和合成可用音色，不默认所有 ID 通用 |
| 文本合成 | `synthesize(text, voice, speed) -> TaskHandle[AudioData]`，文本不超过300字符，自v1.2.0支持 | `result()` 取合成音频，不自动播放；`audio.duration.seconds` 是生成音频长度，不是生成耗时 |
| 有限音频识别 | `recognize(audio) -> TaskHandle[str]`，自v1.2.0支持 | 内存输入须为单声道 S16LE PCM、最长60秒；文件输入支持本地wav/mp3、最大3MB。L1 实测三声道录音不能直接传入 |

### 任务句柄的判断依据

| 接口或状态 | 准确含义 | 常见误读 |
|---|---|---|
| `PENDING/RUNNING/CANCELLING` | 等待执行、执行、取消中的非终态 | `running()` 为假时就允许新建任务 |
| `SUCCEEDED/FAILED/CANCELLED` | 终态，`done()` 为真 | 将所有终态都称为成功，或将主动取消当作故障 |
| `wait(timeout=...)` | 等待终态；超时返回当前状态 | 以为返回就成功，或超时会自动取消、抛出 `TimeoutError` |
| `result(timeout=...)` | 有具体结果的任务成功后返回结果；超时可抛 `TimeoutError` | 用来等待 `TaskHandle[None]` 的单轮回复 |
| `cancel()` | 返回取消请求是否成功提交 | 把 `True` 当作停止已经完成 |
| `error` | 失败时的异常，否则为 `None` | 不区分失败和正常取消 |
| `add_done_callback()` | 整个任务进入终态时回调 | 当成每轮问答完成回调 |
| `add_status_change_callback()` | 整个任务状态变化时回调 | 当成内部 ASR/LLM/TTS 阶段信号 |

`AudioPlaybackStreamHandle.is_playing()`、`has_pending_audio()` 作用于调用者持有的播放流。文档没有将 `chat()` 内部播放流暴露出来，不能拿一个新建的播放流来监测聊天是否说完。任务同组“通常互斥”也不替代应用防重复和句柄保存。

### close与wait的顺序：依据方法定义

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

## 三、哪些时间可以测，哪些不能这样测

- 已知有限音频交给 `recognize()` 后，到成功取得文字之间的程序等待时间，可以定义为该次独立识别任务的处理等待时间。它不含现场录音过程，也不代表 `chat()` 的识别阶段耗时；需要先验证输入格式与版本。
- `synthesize()` 调用到成功取得音频的时间，可以测这次合成任务的等待时间。生成音频的 `duration` 则描述这段声音有多长，两者应分别命名。
- `recognize_stream()` 启动到首次文字回调，可以按明确起止定义为“首次文字返回等待时间”；它不等于整句识别完成时间，还混有学生何时开口等因素。
- 固定6秒监听窗口主要由程序人为限定；`chat()` 启动后等待20秒再取消，主要量得人为保留会话的时间。两者都不能支持原 L4 的单轮或分段延迟结论。
- 人工观察“提问说完到机器人开口”可记录体验，仍需明确定义打点、误差与条件。本轮 L4 不以此替代缺失的机器事件，也不再要求分段延迟验收。

因此，本轮选择会话管理主线有教学和测量依据，同时保留有限音频识别、合成作为其他实验的可用能力。

## 四、对现有材料的处理

- U4-L1：P3 教学设计已编写，未改学生 Notebook；待用户确认④。
- U5-L1～L3：已按真机主稿反向同步 `_gen_L17.py`～`_gen_L19.py`；Notebook 及 L2 附件保持原稿。P2 已完成复核，问题、修改建议和补验范围见[复核与修改方案](U5-L1-L2-L3_P2复核与修改方案.md)。
- U5-L4：Notebook 与 `_gen_L20.py` 已重构；原稿留在本次任务记录中，不再发放。新稿待确认①、②，尚未通过真机验证。
- 本次所有新代码只做离线检查；L4 状态分支使用替身任务测试，不能据此证明设备、音频服务或网络已可用。

## 五、官方来源

以下为2026-10-23读取的页面，缓存位于 `99-task-contexts/20261023-X课程U4U5推进/sdk-pages/`。课程设计以这些具体接口页面为依据，不混用知识库中的旧版本摘要。

| 类别 | 官方页面 |
|---|---|
| 音频入口 | [BoosterAudioManager](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/booster-robot-client-reference/audio-manager/booster-robot-audio-manager/) |
| 音量 | [get_system_volume](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/booster-robot-client-reference/audio-manager/get-system-volume/)、[set_system_volume](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/booster-robot-client-reference/audio-manager/set-system-volume/) |
| 录音 | [start_recording](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/booster-robot-client-reference/audio-manager/start-recording/)、[stop_recording](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/booster-robot-client-reference/audio-manager/stop-recording/)、[is_recording](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/booster-robot-client-reference/audio-manager/is-recording/)、[get_recording_duration](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/booster-robot-client-reference/audio-manager/get-recording-duration/) |
| 音频流 | [record_stream](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/booster-robot-client-reference/audio-manager/record-stream/)、[play_stream](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/booster-robot-client-reference/audio-manager/play-stream/) |
| 整段播放 | [play_sound](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/booster-robot-client-reference/advanced-task-apis/play-sound/) |
| 语音入口 | [Speech](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/vision-and-speech/speech/) |
| 识别 | [recognize_stream](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/vision-and-speech/speech/recognize-stream/)、[recognize](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/vision-and-speech/speech/recognize/) |
| 对话 | [chat](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/vision-and-speech/speech/chat/) |
| 合成与音色 | [synthesize](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/vision-and-speech/speech/synthesize/)、[list_voices](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/vision-and-speech/speech/list-voices/) |
| 任务类型 | [TaskHandle](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/common-data-types/tasks-and-subscriptions/task-handle/)、[TaskStatus](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/common-data-types/tasks-and-subscriptions/task-status/) |
| 播放流类型 | [AudioPlaybackStreamHandle](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/common-data-types/tasks-and-subscriptions/audio-playback-stream-handle/)、[OverflowPolicy](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/common-data-types/tasks-and-subscriptions/overflow-policy/) |
| 音频数据类型 | [AudioData](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/common-data-types/sensor-and-state-data/audio-data/)、[PcmSampleFormat](https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/common-data-types/sensor-and-state-data/pcm-sample-format/) |

## 六、U5-L4第二轮：只读状态与应用状态机

2026-10-23再次回读TaskHandle、TaskStatus和chat的官方页面：status、error为只读；wait超时返回当前状态，不会自动取消；cancel返回是否成功提交请求。TaskHandle[None]仍是句柄，只是没有供程序领取的最终结果数据。

add_status_change_callback(fn)接收任务句柄，注册时立即以当前状态触发一次，后续状态变化时再调用；注册前已发生的短暂状态不会补发。本课回调只打印，不修改管理状态或调度其他任务。当前Notebook环境的后续回调输出位置待真机核实。

应用状态机可根据操作与旧任务是否终止来决定调用chat或cancel；SDK按实际执行情况更新任务状态。读状态、调用done或wait、修改应用字符串，都不会直接设定SDK状态。不主动取消时仍可能发生启动或故障等生命周期变化；公开文档未给出持续聊天的全部自然终止条件，不能承诺永远RUNNING，也不推定静默后自动停止。

L4第二轮未使用recognize()。该接口在本记录中作为官方能力索引保留，不表示加入课程。学生稿27格，新增状态观察与真实操作控制，待新确认①②；教学取舍、接口依据与逐格测试见[教学审阅与真机验证建议](U5-L4_教学审阅与真机验证建议.md)。本轮未连接真机或核验SDK实现源码。
