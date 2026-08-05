# Chapter\_03\_机器人控制基础与SDK

# Chapter 03｜机器人控制基础与 SDK

## 3\.1 机器人本体操作基础

前两章已经建立了课程目标和 K1 系统架构。从本章开始，课程进入机器人控制部分。机器人控制是后续所有任务的基础：机器人只有能够被安全启动、正确连接、稳定进入运动状态，后面的相机感知、动作生成、追球控制和视觉踢球才有实践基础。

本章要完成一个关键转变：从“会操作 K1”进入“会开发 K1”。前者依赖手柄或 App 完成基础操控，后者需要通过网络连接、远程登录、开发环境和 SDK 调用，让程序成为控制机器人的入口。

这个转变不能跳过机器人本体操作。人形机器人不是屏幕上的仿真对象，任何控制指令最终都会作用到真实身体上。开机顺序、运行模式、站立状态、周围环境和停止方式，都是代码控制之前必须确认的条件。

本章的学习路径可以概括为：

```Plaintext
安全开机
  ↓
理解运行模式
  ↓
完成手柄或 App 基础操控
  ↓
连接机器人系统
  ↓
准备开发环境
  ↓
调用 SDK 控制接口
  ↓
运行 Hello Robot 程序
  ↓
验证基础运动结果
```

图 3\-1 待补充：从本体操作到程序控制的流程图。左侧展示手柄/App 操作机器人，右侧展示电脑通过 SSH、VSCode Remote 和 SDK 控制机器人。

### 3\.1\.1 开机与安全红线

K1 开机不是简单按下电源键，而是一次安全流程的开始。开机后，机器人会启动主控、初始化传感器和控制程序。后续是否能稳定站立、行走和执行动作，都依赖开机阶段的状态是否正常。

本课程建议按以下步骤完成开机：

1. 将机器人放置在安全位置。开机前，让机器人脸朝下、趴在地面或软垫上，四肢自然放置，周围不要站人。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTQ1YWVlMThjYTlkNTdjMjJlNTVmMTc0Mjc1NTFlNjZfMzhlNzIyYmJmYTAyZWFlMGEyYjRkZjA0ZDhlY2RkMzJfSUQ6NzY2MDAxMjYzMDExOTI3MTYzM18xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

2. 确认电池已经安装牢固，电量足够支撑本次实验。

3. 找到机器人背部的圆形电源按钮。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OTcwZTU0NTUyNzEwZDI5YjIyODdhYWY0MjdkNmE0NDRfYTQ4NWNiNTI0OWJiNTFjYTVhMTY4NGQwYWUxYTBlOGJfSUQ6NzY2MDAxMzI5ODY5MTYyNDE4MV8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

4. 长按电源按钮约 3 秒，指示灯亮起后松开。不要长按超过 6 秒，长按过久可能触发关机。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTdkOGZlZGJjNDNlMDMzN2VkNThjOWM2NjU2NjdiOWZfOGM4NzRjNjg0YTcwOGJjOGU1YjFjNDFjZTk1NjRhNDVfSUQ6NzY2MDAxMzM4OTkyMjM3MjU5NV8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

5. 开机后保持机器人静止，等待约 1 分钟。

6. 听到机器人提示音后，表示机器人启动完成，各部件初始化完成，可以进入后续模式切换。

开机后需要等待，是因为机器人需要完成主控启动和 IMU 初始化。IMU 是 Inertial Measurement Unit 的缩写，通常译为“惯性测量单元”，用于感知机器人姿态变化。初始化阶段如果机器人被搬动、晃动或姿态不稳定，可能影响后续站立和运动控制。

### 3\.1\.2 运行模式：阻尼、准备与行走

K1 的运行模式可以理解为控制系统对关节发力、姿态保持和运动能力的不同配置。学习模式切换时，不能只记住按钮名称，还要理解每个模式下机器人身体发生了什么变化。

K1 背部除了圆形电源按钮外，还有 `WALK`、`STAND`、`F1` 三个常用按键。其中：

- `F1` 默认用于进入阻尼模式；

- `STAND` 用于进入准备模式；

- `WALK` 用于进入行走模式。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MmI4MzBhM2YxZTUyYzgwOWJhMjM1YjNhODFmOTYwNWZfNzc3Y2E3OTRiZWE4ZDAwYzk2YmI2OWE1MmVkNDc4NDFfSUQ6NzY2MDAxNDc4NjcxMDI2MDkzN18xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

开机后，机器人首先应按阻尼状态理解。阻尼模式下，所有关节不会主动保持姿态，只会表现出一定阻力。此时机器人不能自己站立，通常需要趴在地上、放在支撑物上或由人员安全扶持。

阻尼模式的作用是让机器人处于相对安全的放松状态。它不是“完全断电”，而是让关节不主动发力，避免机器人在未准备好时突然做动作。如果后续想手动切换到阻尼状态，可以按背部 `F1` 按钮。关机前，也可以从行走模式直接按 `F1` 回到阻尼状态，再执行关机操作。

下一步是进入准备模式。按下背部 `STAND` 按钮后，机器人会进入站立准备状态。此时全身关节会明显变硬，不能像阻尼状态下那样被随意摆动，身体会尝试保持站立姿态。可以手动提起背后的拉绳，将机器人从趴地状态拉起，让双脚接触地面并站稳。

准备模式下，机器人可以站立，但还没有开启完整行走运动控制。此时机器人能保持姿态，但不能承受较大推搡，也不应被当作已经可以自由行走的状态。操作人员应站在侧后方，确认双脚平稳落地、身体没有明显前倾或侧倾。

图 3\-6 待补充：从阻尼模式拉起机器人进入准备模式的过程图。建议展示背部拉绳、双脚落地和站立姿态。

确认机器人站稳后，按下背部 `WALK` 按钮，机器人进入行走模式。行走模式下，运动控制程序开启，机器人可以响应行走、转向、转头等控制输入。此时如果轻轻推机器人，机器人会尝试通过控制身体恢复平衡。

图 3\-7 待补充：K1 行走模式下的标准站姿图。建议展示机器人双脚站立、身体朝前、周围留出安全空间。

三种主要状态可以这样理解：

|状态|操作方式|机器人表现|适合做什么|
|---|---|---|---|
|阻尼模式|按 `F1`|关节有阻尼，不主动保持姿态，不能独立站立|安全放置、准备关机、异常后放松|
|准备模式|按 `STAND`|关节变硬，机器人保持站立姿态|拉起机器人、短暂停止、确认站姿|
|行走模式|按 `WALK`|运动控制开启，机器人可以行走、转向并尝试保持平衡|手柄行走、SDK 基础运动控制|

正确顺序是：

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MWE4OWE2ZTM0N2Y2Yjc4ZWRlZDQxYzVlMDM2MGNlYzlfOTMzZjA1NWJlMzU0OGE3NmYxZTcxMzMyNmQ4MmEwMDVfSUQ6NzY2MDAyMDY5NDIyNjUyMTA0MF8xNzg1ODM5NDIzOjE3ODU5MjU4MjNfVjM)



```Plaintext
开机
  ↓
阻尼模式
  ↓ 按 STAND
准备模式
  ↓ 拉起并确认站稳
  ↓ 按 WALK
行走模式
```

如果需要快速停下当前运动，可以按 `STAND`。如果需要放松关节或准备关机，可以按 `F1` 进入阻尼模式。

**本章所有上机操作必须遵守两条最重要的安全红线**。

**第一**，模式切换顺序不能错。机器人必须先从阻尼状态进入准备模式，再进入行走模式。不能从阻尼状态直接尝试进入行走控制。阻尼状态下机器人通常还趴在地上或需要支撑，如果直接进入行走控制，机器人没有稳定站姿和地面反作用力支撑，可能出现异常动作或摔倒风险。

**第二**，行走模式下不能把机器人提起来挪动位置。行走模式已经开启运动控制，机器人会尝试维持自身平衡。如果此时把机器人提起，机器人可能为了恢复平衡而出现腿部乱蹬、关节快速运动等情况，容易踢伤人员，也可能损伤机器人。

如果想让机器人快速停止当前运动，优先按下背部 `STAND` 按钮，让机器人回到准备模式。准备模式下机器人会站立并保持姿态，适合作为短暂停止和重新确认状态的安全过渡。若需要让机器人彻底放松关节或准备关机，可以再按 `F1` 按钮进入阻尼状态。



### 3\.1\.3 手柄操控

手柄操控用于确认机器人本体和运动控制是否正常。第一次进入程序控制前，建议先用手柄完成一次最小运动流程：准备模式、行走模式、小幅行走、停止。

手柄使用前，先确认手柄已经开机并成功连接。

- **Booster 手柄**长按 `Home` 键约 5 秒开机；开机瞬间 `LED1`、`LED2`、`LED3`、`LED4` 会同时亮起，开机完成后 `LED1` 常亮。看到 `LED1` 常亮，说明手柄已经进入可用状态。

- **若使用 Xbox 手柄**，需要确认手柄处于接收器模式，且工作模式指示灯为三个灯常亮。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YzUzYmQxMzQwZDMzMDVkZTU2NjQ3M2VlNGZkYjkyMDVfYmJlZGRjZTc4Y2ZmN2YxMzg3NTFhMzFjZTljMjNlMjRfSUQ6NzY2MDAyMjIxODY0MjE0ODI4MF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

1\.接收器模式指的是：上面两个开关要在“长程”处，下面的开关在最右侧

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZDcyMTM2OTBhNTNiNzhiNzcyZTY1NmE0N2Y3YTQ3MGVfYjVjMTdhYTY3NmIyYTUzN2M4MGViNmZiYmUyYjU0NjJfSUQ6NzY2MDAyMjIzMjMxMTMwMzEwOF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

2\.开机为点按手柄正面的“房子”图标

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTU0MjExY2Y3NTNlNTY1MDA1NDcxMDBkNGIzN2JhM2ZfOGUyZWUwNzIyZDE3NDljYTNlMmM1ODQxMzJlNjc2NDhfSUQ6NzY2MDAyMjE4MTI1NDA3MzUzMF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

3\.三灯常亮为连接成功。

手柄基础操作如下：

|操作|Booster 手柄<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OTM4YTdjMmU1ODk2MGMwNzM5NjQ3NzQ5Y2Q3NmEwNjdfYzg2YzljNTRhYTRjOTYwYTMwMTUwY2ZmZjVmYTU3M2RfSUQ6NzY2MDAxNjQxNTc1OTg5NTc5MF8xNzg1ODM5NDIzOjE3ODU5MjU4MjNfVjM)|Xbox 手柄<br>![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YmI1MjdhNGI0ZmM5YzllYTE1OTExOTIwNWY0YzljMTNfZWVhMTUyMTlhOWI0MDQzZmE0NjI3YWQ5MDdmZjFlYWRfSUQ6NzY2MDAxNjM3OTEwNTQ0Njg2Ml8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)|前置条件<br>|
|---|---|---|---|
|进入阻尼模式|`L2 + Back`|`LT + Back`|任意安全状态下|
|进入准备模式|`L2 + Start`|`LT + Start`|机器人已开机并稳定放置|
|进入行走模式|`R2 + A`|`RT + A`|机器人已处于准备模式|
|行走控制|左摇杆|左摇杆|行走模式下|
|转身控制|右摇杆|右摇杆|行走模式下|
|头部转动|方向键|方向键|行走模式下|

第一次手柄操控建议按以下步骤执行：

1. 确认机器人已经开机，并处于安全放置状态。

2. 按 `STAND` 或使用手柄组合键进入准备模式。

3. 拉起机器人背部拉绳，让机器人双脚落地并站稳。

4. 按 `WALK` 或使用手柄组合键进入行走模式。

5. 轻推左摇杆，让机器人向前小幅移动。

6. 松开左摇杆，观察机器人是否停止。

7. 轻推右摇杆，让机器人小幅转身。

8. 松开右摇杆，观察机器人是否停稳。

9. 按 `STAND` 让机器人回到准备模式。

10. 如需放松关节或结束操作，按 `F1` 进入阻尼模式。

手柄操作的意义不是替代程序控制，而是建立对机器人运动状态的直观认识。后续 SDK 中的模式切换、`Move` 指令和停止逻辑，都可以与手柄操控中的站立、行走和停止现象对应起来。



### 3\.1\.4 App 连接与基础控制

App 适合完成机器人配网、状态查看和基础控制。相比手柄，App 更强调连接和状态管理；相比 SSH，它更适合快速确认机器人是否在线、网络是否配置成功、当前设备是否可被访问。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZThmYTk4NTFiNTViMzc2ZDg3NTA2MDhlYWY1NjRjZWNfN2U1NzA3ZmEyMDExMzAxMjc5Nzg0NGQ3YzBmMzQzMTVfSUQ6NzY2MDAxNzM4NzQ5MTk3MDI4Nl8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MDc4MDRkNjdkMTcwZTIzNzY5ODQ3MWM2NTcyNTcyOWZfOWYwNDY1ZDM1YzhjNDNmODIxZDJhOWQ1N2Y1OTIzMjVfSUQ6NzY2MDAxNzQxNjk4MTcyODIxMl8xNzg1ODM5NDIzOjE3ODU5MjU4MjNfVjM)

App 安装完成后，可以按以下步骤连接 K1：

1. 打开 App，点击“连接机器人”。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YWUxMGQxMjcxZDQyYjk5ZDdkMmY1NDliNWNlOGNiMThfNzJjYWVhN2RkZjdkM2UxNGFmZTgwZGMyM2EzODE0OTFfSUQ6NzY2MTkxNDE3NjM0ODMyNjg5NV8xNzg1ODM5NDIzOjE3ODU5MjU4MjNfVjM)

2. 点击“发现设备”，先使用蓝牙为机器人配置无线网络。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDUxMmY0NDk4MTIzZWY5ZmU4NTE4OTU3YWVmZGZkMjdfYTkwZmExODIwMDE2OTAxOTYxNDAxZGNjNDM1YzU5YTZfSUQ6NzY2MTkxODk4NjUxODUzMTI3NV8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

3. 在设备列表中按照编号选择对应的 K1。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzdlYTJmZTAzZGNmMDFmMWE1OGY4ZjgxMmNhOWZjMDlfMTMwM2ExMjczMGRhMjg2MDVlMzhlMzZkYzg3MTQ2ZWVfSUQ6NzY2MTkxODMxMjg4OTUxOTA3MV8xNzg1ODM5NDIzOjE3ODU5MjU4MjNfVjM)

4. 选择Wi\-Fi 连接模式后，选择与手机相同的无线网络，并输入无线网络信息。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTAzYzJhYWI0OTk2NTBiMzg2NjVkNmRkZjc3YjhkMzhfMDI1OTkwODFiODhmMjM4YzE4NjA5OTk3ODBjZjE3ZmZfSUQ6NzY2MTkxNTQ5ODIyMTc4NDAyM18xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=N2M3MDk5NTg1MGM2MTZlNTljMGYxN2JiZDhhYjQ0ZDlfMWIzNDYwN2U0MDM1M2IwZjkyYzkzYTc2NDdkYmNjNDVfSUQ6NzY2MTkxNTUzMzY5MjIxMDEzNV8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

5. 等待网络配置完成。

6. 返回首页，点击已联网的 K1 进入控制页面。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OThhMmNkN2Q5MmFhNWVkMTI0Nzk2YTZlMjU4YjA3MThfOGZkMGExZDA3NGUwZjQ3ODVjODliZDRjNTJiYzk1OWJfSUQ6NzY2MTkxOTcwNzIwNTgzMTg1OV8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

7. 查看机器人在线状态和 IP 地址，注意无线连接每次机器人开机会有不同的IP地址。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OTE4YTEwODg1OWM0ZmNiMTg2NzYzMmQzNjMzMjcyMjFfNjQzMGU2NGMxOWIwYmJlMmQ0YzBlZWUzMzEzZjYzOTJfSUQ6NzY2MTkxNjE5MjY0NjU0ODY5OF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

8. 可以通过App切换Agent，运行机器人本体自带的多项Agent能力，可进入足球大师模式，体验头部盯球、追球、射门功能。这三个功能都是后面章节通过代码实现的最终效果。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YTA1MWFjNTk3ZGRlMWYyNzU1NWI0OGU0YzI4NDI1MDlfN2MzOGE1Y2MwZTEzNDhmMjYzNmNhZjg5MjA0ODBlYWVfSUQ6NzY2MTkxNjkxNzM0Nzg4MDEzNl8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YmI5MTU3MWQzY2U4ZmEwZDNlOGUxMjAxOTM5OGRjYjVfOGM2ZDhmOTllMTM4Yzk5YmVhNjg1YWYyYmFkNzFjZjBfSUQ6NzY2MTkxNzE5ODQ5NjM1MzQ3NF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

App 在本章中的主要作用包括：

- 配置机器人无线网络；

- 确认机器人是否在线；

- 查看机器人当前 IP 地址；

- 执行基础控制或重启操作；

- 辅助判断机器人是否处于正常连接状态。

App 连接成功后，下一步通常是让开发电脑通过网络访问 K1。也就是说，App 解决的是“机器人连上网络并暴露可访问地址”的问题，而 SSH 和开发环境解决的是“进入机器人系统并运行程序”的问题。

## 3\.2 开发环境准备

完成本体操作后，下一步是进入开发环境。开发环境准备的目标不是安装尽可能多的工具，而是建立一条稳定链路：

```Plaintext
开发电脑
  ↓
网络连接
  ↓
K1 系统
  ↓
代码编辑
  ↓
程序运行
  ↓
状态观察
```

本章需要完成四件事：确认网络连接、通过 SSH 登录、使用 VSCode Remote 开发、通过 Booster Studio 观察状态。它们的顺序不能随意调换：先让电脑能访问机器人，再登录机器人系统；先确认能登录，再配置远程开发工具；先确认状态可观察，再运行控制程序。

### 3\.2\.1 网络连接与 IP 确认

开发电脑要控制 K1，首先必须和 K1 建立网络连接。常见连接方式有两种：有线连接和无线连接。初次上机调试建议优先使用有线连接，因为链路更稳定，IP 更固定，也更容易排查问题。

有线连接按以下步骤完成：

1. 找到 K1 机身上的有线网口。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZjM0ODUwNzFkZmI1MGUyMjMzZGM3ZWEyNWI4ZmYyZWJfMWFiZTQzNmNhN2E0MDIyNTQyNTVhZGM1ZmIxNzBiYzhfSUQ6NzY2Nzg0NzgzMDkwODUyMTQzMV8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

2. 使用网线连接开发电脑和 K1。

3. 在开发电脑的网络设置中，找到当前使用的以太网卡。

4. 将 IPv4 配置方式改为“手动”。

待补充：开发电脑手动配置 IPv4 的截图。建议分别保留 macOS、Windows 或机房系统实际界面的截图位置，标出 IP 地址、子网掩码和网关。

5. 按下面的参数填写开发电脑的有线网卡地址。

```Plaintext
K1 IP：192.168.10.102
电脑 IP：192.168.10.10
子网掩码：255.255.255.0
网关：192.168.10.1
```

这里的关键不是记住某个界面，而是理解网络关系：K1 的以太网卡固定IP地址是 **`192.168.10.102`**，开发电脑要配置成同一网段内的另一个地址，例如 **`192.168.10.10`**。两者前三段 **`192.168.10`** 相同，最后一段不同，表示它们处在同一个局域网中。

无线连接适合已经通过 App 完成配网的场景。无线连接按以下步骤完成：

1. 使用 App 为 K1 配置无线网络。

2. 在 App 控制页面查看 K1 当前 IP 地址。

3. 让开发电脑连接到同一个无线网络。

4. 记录 App 中显示的 K1 IP，后续 SSH 和工具连接都使用这个地址。

如果学校网络开启了客户端隔离，手机能看到机器人不代表开发电脑一定能访问机器人。此时应优先换回有线连接，或请网络管理员确认同一无线网络内的设备是否允许互相访问。

确认 IP 后，可以进入电脑终端，用 `ping` 测试网络是否连通：

```Bash
ping 192.168.10.102
```

如果使用无线连接，把命令中的地址替换成 App 中显示的 K1 IP：

```Bash
ping <K1_IP>
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZWM5Njk5ZDE0NzkyNjUxYTNjNTg1Y2RiMDU4YTY0OTRfM2NiYjQwMzZlMDY2ZTViYTcyZmNlYTljNDYyNWRhY2RfSUQ6NzY2MTkyMzA1MjAyODQ0NzkyMl8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

如果终端持续返回类似下面的响应，说明开发电脑能够访问 K1：

```Plaintext
64 bytes from 192.168.10.102: icmp_seq=1 ttl=64 time=0.5 ms
```

如果出现超时，需要按顺序检查：

- K1 是否开机；

- 网线是否连接正确；

- 开发电脑有线网卡是否配置为 `192.168.10.10`；

- K1 IP 是否写成了 `192.168.10.102`；

- 无线连接时，开发电脑和 K1 是否在同一个网络；

- App 中看到的无线 IP 是否与命令中的 IP 一致；

- 防火墙或网络策略是否阻止访问。

### 3\.2\.2 SSH 远程登录

SSH 是 Secure Shell 的缩写，通常译为“安全远程登录”。它的作用是让开发电脑通过命令行进入 K1 的 Ubuntu 系统。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YjE1YWVlNmE2NTljYjdmMTAwNmNhMGMzMWQ2MmMzYmRfNjE5MGM0MTk0Mzc1MDc5ZTI0NDkxYjhjZWVhYmY3ODZfSUQ6NzY2MDAyNTI2MDQ4MTUzMTA5Ml8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ODY4MjIxMmMxYmVmNTQ0NmNiMjBhODQwZTI0ZTJmZDVfOWI2MWQzZjJjMGNmMDRiMWIxZDJjMWE0YmUxMWY3YWVfSUQ6NzY2MDAyNTMwNDY3Mjg0ODg1MF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OGUxNjkxMjg1OGVhNzE0ZWJmNTYyN2U2MTJkMDYyOTBfZDBkN2JkMmM2ZjFhZGQzODY3MzQxM2ZkZDBiMGY3YTZfSUQ6NzY2MDAyNTMzNzg4OTM0NDQ4MV8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

网络连通后，打开开发电脑终端，输入：

```Bash
ssh booster@192.168.10.102
```

第一次连接时，终端可能会提示是否继续连接，输入 `yes` 后回车。随后输入初始密码：

```Plaintext
123456
```

如果通过无线网络连接，应把命令中的 IP 替换为 App 中显示的实际 IP：

```Bash
ssh booster@<K1_IP>
```

登录成功后，终端就进入了 K1 的命令行环境。可以用以下命令确认当前用户和路径：

```Bash
whoami
pwd
```

如果 `whoami` 输出 `booster`，说明当前登录用户正确。`pwd` 会显示当前所在目录，通常位于 `/home/booster` 下。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YmJkOWJlMDFhYzFiOWVkYjcyYzY3MzAyYzAxNDZkNTlfZjk4NjFmMThkMzIzOGM2NmE2ZmJkNzI2YmY0Zjc1YjRfSUQ6NzY2MTkyNDg1NDA0OTAxNzA2Ml8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

SSH 的价值在于直接、高效、稳定。后续运行 Python 程序、查看文件、启动 ROS2 节点、检查日志，都可以通过 SSH 完成。ROS2 是 Robot Operating System 2 的缩写，通常译为“机器人操作系统 2”，后续章节会围绕具体任务逐步使用。

第一次使用 SSH 时，读者只需要掌握三件事：

1. 能否通过 IP 访问 K1；

2. 能否成功登录 K1；

3. 能否在 K1 内运行基本命令。

不要把 SSH 理解成复杂的 Linux 学习门槛。它只是进入机器人系统的远程入口。后续所有命令都会围绕具体任务逐步使用。

### 3\.2\.3 VSCode Remote 开发

SSH 适合运行命令，但长时间编写代码并不方便。VSCode Remote 是 VSCode 的远程开发功能，可以让读者在本地电脑中打开 VSCode，同时编辑 K1 系统中的文件。

推荐安装顺序如下：

1. 先安装 VSCode。

2. 再安装 VSCode 中的 Remote\-SSH 插件（同样的方式再补充安装Chinese、Python插件）。

3. 确认普通 SSH 已经能登录 K1。

4. 最后在 VSCode 中创建 K1 远程连接。

VSCode 安装地址：https://code\.visualstudio\.com/

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YmUwYmIxMTIzNTRkYjJlNTgxYWQ2MTYyNGYxZTVlZThfNDI2MDBlYTNiZGM0NmRhM2I0OTczMjZkNDYyNWY0N2NfSUQ6NzY2MDAyNjU5MDY1MjMwNDM0M18xNzg1ODM5NDIzOjE3ODU5MjU4MjNfVjM)

Remote\-SSH 插件可以在 VSCode 扩展面板中搜索 `Remote - SSH` 安装。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MzMzNjAzNGE3ODUzMzcyOWM4OGZmMTMzNWYxZDc2ZmRfMTU2Zjk3NDQyNWEzZmVmZWE5MjZiNzU0ZmU3MmJmNGFfSUQ6NzY2MDAyODc5Njc1Nzc0MDc0NF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ODgwNmM1YjlmYmUwYjIwMTVlZjk0YzkyNjU0YWYyYTZfNDc4YzYwZTkyZTRhYjI0ZTEyYTk5ZTI4NWY0YWYwNDBfSUQ6NzY2MDAyODkyNjg3NzgzMDMzMF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NmQ2MDdhMTA4M2FjOWY3NDc5OGJkYWVhMjA1NjIyNThfOTUyZDFlNjZkM2I5MWViZThmOTE0NDE3ZjZhOTVhZWNfSUQ6NzY2MDAyODk5MTQ3NDA0MzgzNl8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZGU3ZWM3YmMxMDIwMzYwNzQ1ZGFkZThkYzFiYzY0YjJfMTQzODExNWEzOTYyMGJmMWNkM2EwOWZjMjdiNTQxZmJfSUQ6NzY2MDAyOTU2NjM5NjM4NjI1N18xNzg1ODM5NDIzOjE3ODU5MjU4MjNfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NGQxNTNlNTAyYjNmMTVlM2JmNjE5NDRjY2E5NjRlYzlfNGUwODA1MDI5ZTU3M2NjYzYwMTE1NjQ5MzE4MmQyZDdfSUQ6NzY2MDAyOTcwMTIyNjEwNTgwOF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

VSCode Remote 的作用可以概括为：

```Plaintext
编辑界面在本地电脑
代码文件在 K1 系统
运行终端连接 K1
```

基本流程如下：

1. 打开 VSCode。

2. 点击左侧远程资源管理器，或通过命令面板选择 `Remote-SSH: Add New SSH Host`。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OGI4N2JjMjIwYWVlMmZmMjFkNTFhNzJmMWY0MmJhZGNfNDczZmZiNjViM2UzZDZjMDViZmY5MTc4MDFiMTlmYjNfSUQ6NzY2MTkyODUxMzkzNDk2OTc5NF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

3. 输入连接命令：`ssh booster@``<K1_IP>`。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=N2VhZjAxZDAxODRhOGMzNDRjNDdiOWE0NmJlNjVhZDdfZGJkZjQ2ZDc5YTM4Y2U4MTYyYTUyMmQ2MmMwZTlhMjFfSUQ6NzY2MTkzMDAyNzA0MzQ5MTA5OF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

4. 选择保存到默认 SSH 配置文件。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NGJiZTI4OTZiNGY2YzZkYmVhNTAyOTEwZGQ1ZDY0MzBfYWIwYzJlZDUyY2I0OWQ1NDI0YmFmNzFmNmQzMjM5YmNfSUQ6NzY2MTkyODc4NjgyNTI1MTgxM18xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OWNjNDg2MTM2YWJhMTBkOTFhZDFjMWFkMzlmMzYxOTlfN2JmZWM5NGEyZWE4OWFlMzM2YjI4OWNiNTE2NTQ1ZGZfSUQ6NzY2MTkyODg2MzQzMzQxMTc4Nl8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MWIzZTM4ZGM3ZmU2YzBjMTZkZWY1N2NkMTc1ZmJjN2FfNmVjZTc1NTVmNGJkOWQ4OWVjYTQzNzNkMTVlZTIyMzlfSUQ6NzY2MTkyNzYwMjg2NTYyMTk2NF8xNzg1ODM5NDIzOjE3ODU5MjU4MjNfVjM)

5. 根据提示输入密码 `123456`。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MDU2NjYwNGFkYzdmZWRkNDkzMTM2MzUxZDM0NGY1MDRfNjU1NzM3MzNiODA3MmE4NmY2MTFiMWViMTUyZmJlYzNfSUQ6NzY2MTkzMDkzNjMwOTUxNzYwMl8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

6. 连接成功后，选择打开 K1 内部的课程开发目录。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTg5ODM1YjliNjU0OTVhMGQxYmJmZjZjZjExYzgxZDVfNGMzZTIyMTE1MjM5NjY4OGFmNDAzN2UzMTU0YzBlZDJfSUQ6NzY2MTkzMTYxMzkyNDQyODczOF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

连接成功后，建议将课程代码放在用户工作目录下，例如：

```Bash
/home/booster/Workspace/
```

不建议初学阶段随意修改系统目录，例如：

```Bash
/opt/booster/
```

系统目录通常包含机器人运行程序、核心配置或服务文件。课程开发应优先在独立工作目录中完成，避免误改机器人系统环境。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YjM2NTcxZWY0OTdiMmI5NWQyMWI1MDczZmYxMzcxMzdfNTYzZWNmMjAwNmIxMzMwYTQzZGM5MjE0MTAwNTcwOGFfSUQ6NzY2MTkzMjU2Mjc4MDc1Mjg0Nl8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

### 3\.2\.4 Booster Studio 状态观察

写机器人程序时，不能只看终端输出。机器人是否在线、是否处于正确模式、电量是否充足、关节状态是否异常、相机图像是否正常，都需要通过状态观察工具辅助判断。

Booster Studio 是 K1 控制和调试过程中的可视化窗口。它可以用于查看机器人状态、图像、话题、速度、电机温度、电机通信状态和电池曲线，也可以辅助观察程序运行后系统是否发生变化。

Booster Studio 安装包地址：https://studio\.booster\.tech/。

安装完成后，按以下步骤连接 K1：

1. 确认 K1 已经开机，并且开发电脑可以 `ping` 通 K1。

2. 打开 Booster Studio。

3. 点击左侧第二个图标，点击连接机器人。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YjlmNDk5YThjMzgwNDg0NjJkNTYwMWIwMTlmN2FhOGJfNzk1YTExMjdkOWM5ZjIwOTcwNDVmNjU4MGMzYTYzMTdfSUQ6NzY2MDAzMDk2Njc1NjgzODM2Nl8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzEwOTEwYWVjN2E0MDQzOGMyN2FkODRmMjk0MTYyMTRfNjJlYzJlZDJjZjMwNzkwZDk0OTc1OGYyYzM0OTQzMjVfSUQ6NzY2MDAzMTE1NzczNjU0MTM4OF8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

4. 点击连接Booster 机器人，在列表中核对设备名称后，点击对应的机器人。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTYwZDY2OTZmZjdmODcwYjBjNGIyN2M1NjkxNTMwZGRfZGM5MzczN2M2MTVhMDM2NGI5NWEwNzFkZjk2NGNiZTVfSUQ6NzY2MDAzMTMwOTQ0ODc0NDE0M18xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=N2I5NGQyOWMwMzQyOWY4ZWVjNzNhNjIwMmYwNTBiNDJfNTU3YzUzNzcyNzU3Y2ExMjM4ZGViNGZjM2NlOTE3Y2ZfSUQ6NzY2MDAzMTYxNjQ0MTc4MTIzMV8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

5. 输入用户名booster，密码123456，点击确定。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTVkNTJlN2QxM2FhMTNlZTk2NjkyZGJiYmIwYzNhZDZfMWFjOWQ1YWYwZTQ1OTJmMjE2MzgwMjIxYjhlZjNlZDJfSUQ6NzY2MDAzMTcwOTMyMDcxMTEwNl8xNzg1ODM5NDIzOjE3ODU5MjU4MjNfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTU5ZTBkZTYxYjFlMTRkNDViODk5MmRmMjk3YjIzMjRfMzYwMTFlZGQyNGFjMDZkZDk5YjY5MzYzNjE3MzE3MzlfSUQ6NzY2MDAzMTc2OTgyNzc3MzQwMV8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

6. 查看相机画面、机器人状态、电池状态、电机状态或话题数据是否正常。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzcwMjM3ZTIyMDZiMzQ4NWNhNDA5MDgyNDljNWMxOWVfZTFhNDcxZDdlNTA1NDg4Zjk1NmNjOTE4MGE5MTU5YWJfSUQ6NzY2MDAzMTg0MjcyNDY5NDk3Nl8xNzg1ODM5NDI0OjE3ODU5MjU4MjRfVjM)

在本章中，Booster Studio 主要用于：

- 确认机器人在线；

- 查看相机画面是否正常；

- 观察电池和电机状态；

- 查看话题或数据是否变化；

- 辅助判断控制程序是否真的作用到机器人；

- 在运行控制程序前确认机器人状态。

机器人控制程序不应该“盲跑”。每次运行前，都应先确认机器人状态；运行时，应有人观察机器人动作；运行后，应确认机器人已经停止或回到安全状态。

## 3\.3 SDK 控制接口

完成本体操作和开发环境准备后，可以进入 SDK 相关内容。SDK 是调用机器人能力的重要入口。通过 SDK，可以完成模式切换、行走控制、头部控制、预置动作调用等任务。

本节学生无需一下子理解全部SDK接口清单，只需要先建立应用 SDK 控制机器人的基本概念，包括连接机器人、确认状态、切换模式、发送控制指令、观察执行结果、停止或返回安全状态。

### 3\.3\.1 SDK 的作用

SDK 可以理解为上层程序调用 K1 能力的一组接口。读者不需要从电机控制、步态生成和通信协议开始写起，而是可以通过 SDK 直接使用已经封装好的机器人能力。

在本课程中，SDK 主要承担三类作用：

|作用|示例|
|---|---|
|状态与模式控制|切换准备模式、行走模式、阻尼模式|
|基础运动控制|前进、后退、左右移动、旋转、停止|
|动作能力调用|挥手、握手、舞蹈、起身等预置动作|

SDK 的设计初衷是为了降低了开发的入门难度，读者需要理解机器人当前处于什么模式、控制指令会作用到哪里、动作执行是否安全、停止逻辑是否可靠。

从系统层面看，SDK 位于软件层和控制层之间。上层程序通过 SDK 发出请求，底层控制系统再把请求转化为机器人身体动作。

### 3\.3\.2 基础控制流程

应用 SDK 进行程序控制通常包括以下步骤：

```Plaintext
导入 SDK
  ↓
初始化通信
  ↓
创建控制客户端
  ↓
切换到准备模式
  ↓
切换到行走模式
  ↓
发送运动指令
  ↓
等待一定时间
  ↓
发送停止指令
```

这里每一步都有意义：

- 导入 SDK 是让 Python 程序获得机器人的 SDK 接口。

- 初始化通信是让程序和机器人服务建立连接。

- 创建控制客户端是获得运动控制的程序入口。

- 切换准备模式和行走模式是为了让机器人进入可以安全执行运动的状态。

- 发送运动指令后必须等待一定时间，并且必须发送停止指令。

切记，程序最重要的最后一步：停止。机器人控制程序中，停止是必选项。任何运动测试都必须具备明确停止指令，尤其不能写“持续运动但没有退出条件”的程序。

### 3\.3\.3 模式切换与动作调用

模式切换的意义，是保障机器人在执行某些运动的动作指令之前，处于必须的控制状态。

例如：

- 执行站立准备前，需要进入准备模式；

- 执行行走控制前，需要进入行走模式；

- 机器人异常或需要安全放置时，需要回到阻尼或其他安全状态；

- 某些动作只允许在特定模式下执行。

动作调用也要遵守前置条件。挥手、握手、舞蹈、起身、踢球等动作不应在任意状态下随意调用。尤其是起身、舞蹈、踢球这类大幅度动作，必须确认环境、地面和机器人姿态。

本章只使用小幅度基础运动作为第一个程序案例。复杂动作调用会在后续动作和项目章节中逐步展开。

## 3\.4 运动参数与基础行走

SDK 控制机器人行走时，最常用的接口是：

```Python
client.Move(vx, vy, vyaw)
```

这条指令的三个参数不是关节角度，也不是“走几步”的离散命令，而是对机器人整体运动速度的描述。程序发送的是“希望机器人以什么速度运动”，底层运动控制系统再把速度意图转化为步态、平衡和各关节动作。

### 3\.4\.1 速度参数：vx、vy、vyaw

`Move(vx, vy, vyaw)` 中三个参数分别对应前后速度、左右速度和旋转角速度。

|参数|含义|单位|正负方向|
|---|---|---|---|
|`vx`|前后方向速度|m/s|正值向前，负值向后|
|`vy`|左右方向速度|m/s|正值向左，负值向右|
|`vyaw`|旋转角速度|rad/s|正值逆时针转，负值顺时针转|

`vx` 控制机器人沿身体前后方向移动。例如：

```Python
client.Move(0.2, 0.0, 0.0)
```

这表示让机器人以约 `0.2 m/s` 的速度向前移动。若保持这个速度约 `1.5 s`，理论前进距离可以估算为：

```Plaintext
前进距离 ≈ 速度 × 时间 = 0.2 × 1.5 = 0.3 m
```

这个距离只是估算值，不是精确位移。真实机器人会受到起步加速、地面摩擦、步态稳定、控制延迟等因素影响，所以不能把 `vx × time` 当作精确定位结果。它更适合用于理解“速度和时间共同决定运动幅度”。

`vy` 控制机器人横向移动。例如：

```Python
client.Move(0.0, 0.1, 0.0)
```

这表示让机器人以约 `0.1 m/s` 的速度向左侧移。若保持 `1.0 s`，理论横移距离约为：

```Plaintext
横移距离 ≈ 0.1 × 1.0 = 0.1 m
```

如果写成：

```Python
client.Move(0.0, -0.1, 0.0)
```

则表示向右侧移。横向移动对双足机器人更敏感，因为机器人需要在左右支撑切换中保持平衡。第一次基础控制不建议直接使用较大的 `vy`，应先从 `0.05` 到 `0.1` 这样的较小值开始，并保持短时间。

`vyaw` 控制机器人原地旋转。例如：

```Python
client.Move(0.0, 0.0, 0.2)
```

这表示让机器人以约 `0.2 rad/s` 的角速度逆时针旋转。`rad/s` 是弧度每秒，弧度是描述角度的单位。`1 rad` 约等于 `57.3°`。若保持 `2.0 s`，理论旋转角度可以估算为：

```Plaintext
旋转角度 ≈ 0.2 × 2.0 = 0.4 rad ≈ 22.9°
```

如果写成：

```Python
client.Move(0.0, 0.0, -0.2)
```

则表示顺时针旋转。与平移一样，旋转角度也不是精确控制结果，只能作为初步估算。

### 3\.4\.2 速度指令与持续时间

`Move` 指令本身只描述速度，不直接包含“持续几秒”。机器人会在收到速度指令后按该速度意图运动，直到收到新的速度指令、停止指令，或底层控制系统进入其他状态。

因此，一个完整的小幅运动通常由三步组成：

```Plaintext
发送速度指令
  ↓
等待一段时间
  ↓
发送停止指令
```

对应到代码就是：

```Python
client.Move(0.2, 0.0, 0.0)
time.sleep(1.5)
client.Move(0.0, 0.0, 0.0)
```

这里的 `time.sleep(1.5)` 不是 SDK 的运动参数，而是让 Python 程序暂停 `1.5 s`。在这段暂停时间里，机器人继续执行上一条速度指令。暂停结束后，程序继续向下执行，发送 `Move(0.0, 0.0, 0.0)`，机器人停止移动。

如果没有 `sleep`，程序会几乎立刻执行停止指令：

```Python
client.Move(0.2, 0.0, 0.0)
client.Move(0.0, 0.0, 0.0)
```

这样机器人可能刚收到前进指令，就立即收到停止指令，几乎看不到运动效果。反过来，如果 `sleep` 时间过长，机器人会持续运动更久，风险也会增大。

### 3\.4\.3 如何选择速度和时间

选择速度和时间时，不要先追求“走得明显”，而要先追求“能安全观察、能及时停止、能复现”。基础测试可以按以下原则设置：

|场景|推荐速度|推荐持续时间|说明|
|---|---|---|---|
|第一次前进|`vx = 0.1` 到 `0.2`|`1.0` 到 `1.5 s`|只观察机器人是否能向前小幅移动|
|第一次后退|`vx = -0.1`|`1.0 s`|后退更容易忽略后方空间，时间要短|
|第一次左移|`vy = 0.05` 到 `0.1`|`1.0 s`|横移对平衡更敏感，速度要小|
|第一次右移|`vy = -0.05` 到 `-0.1`|`1.0 s`|确认右侧空间安全|
|第一次旋转|`vyaw = 0.1` 到 `0.2`|`1.0` 到 `2.0 s`|只观察转向趋势，不追求角度精确|

如果希望估算运动幅度，可以使用下面的近似关系：

```Plaintext
前后距离 ≈ vx × 持续时间
左右距离 ≈ vy × 持续时间
旋转角度(rad) ≈ vyaw × 持续时间
旋转角度(°) ≈ vyaw × 持续时间 × 57.3
```

例如：

```Plaintext
vx = 0.2, 持续 1.5 s
前进距离 ≈ 0.2 × 1.5 = 0.3 m

vy = 0.1, 持续 1.0 s
左移距离 ≈ 0.1 × 1.0 = 0.1 m

vyaw = 0.2, 持续 2.0 s
旋转角度 ≈ 0.2 × 2.0 × 57.3 = 22.9°
```

这些公式用于帮助理解代码参数，不用于精确定位。后续如果需要让机器人到达准确位置，需要引入里程计、定位、反馈控制或视觉闭环，而不是只依赖 `Move` 加 `sleep`。

### 3\.4\.4 基础动作组合

掌握三个速度参数后，可以把基础运动理解为不同参数组合。

```Plaintext
向前：vx > 0, vy = 0, vyaw = 0
向后：vx < 0, vy = 0, vyaw = 0
左移：vx = 0, vy > 0, vyaw = 0
右移：vx = 0, vy < 0, vyaw = 0
左转：vx = 0, vy = 0, vyaw > 0
右转：vx = 0, vy = 0, vyaw < 0
停止：vx = 0, vy = 0, vyaw = 0
```

也可以组合运动，例如边前进边转向：

```Python
client.Move(0.15, 0.0, 0.1)
```

但在第一轮基础控制中，不建议同时修改多个参数。更稳妥的顺序是：先测试 `vx`，再测试 `vy`，再测试 `vyaw`，最后再尝试小幅组合。每次测试结束都必须发送停止指令：

```Python
client.Move(0.0, 0.0, 0.0)
```

## 3\.5 实践案例：Hello Robot

本节通过一个最小程序完成 K1 的基础运动控制。这个案例的重点不是让机器人执行复杂动作，而是教会读者看懂并写出一段完整的 SDK 控制代码：如何连接机器人、如何初始化客户端、如何切换模式、如何发送速度指令、如何控制运动持续时间、如何确保停止。

### 3\.5\.1 案例目标

Hello Robot 程序完成一个小幅前进并停止的动作序列：

```Plaintext
连接机器人
  ↓
初始化控制客户端
  ↓
进入准备模式
  ↓
进入行走模式
  ↓
以小速度向前移动一小段时间
  ↓
发送停止指令
```

运行这个程序前，机器人应已经完成开机、站立和安全检查。程序运行时，操作者应站在安全位置观察机器人状态，并确保紧急情况下快速按下机器人背后的Stand按钮，让机器人回到准备模式。

### 3\.5\.2 程序结构

从本章开始，手册中需要亲手运行的代码统一放在项目根目录下的 `CourseCode/` 目录中。每一章对应一个独立子目录，例如本章代码放在：

```Plaintext
CourseCode/chapter_03_robot_control/
```

本案例对应的代码文件为：

```Plaintext
CourseCode/chapter_03_robot_control/hello_robot.py
```

下面先展示完整程序。

完整示例：

```Python
# hello_robot.py

import time
from booster_robotics_sdk_python import *


ROBOT_IP = "127.0.0.1"


def main():
    print("Hello, Booster K1!")

    print("初始化通信...")
    ChannelFactory.Instance().Init(0, ROBOT_IP)
    time.sleep(2)

    print("初始化控制客户端...")
    client = B1LocoClient()
    client.Init()
    time.sleep(2)

    try:
        print("切换到准备模式")
        result = client.ChangeMode(RobotMode.kPrepare)
        print("返回值：", result)
        time.sleep(2)

        print("切换到行走模式")
        result = client.ChangeMode(RobotMode.kWalking)
        print("返回值：", result)
        time.sleep(2)

        print("发送运动指令")
        result = client.Move(0.2, 0.0, 0.0)
        print("返回值：", result)
        time.sleep(1.5)

    finally:
        print("发送停止指令")
        result = client.Move(0.0, 0.0, 0.0)
        print("返回值：", result)
        time.sleep(1)

    print("Hello Robot 程序结束")


if __name__ == "__main__":
    main()
```

因为程序直接运行在 K1 本机环境中，`ROBOT_IP` 可以使用 `127.0.0.1`，不用修改。如果从外部上位机直接通过 SDK 控制机器人，需要结合当前网络和通信配置设置实际 IP。初学阶段建议优先在 K1 内部运行程序，减少网络配置变量。

### 3\.5\.3 关键代码说明

第一，导入时间模块和 SDK：

```Python
import time
from booster_robotics_sdk_python import *
```

`time` 模块用于调用 `time.sleep()`，也就是让程序暂停一段时间。SDK 相关类和函数来自 `booster_robotics_sdk_python`，后续的 `ChannelFactory`、`B1LocoClient`、`RobotMode` 都由它提供。

第二，设置机器人 IP：

```Python
ROBOT_IP = "127.0.0.1"
```

`127.0.0.1` 表示本机地址。因为这段程序运行在 K1 机器人内部，可以用这个地址连接本机机器人服务。如果程序运行在外部开发电脑上，需要把它改成机器人 IP，例如：

```Python
ROBOT_IP = "192.168.10.102"
```

第三，初始化通信：

```Python
ChannelFactory.Instance().Init(0, ROBOT_IP)
time.sleep(2)
```

这一步用于建立程序与机器人服务之间的通信。没有通信初始化，后续控制客户端无法正常向机器人发送请求。紧跟着的 `time.sleep(2)` 是给通信通道和机器人服务留出启动时间。这里的 `2` 不是运动时间，而是工程上的稳定等待。若设备响应较慢，可以适当改成 `3`；若系统状态已经稳定，也可以缩短，但初次上机不建议过早压缩等待时间。

第四，创建并初始化控制客户端：

```Python
client = B1LocoClient()
client.Init()
time.sleep(2)
```

`B1LocoClient` 可以理解为运动控制客户端。后续模式切换、基础运动等指令都通过这个客户端发出。客户端初始化后的 `time.sleep(2)` 用于让控制客户端完成准备。如果客户端还没有准备好就继续发指令，程序可能返回异常或机器人没有反应。

第五，切换模式：

```Python
client.ChangeMode(RobotMode.kPrepare)
time.sleep(2)

client.ChangeMode(RobotMode.kWalking)
time.sleep(2)
```

程序先进入准备模式，再进入行走模式。这个顺序与本体操作中的安全链路一致，不能从阻尼状态直接进入行走控制。准备模式和行走模式不是瞬时概念，机器人从一个模式进入另一个模式时，需要调整关节状态、姿态控制和运动控制程序。这里等待 `2 s`，是为了让机器人身体状态稳定下来，再执行下一步。若现场观察到机器人姿态变化较慢，可以把等待时间改成 `3 s`。

第六，发送运动指令并保持一段时间：

```Python
client.Move(0.2, 0.0, 0.0)
time.sleep(1.5)
```

`Move(0.2, 0.0, 0.0)` 表示机器人以较小速度向前移动，不横移、不旋转。`time.sleep(1.5)` 才真正决定机器人以当前速度运动多久。选择 `1.5 s`，是因为第一次测试只需要让机器人向前移动一小段，既能看到效果，又不会让机器人走得太远。按前面的估算关系，`0.2 m/s` 持续 `1.5 s`，理论前进距离约为 `0.3 m`。

如果想测试左移，可以把这一段改成：

```Python
client.Move(0.0, 0.1, 0.0)
time.sleep(1)
```

如果想测试原地左转，可以改成：

```Python
client.Move(0.0, 0.0, 0.2)
time.sleep(2)
```

每次只改一个速度参数，更容易判断机器人运动现象和代码参数之间的关系。

第七，发送停止指令：

```Python
client.Move(0.0, 0.0, 0.0)
time.sleep(1)
```

停止指令的本质是把三个速度都设为 `0`。发送停止指令后等待 `1 s`，是为了给停止指令留出生效和观察时间。程序不要刚发出停止指令就马上退出，应该留出短暂时间确认机器人已经真正停住。

到这里，读者就能理解程序中为什么会有多个 `sleep`：有些等待是为了通信和客户端初始化，有些等待是为了模式切换稳定，有些等待才是真正控制运动持续时间，还有一个等待用于观察停止是否生效。它们都叫 `sleep`，但语义并不相同。

第八，使用 `try...finally` 保证停止：

```Python
try:
    ...
finally:
    client.Move(0.0, 0.0, 0.0)
```

`finally` 中的代码会在 `try` 代码块结束时执行；即使中途出现异常，也会尽量执行停止逻辑。机器人控制程序必须有停止兜底，不能只考虑正常流程。

### 3\.5\.4 运行方式

本项目中的正式代码文件位于：

```Plaintext
CourseCode/chapter_03_robot_control/hello_robot.py
```

在 K1 上运行时，建议通过vs code ssh remote连接机器人后，打开机器人本体的Workspace目录，然后将代码文件复制到该目录下，例如：

```Bash
/home/booster/Workspace/chapter_03_robot_control/hello_robot.py
```

打开终端，进入代码所在目录后运行：

```Bash
cd /home/booster/Workspace/chapter_03_robot_control
python3 hello_robot.py
```

运行前必须确认：

- 机器人已经开机并完成初始化；

- 机器人已经按照安全顺序进入准备模式或可切换到准备模式；

- 机器人周围有足够空间；

- 机器人处于平整地面；

运行时重点观察：

- 终端是否打印初始化信息；

- 模式切换是否有返回值；

- 机器人是否进入准备模式和行走模式；

- 机器人是否向前小幅移动；

- 程序是否发送停止指令；

- 程序结束后机器人是否停止。

### 3\.5\.5 常见问题排查

问题 1：程序无法导入 SDK。

可以按顺序检查：

- 是否在 K1 系统中运行程序；

- 当前 Python 环境是否正确；

- 是否安装了 `booster_robotics_sdk_python`；

可以先运行：

```Bash
python3 -m pip show booster_robotics_sdk_python
```

如果没有任何输出，说明当前 Python 环境中没有安装该 SDK。

问题 2：程序卡在初始化或通信失败。

可以按顺序检查：

- `ROBOT_IP` 是否正确；

- 程序是在 K1 本机运行，还是在外部开发电脑运行；

- 外部开发电脑是否能 `ping` 通 K1；

- 是否重复执行了 `ChannelFactory.Instance().Init()`；

- 机器人服务是否正常运行。

问题 3：模式切换没有明显效果。

可以按顺序检查：

- 机器人是否已经完成开机初始化；

- 机器人是否处于安全放置状态；

- 准备模式是否已经让机器人站稳；

- 模式切换后的 `time.sleep(2)` 是否太短；

- 终端返回值是否提示异常；

如果机器人姿态变化较慢，可以把模式切换后的 `time.sleep(2)` 改为 `time.sleep(3)`，先保证状态稳定，再继续执行运动指令。

问题 4：程序运行了，但机器人没有移动。

可以按顺序检查：

- 机器人是否已经进入行走模式；

- `Move` 中的三个速度参数是否全是 `0`；

- 速度是否设置得过小；

- 运动指令后的 `time.sleep()` 是否太短；

- 是否刚发送运动指令就发送了停止指令；

- 机器人是否处于保护状态或控制服务异常。

第一次测试可以使用：

```Python
client.Move(0.2, 0.0, 0.0)
time.sleep(1.5)
```

确认前进有效后，再分别测试横移和旋转。

问题 5：机器人移动距离过大。

可以按顺序处理：

- 先按 `STAND` 让机器人回到准备模式；

- 下次运行时减小运动指令后的 `time.sleep()`；

- 再减小 `Move` 中的 `vx`、`vy` 或 `vyaw`；

- 不要同时增大速度和时间；

- 确认 `finally` 中有停止指令。

问题 6：机器人运动后没有停止。

这是严重问题，应立即让机器人进入安全状态。后续排查时重点检查：

- 是否发送了 `client.Move(0.0, 0.0, 0.0)`；

- 停止指令是否放在 `finally` 中；

- 程序是否存在无限循环；

- 运动指令后的 `time.sleep()` 是否被设置得过长；

- 是否存在网络中断导致停止指令没有送达。

## 3\.6 补充：SDK 版本查看与管理

K1 开发中要区分两类版本：机器人系统版本和 Python SDK 版本。系统版本决定机器人底层服务、运动控制程序和固件能力；Python SDK 版本决定当前 Python 程序能调用哪些接口。两者存在匹配关系，不能只升级其中一个而不考虑兼容性。

### 3\.6\.1 查看机器人系统版本

通过 SSH 登录 K1 后，运行：

```Bash
cat /opt/booster/version.txt
```

这条命令查看的是机器人系统版本，不是 Python SDK 包版本。它可以用于判断当前机器人固件和系统软件处于哪个版本。

### 3\.6\.2 查看 Python SDK 版本

查看当前 Python 环境中安装的 SDK 版本：

```Bash
python3 -m pip show booster_robotics_sdk_python
```

输出中重点看 `Version` 字段。例如：

```Plaintext
Name: booster_robotics_sdk_python
Version: 1.3.6
```

也可以直接用 Python 读取安装包版本：

```Bash
python3 -c "import importlib.metadata as m; print(m.version('booster_robotics_sdk_python'))"
```

如果想确认当前导入的是哪个位置的 SDK，可以运行：

```Bash
python3 -c "import booster_robotics_sdk_python as br; print(br.__file__)"
```

这个命令有助于判断程序到底使用的是系统中哪个 Python 环境下的 SDK。

### 3\.6\.3 升级 Python SDK

升级到当前可获取的最新已发布版本：

```Bash
python3 -m pip install --user --upgrade booster_robotics_sdk_python
```

升级完成后，再查看版本：

```Bash
python3 -m pip show booster_robotics_sdk_python
```

如果下载速度较慢，可以临时使用镜像源：

```Bash
python3 -m pip install --user --upgrade booster_robotics_sdk_python -i https://pypi.tuna.tsinghua.edu.cn/simple
```

升级 SDK 前应先确认当前机器人系统版本和课程代码所需版本。SDK 升级不是越新越好，如果接口或底层通信行为发生变化，旧代码可能需要调整。

### 3\.6\.4 重置 SDK 到指定版本

如果需要把 SDK 固定到某一个版本，例如 `1.3.6`，可以使用：

```Bash
python3 -m pip install --user --force-reinstall booster_robotics_sdk_python==1.3.6
```

如果怀疑缓存导致安装结果不正确，可以加上 `--no-cache-dir`：

```Bash
python3 -m pip install --user --force-reinstall --no-cache-dir booster_robotics_sdk_python==1.3.6
```

安装完成后再次检查：

```Bash
python3 -m pip show booster_robotics_sdk_python
```

如果需要先卸载再安装：

```Bash
python3 -m pip uninstall booster_robotics_sdk_python
python3 -m pip install --user booster_robotics_sdk_python==1.3.6
```

### 3\.6\.5 系统升级与 SDK 升级的区别

下面这条命令用于升级机器人系统软件：

```Bash
booster-cli upgrade
```

它和 Python SDK 升级不是一回事。`booster-cli upgrade` 影响机器人系统软件，`pip install booster_robotics_sdk_python` 影响 Python 开发包。排查问题时应分别确认：

```Bash
cat /opt/booster/version.txt
python3 -m pip show booster_robotics_sdk_python
```

如果系统版本和 SDK 版本不匹配，可能出现导入成功但接口调用异常、某些模式或动作不可用、控制服务响应不一致等问题。遇到这类问题时，先固定课程要求的 SDK 版本，再确认机器人系统版本。

## 3\.7 本章小结

本章完成了从 K1 本体操作到 SDK 程序控制的过渡。

首先，本章介绍了开机、安全红线和运行模式。K1 的阻尼模式、准备模式、行走模式和保护模式，分别对应不同的关节发力状态、姿态保持能力和安全边界。任何控制程序都必须建立在正确模式和安全环境之上。

其次，本章介绍了手柄、App、SSH、VSCode Remote 和 Booster Studio 的作用。手柄和 App 用于基础操控和状态确认，SSH 用于进入 K1 系统，VSCode Remote 用于编辑代码，Booster Studio 用于观察机器人状态和调试信息。

再次，本章引入了 SDK 控制接口和运动参数。`vx`、`vy`、`vyaw` 分别描述前后速度、左右速度和旋转角速度；`time.sleep()` 决定速度指令保持多久；停止指令必须显式发送。

最后，本章通过 Hello Robot 实践案例建立了第一个控制闭环。这个闭环包括连接机器人、切换模式、发送运动参数、等待执行、发送停止指令和排查常见问题。

进入下一章后，课程将从单个 SDK 控制程序扩展到 ROS2 通信与控制接口。读者将进一步理解多个机器人软件模块如何通过节点、话题和服务协同工作。

