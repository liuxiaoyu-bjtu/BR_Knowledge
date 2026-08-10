---
title: Booster Agent Framework
module: 07-tech-platform
status: completed
created: 2026-08-10
updated: 2026-08-10
source: Booster Agent Framework 官方文档（了解/开发第一个 Agent/Python API）
version: V1.0
---

# Booster Agent Framework

> **定位**: Booster Agent Framework 是运行在 **App 端**的高层 Python 开发框架，负责 UI 组件、生命周期管理、机器人状态订阅和回调响应。它不直接操作机器人硬件，而是通过 `call_booster_interface_api()` 与底层 BoosterOS SDK 通信。
>
> **与 BoosterOS SDK 的关系**:
> - **BoosterOS SDK（`boosteros`）**：机器人的操作系统/驱动层，运行在机器人本体或 PC 端，负责传感器读取、运动控制、AI 检测等底层能力
> - **Booster Agent Framework（`booster_agent_framework`）**：运行在 App 端的高层应用开发框架，负责 UI 组件、生命周期管理、机器人状态订阅、回调响应
>
> 两者是**底层能力层 vs 上层应用层**的关系。基于 SDK 的课程教的是底层能力，Agent 框架课程教的是应用开发，两课程有明确的因果顺序。

---

## 目录

- [一、架构概述](#一架构概述)
- [二、Agent 基类](#二agent-基类)
- [三、UI 组件系统](#三ui-组件系统)
- [四、参数系统](#四参数系统)
- [五、手柄与快捷键](#五手柄与快捷键)
- [六、机器人状态](#六机器人状态)
- [七、存储管理](#七存储管理)
- [八、本地化与日志](#八本地化与日志)
- [九、模块级函数](#九模块级函数)
- [十、工程结构与构建部署](#十工程结构与构建部署)
- [十一、线程模型与最佳实践](#十一线程模型与最佳实践)
- [十二、与 BoosterOS SDK 的关系](#十二与-boosteros-sdk-的关系)

---

## 一、架构概述

### 1.1 三端架构

Booster 智能体生态由三部分组成：

```
┌──────────────┐     通信网关     ┌────────────────────────────┐
│   移动端 App  │ ◄──────────► │       机器人端               │
│  (UI 呈现)    │   毫秒级      │  Booster Agent Manager       │
│  按钮/摇杆    │   高带宽      │  ├─ Agent 1 (Python)         │
│  状态展示     │   多模态      │  ├─ Agent 2 (Python)         │
│              │              │  └─ Agent N (Python)         │
│              │              │    ↕ ROS2 通信                │
│              │              │  BoosterOS SDK / 硬件          │
└──────────────┘              └────────────────────────────┘
```

- **移动端**：用户使用的手机 App，负责呈现控制面板，捕获用户点击或摇杆操作
- **通信网关**：移动端与机器人端之间使用协议进行同屏毫秒级的高带宽多模态数据交互
- **机器人端**：Booster Agent Manager 接收移动端信令，通过 ROS2 通信机制调度和管理各激活状态的 Agent 进程

### 1.2 核心子系统

Framework 提供 7 个核心子系统：

| 子系统 | 访问方式 | 职责 |
|--------|---------|------|
| Agent 基类 | 继承 `AgentBase` | 运行配置、生命周期响应、组件管理器获取 |
| UI 组件系统 | `self.component_manager` | 组件声明、更新、页面切换、Toast 推送 |
| 参数系统 | `self.parameter_manager` | 参数读写、校验、变更回调 |
| 机器人状态 | `self.robot_states` | 机器人模式等运行状态访问 |
| 存储系统 | `self.storage_manager` | Agent 配置目录下的文件读写 |
| 手柄输入 | `self.component_manager.shortcut_manager` | 组合键描述、快捷键元数据查询 |
| 日志系统 | `self.logger` | 5 级日志输出 |

### 1.3 开发范式

```
step1. 导入接口: import booster_agent_framework
step2. 实现 Agent: 继承 AgentBase 类，复写/扩展方法
step3. 通过 self 指针获取顶层 API 对象
step4. 调用具体接口
```

### 1.4 最小 Agent 示例

```python
from booster_agent_framework import (
    AgentBase,
    AgentFeatures,
    DefaultStateIconComponent,
    LocaleString,
)

class MyAgent(AgentBase):
    def __init__(self) -> None:
        super().__init__(AgentFeatures())

        demo_component = DefaultStateIconComponent(
            "demo",
            LocaleString("Demo", "示例"),
            "res/demo.png",
            False,
            self.on_demo_click,
        )
        self.component_manager.add_component(demo_component)

    def on_demo_click(self, component):
        self.logger.info(f"clicked: {component.id}")
        return LocaleString("Clicked", "已点击")

    def on_agent_activated(self) -> None:
        self.logger.info("agent activated")

    def on_agent_close(self) -> None:
        self.logger.info("agent closing")
```

一个完整的 Agent 通常包含三部分：**Agent 生命周期管理 + UI 组件定义 + 事件回调处理**。

---

## 二、Agent 基类

### 2.1 AgentBase

`AgentBase` 是所有 Python Agent 的基类，处理与 BoosterAgent 管理器的通信、操纵杆事件和组件生命周期。

**构造函数**: `AgentBase(agent_features: AgentFeatures)`

**方法**

| 方法 | 返回 | 说明 |
|------|------|------|
| `on_agent_activated()` | `None` | Agent 激活时的生命周期回调，子类可重写 |
| `on_agent_close()` | `None` | Agent 关闭前的生命周期回调，子类可重写 |
| `register_robot_states_callback(callback)` | `None` | 注册机器人状态变化回调。签名: `Callable[[RobotStatesAggregation, RobotStatesAggregation], None]`，参数顺序 `(old_state, cur_state)` |
| `call_booster_interface_api(loco_api_id, body, timeout_ms)` | `tuple[int, str]` | 调用 Booster Interface API（高层运控接口） |

**`call_booster_interface_api` 参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `loco_api_id` | `int` | 取值参考 `booster_robotics_sdk_python.LocoApiId` |
| `body` | `str` | 与 `loco_api_id` 对应的 JSON 请求体 |
| `timeout_ms` | `int` | 超时时间（毫秒） |
| **返回** | `tuple[int, str]` | `(status_code, response_body)` |

```python
from booster_robotics_sdk_python import (
    LocoApiId,
    WaveHandParameter,
    HandIndex,
    HandAction,
)

status, body = self.call_booster_interface_api(
    LocoApiId.kWaveHand,
    WaveHandParameter(HandIndex.kRightHand, HandAction.kHandOpen).to_json_str(),
    1000,
)
```

**属性**

| 属性 | 类型 | 说明 |
|------|------|------|
| `agent_id` | `str` | 当前 Agent ID |
| `agent_state` | `AgentState` | 当前 Agent 生命周期状态 |
| `component_manager` | `ComponentManager` | 组件管理器 |
| `logger` | `Logger` | 日志对象 |
| `parameter_manager` | `BoosterAgentParameterManager` | 参数管理器 |
| `robot_states` | `RobotStatesAggregation` | 机器人当前状态集合 |
| `storage_manager` | `StorageManager` | 存储管理器 |

### 2.2 AgentFeatures

配置 Agent 初始化时启用的内建能力。

```python
AgentFeatures(
    enable_orchestration: bool = True,
    enable_auto_getup: bool = False,
    auto_get_up_shortcut: JoystickEvent | None = None,
    param_schema_path: str = "",
    enable_telemetry_report: bool = False,
)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_orchestration` | `bool` | `True` | 是否启用内建自定义动作能力 |
| `enable_auto_getup` | `bool` | `False` | 是否启用自动起身 |
| `auto_get_up_shortcut` | `JoystickEvent \| None` | `None` | 自动起身快捷键 |
| `param_schema_path` | `str` | `""` | 参数 schema 文件路径，用于 App 中配置 Agent 参数 |
| `enable_telemetry_report` | `bool` | `False` | 是否启用遥测事件上报 |

```python
features = AgentFeatures(
    enable_orchestration=True,
    enable_auto_getup=True,
    auto_get_up_shortcut=JoystickEvent(
        JoystickEventType.kBUTTON_DOWN_OR_HAT,
        [JoystickKey.kLT, JoystickKey.kHAT_UP],
    ),
    param_schema_path="res/params/schema.json",
)
```

### 2.3 AgentState

Agent 生命周期状态枚举。

| 成员 | 说明 |
|------|------|
| `kUninitialized` | 尚未初始化 |
| `kInactive` | 已初始化但未激活 |
| `kActive` | 已激活并处于运行状态 |
| `kFinalized` | 已结束生命周期 |

---

## 三、UI 组件系统

### 3.1 组件继承体系

```
Component (基类)
├── IconComponent (带图标)
│   ├── StateIconComponent (整型状态)
│   │   └── DefaultStateIconComponent (布尔状态)
│   ├── PlaceholderComponent (占位)
│   └── OnlineWebviewComponent (在线网页)
```

### 3.2 Component（基类）

所有 UI 组件的基类，代表移动应用上的一个可点击 UI 元素。

```python
Component(
    id: str,
    name: LocaleString,
    click_callback: Callable[[Component], LocaleString | None] | None = None,
    shortcut_id: str = "",
    display_sequence: int = ComponentDisplaySequenceAuto,
)
```

| 参数 | 说明 |
|------|------|
| `id` | 组件唯一标识 |
| `name` | 组件显示名称 |
| `click_callback` | 点击回调；返回 `LocaleString` 时框架会将其作为 Toast 显示 |
| `shortcut_id` | 引用 `agent.toml` 中定义的快捷键 ID |
| `display_sequence` | 显示顺序，数值小的优先显示（从左到右），默认自动分配 |

> **注意**: `click_callback` 接收的是本次点击事件的 Component 副本，不是 ComponentManager 中的实时对象。如需刷新 UI，请用 `component.id` 获取真实组件后更新。

**ComponentType 枚举**: `kICON`（无状态）/ `kSTATE_ICON`（整数状态）/ `kDEFAULT_STATE_ICON`（布尔状态）

### 3.3 IconComponent

带图标路径的基础图标组件。

```python
IconComponent(id, name, icon_path, click_callback=None, shortcut_id="", display_sequence=Auto)
```

| 属性 | 类型 | 说明 |
|------|------|------|
| `activated` | `bool` | 是否已激活 |
| `need_activate` | `bool` | 是否需要激活 |
| `path` | `str` | 图标图片文件路径 |

### 3.4 StateIconComponent

整型状态组件，适合多状态图标（如 0/1/2 三态）。

```python
StateIconComponent(id, name, icon_path, state, click_callback=None, shortcut_id="", display_sequence=Auto)
```

| 属性 | 类型 | 说明 |
|------|------|------|
| `state` | `int` | 组件当前状态值 |

### 3.5 DefaultStateIconComponent

布尔状态组件（继承 StateIconComponent），适合开关类组件。状态在 App/Studio 中通过高亮展示。

```python
DefaultStateIconComponent(id, name, icon_path, state, click_callback=None, shortcut_id="", display_sequence=Auto)
```

```python
def on_wave_click(component: Component) -> LocaleString:
    wave = component
    wave.state = not wave.state
    self.component_manager.update_component(wave)

    if wave.state:
        return LocaleString("Waving", "正在挥手")
    return LocaleString("Wave Stopped", "已停止挥手")

self.wave_component = DefaultStateIconComponent(
    "wave", LocaleString("Wave", "挥手"), "res/wave.png", False, on_wave_click,
)
self.component_manager.add_component(self.wave_component)
```

### 3.6 OnlineWebviewComponent

在线网页组件，点击后在 App 内通过 WebView 打开指定网页，支持 Agent 与前端页面双向消息通信。

```python
OnlineWebviewComponent(
    id, name, icon_path, url,
    callback: Callable[[Any], Any] | None = None,
    orientation: ComponentOrientation = ComponentOrientation.kAUTO,
    shortcut_id="", display_sequence=Auto,
)
```

**通信机制**:
- Web 页面 → Agent: `window.BoosterNativeBridge.sendMessageToAgent(req)` → Agent 侧 `callback`
- Agent → Web 页面: `component_manager.push_component_message(component, message)`

**ComponentOrientation 枚举**: `kAUTO` / `kLANDSCAPE` / `kPORTAIT`

```python
def webview_callback(request: object) -> object:
    if request.get("command") == "ping":
        return {"message": "pong from agent"}
    return {"success": False, "error": "unknown command"}

self.online_webview_component = OnlineWebviewComponent(
    "web", LocaleString("Web test", "网页测试"), "res/web.png",
    "www.xxxx.com", webview_callback, ComponentOrientation.kAUTO,
)
```

```javascript
// Web 页面侧
const res = await window.BoosterNativeBridge.sendMessageToAgent({ command: "ping" });
```

### 3.7 ComponentManager

组件管理器，负责组件的增删改查、Toast 推送和组件消息推送。通过 `self.component_manager` 访问。

| 方法 | 返回 | 说明 |
|------|------|------|
| `add_component(component)` | `None` | 添加单个组件 |
| `add_components(components)` | `None` | 批量添加组件 |
| `get_component(component_id)` | `Component \| None` | 按 ID 查询组件 |
| `get_components()` | `dict[str, Component]` | 获取 general section 下的组件映射 |
| `update_component(component)` | `None` | 更新已注册组件（同步状态到 App） |
| `remove_component(component)` | `None` | 移除组件 |
| `push_component_message(component, message)` | `None` | 向指定组件推送消息（用于 WebView 双向通信） |
| `publish_toast(message, position, icon)` | `None` | 向 App 推送 Toast |

**ToastIcon 枚举**: `kNONE` / `kSUCCESS` / `kWARNING` / `kERROR`

**ToastPosition 枚举**: `kCENTER` / `kBOTTOM` / `kTOP`

```python
self.component_manager.publish_toast(
    LocaleString({"en": "Saved", "zh": "已保存"}),
    ToastPosition.kCENTER,
    ToastIcon.kSUCCESS,
)
```

**属性**: `shortcut_manager: ShortcutManager` — 快捷键管理器

### 3.8 ComponentStatePageProxy

根据机器人状态自动切换页面，并管理页面内组件的显示与状态刷新。适用于：行走模式显示运动控制界面、足球模式显示比赛控制界面等场景。

```python
ComponentStatePageProxy(agent: AgentBase)
```

| 方法 | 说明 |
|------|------|
| `register_page(page_id, predicate)` | 注册页面。`predicate: Callable[[str, RobotStatesAggregation], bool]`，返回 `True` 时该页面激活 |
| `register_component(page_id, component, predicate)` | 向页面注册组件并提供状态谓词。`predicate: Callable[[Component, RobotStatesAggregation], int]`，返回值作为组件默认状态 |
| `register_component(page_id, component)` | 向页面注册组件（默认状态谓词，始终返回 0） |
| `register_component(page_id, components)` | 批量注册组件 |
| `get_component(page_id, component_id)` | 按页面和组件 ID 查询 |
| `unregister_component(page_id, component_id)` | 从页面注销组件 |
| `force_update()` | 基于当前最新机器人状态重新计算激活页面和组件状态 |

**属性**: `active_page: str`（当前激活页面 ID）/ `all_components: set[Component]`（全部组件集合）

```python
self.page_proxy = ComponentStatePageProxy(self)

self.page_proxy.register_page(
    "Walking",
    lambda page_id, state: state.robot_states_.current_mode == RobotMode.WALKING
)

self.wave_component = DefaultStateIconComponent(
    "wave", LocaleString("Wave", "挥手"), "res/wave.png", False, self.on_wave_click,
)
self.page_proxy.register_component("Walking", self.wave_component)
```

> **注意**: `ComponentStatePageProxy` 应作为 Agent 实例成员长期持有（如 `self.page_proxy`），不应在局部函数中临时创建。页面谓词应设计为互斥。

---

## 四、参数系统

参数系统依赖 `AgentFeatures.param_schema_path` 指定的 `schema.json` 文件，用于描述 App 参数配置页的字段、展示文本、默认值和校验规则。

### 4.1 schema.json 结构

```json
{
  "lang": { "zh": {}, "en": {} },
  "fields": []
}
```

- `lang`: 多语言文本表，字段中的 `*I18nKey` 会引用这里的 key
- `fields`: 参数字段数组，按顺序展示

**通用字段属性**

| 属性 | 必填 | 说明 |
|------|------|------|
| `fieldType` | 是 | `boolean` / `string` / `integer` / `float` / `select` / `divider` |
| `key` | 除 divider 外 | ROS2 参数名，也是代码读写参数时使用的名称 |
| `nameI18nKey` / `name` | 建议 | 展示名称 |
| `descriptionI18nKey` / `description` | 否 | 参数说明 |
| `defaultValue` | 否 | 默认值，类型必须与字段类型匹配 |

**schema → 参数类型映射**

| schema 写法 | 参数类型 |
|-------------|---------|
| `fieldType: "boolean"` | `BOOL` |
| `fieldType: "integer"` | `INT` |
| `fieldType: "float"` | `FLOAT` |
| `fieldType: "string"` | `STRING` |
| `select` + `valueType: "integer"` + `multiple: false` | `ENUM_INT` |
| `select` + `valueType: "string"` + `multiple: true` | `ENUM_MULTI_STRING` |
| ... | ... |

### 4.2 参数类型枚举

`BoosterAgentParameterType` 成员:

`BOOL` / `INT` / `INT_ARRAY` / `FLOAT` / `FLOAT_ARRAY` / `STRING` / `STRING_ARRAY` / `ENUM_INT` / `ENUM_FLOAT` / `ENUM_STRING` / `ENUM_MULTI_INT` / `ENUM_MULTI_FLOAT` / `ENUM_MULTI_STRING`

### 4.3 BoosterAgentParameter

表示单个参数值对象。

**构造方式**:
- 基于 schema 推断: `BoosterAgentParameter(name: str, value: Any)` — 需存在可用运行时且参数名已在 schema 中声明
- 显式指定类型: `BoosterAgentParameter(type: BoosterAgentParameterType, name: str, value: ...)`

**取值方法**: `as_bool()` / `as_int()` / `as_float()` / `as_string()` / `as_int_array()` / `as_float_array()` / `as_string_array()`

### 4.4 BoosterAgentParameterManager

通过 `self.parameter_manager` 访问。

**回调注册**

| 方法 | 回调签名 | 说明 |
|------|---------|------|
| `add_parameter_callback(name, callback)` | `Callable[[BoosterAgentParameter], None]` | 监听单个参数变化 |
| `add_parameter_event_callback(callback)` | `Callable[[BoosterAgentParameterEvent], None]` | 监听参数事件集合 |

**参数读取**

| 方法 | 返回 | 说明 |
|------|------|------|
| `get_parameter(name)` | `BoosterAgentParameter` | 按名称获取（不存在时抛 `ValueError`） |
| `get_parameters(keys=[])` | `list[BoosterAgentParameter]` | 批量获取，`keys=[]` 表示全部 |

**参数写入**

| 方法 | 返回 | 说明 |
|------|------|------|
| `set_parameter(param)` | `SetParametersResult` | 写入单个参数（支持参数对象或元组） |
| `set_parameters(params)` | `list[SetParametersResult]` | 批量写入 |

**元组写入形式**: `(BoosterAgentParameterType, name, value)` 或 `(name, value)`

```python
# 显式类型写入
result = self.parameter_manager.set_parameter(
    BoosterAgentParameter(BoosterAgentParameterType.INT, "maxCount", 10)
)

# 基于 schema 推断写入
result = self.parameter_manager.set_parameter(("maxCount", 10))

# 批量写入
results = self.parameter_manager.set_parameters([
    ("maxCount", 100),
    ("scale", 0.5),
    ("tags", ["tag1", "tag2"]),
])
for result in results:
    if not result.successful:
        self.logger.warn(result.reason)
```

**SetParametersResult**: `successful: bool` / `reason: str`

**BoosterAgentParameterEvent**: `new_params: list[BoosterAgentParameter]` / `updated_params: list[BoosterAgentParameter]` / `empty() -> bool`

---

## 五、手柄与快捷键

### 5.1 JoystickEvent

表示一个手柄事件。

```python
JoystickEvent()                                          # 空事件
JoystickEvent(event_type: JoystickEventType, key_set: int)
JoystickEvent(event_type: JoystickEventType, keys: list[str])
JoystickEvent(event_type: JoystickEventType, keys: list[JoystickKey])
JoystickEvent(event_type, keys, axis_lx, axis_ly, axis_rx, axis_ry)
```

| 方法 | 返回 | 说明 |
|------|------|------|
| `has_key(key)` | `bool` | 是否包含指定按键 |
| `is_none()` | `bool` | 是否为空事件 |
| `is_valid(key_num)` | `bool` | 校验快捷键组合是否有效 |
| `to_string()` | `str` | 转换为字符串 |
| `to_string_list()` | `list[str]` | 转换为按键字符串列表 |

**属性**: `axis_lx_` / `axis_ly_` / `axis_rx_` / `axis_ry_` / `event_type_` / `key_set_`

### 5.2 JoystickEventType

| 成员 | 说明 |
|------|------|
| `kNONE` | 无事件 |
| `kAXIS` | 摇杆/轴值变化 |
| `kHAT` | 方向键位置变化 |
| `kBUTTON_DOWN` | 按键按下 |
| `kBUTTON_UP` | 按键抬起 |
| `kREMOVE` | 输入设备移除 |
| `kBUTTON_DOWN_OR_HAT` | 按键按下或方向键 |

### 5.3 JoystickKey

`kNONE` / `kA` / `kB` / `kX` / `kY` / `kLB` / `kRB` / `kLT` / `kRT` / `kLS` / `kRS` / `kHAT_CENTER` / `kHAT_UP` / `kHAT_DOWN` / `kHAT_LEFT` / `kHAT_RIGHT` / `kHAT_LEFT_UP` / `kHAT_LEFT_DOWN` / `kHAT_RIGHT_UP` / `kHAT_RIGHT_DOWN` / `kBACK` / `kSTART`

### 5.4 ShortcutManager

通过 `self.component_manager.shortcut_manager` 访问。快捷键信息在 `agent.toml` 中定义。

```toml
[component_shortcuts]
version = "1.0"

[[component_shortcuts.shortcut_list]]
id = "wave"
shortcut = ["A"]
locale_name = { en = "Wave", zh = "挥手" }
```

| 方法 | 返回 | 说明 |
|------|------|------|
| `find_shortcut(shortcut)` | `ShortcutInfo \| None` | 按手柄事件查找 |
| `get_shortcut_by_id(id)` | `ShortcutInfo \| None` | 按 ID 查找 |
| `remove_shortcuts_by_id(ids)` | `int` | 批量移除，返回成功数 |

**属性**: `shortcut_list: list[ShortcutInfo]`

**ShortcutInfo**: `id: str` / `shortcut: JoystickEvent` / `locale_name: LocaleString`

---

## 六、机器人状态

### 6.1 RobotStatesAggregation

通过 `self.robot_states` 访问，也可在机器人状态回调中获取。

| 方法/属性 | 类型 | 说明 |
|-----------|------|------|
| `to_string()` | `str` | 状态集合字符串表示 |
| `robot_states_` | `RobotStatesMsg` | 机器人运行主状态消息 |

### 6.2 RobotStatesMsg

| 属性 | 类型 | 说明 |
|------|------|------|
| `current_mode` | `int` | 0=damping, 1=prepare, 2=walking, 3=custom, 4=soccer |
| `current_body_control` | `int` | 机体控制状态，参考 `booster_robotics_sdk_python.BodyControl` |
| `current_actions` | `list[int]` | 当前执行中的动作 ID 列表 |

### 6.3 FallDownState

通过 `self.robot_states.fall_down_state_` 访问。

| 属性 | 类型 | 说明 |
|------|------|------|
| `fall_down_state` | `FallDownStateType` | 当前跌倒状态 |
| `is_recovery_available` | `bool` | 是否允许执行恢复动作 |

**FallDownStateType**: `UNKNOWN` / `IS_READY` / `IS_FALLING` / `HAS_FALLEN` / `IS_GETTING_UP`

---

## 七、存储管理

### 7.1 StorageManager

通过 `self.storage_manager` 访问，用于读写 Agent 独立存储目录下的文件。

> **约束**: 所有路径必须使用相对路径，绝对路径和越界路径会被拒绝。

| 方法 | 返回 | 说明 |
|------|------|------|
| `copy_file(src, dst)` | `bool` | 复制文件 |
| `file_exists(relative_path)` | `bool` | 判断文件是否存在 |
| `read_text_file(relative_path)` | `str` | 读取文本文件 |
| `write_text_file(relative_path, content)` | `None` | 写入文本文件 |
| `read_binary_file(relative_path)` | `bytes` | 读取二进制文件 |
| `write_binary_file(relative_path, data)` | `None` | 写入二进制文件 |
| `remove_file(relative_path)` | `bool` | 删除文件 |
| `remove_folder(relative_path)` | `None` | 递归删除目录 |

**静态方法**:
- `generate_storage_path_string(relative_path, is_public=False) -> str` — 将相对路径编码为存储路径字符串
- `parse_storage_path_string(path) -> os.PathLike` — 解析回相对路径

**属性**: `node_config_path: os.PathLike` — Agent 配置目录根路径

```python
from pathlib import Path

result_path = Path("cache/result.txt")
self.storage_manager.write_text_file(result_path, "ok")
text = self.storage_manager.read_text_file(result_path)

data_path = Path("cache/data.bin")
self.storage_manager.write_binary_file(data_path, b"\x01\x02\x03\xff")
data = self.storage_manager.read_binary_file(data_path)
```

---

## 八、本地化与日志

### 8.1 LocaleString

多语言字符串类型。

```python
LocaleString()                          # 空
LocaleString(default_string: str)       # 单语言
LocaleString(en: str, zh: str)          # 双语言
LocaleString({"en": "Start", "zh": "开始"})  # 字典
```

| 方法 | 说明 |
|------|------|
| `add_translation(lang, text)` | 添加/更新单个语言版本 |
| `get_string(lang)` | 获取指定语言文本（回退到默认） |
| `size()` | 返回翻译条目数量 |

### 8.2 Logger

通过 `self.logger` 访问，5 个日志等级。

| 方法 | 用途 |
|------|------|
| `debug(msg)` | 开发排障详细诊断信息 |
| `info(msg)` | 系统正常运行关键事件 |
| `warn(msg)` | 异常但系统可继续运行（降级/回退） |
| `error(msg)` | 操作失败，需要排查 |
| `fatal(msg)` | 严重故障，需立即处理 |

---

## 九、模块级函数

| 函数 | 返回 | 说明 |
|------|------|------|
| `get_agent_config()` | `AgentConfig` | 读取 Agent 配置 |
| `get_sys_api_level()` | `int` | 获取当前系统 API Level |

**API Level 规则**: `主版本 × 10000 + 次版本 × 100 + 修订版本`（如 `10601` 对应固件 `1.6.1`）

---

## 十、工程结构与构建部署

### 10.1 标准工程结构

```
example_agent/
├── agent.toml          # Agent 运行配置（ID、名称、版本、入口类、快捷键）
├── build.toml          # 构建配置（构建参数、打包选项、pip 镜像源）
├── src/
│   └── main.py         # 主入口文件（组件定义、生命周期、回调）
├── res/                # 静态资源（图片、图标、配置文件）
└── build/
    └── xxx.agent       # 构建产物（可部署的 Agent 安装包）
```

| 文件/目录 | 职责 |
|-----------|------|
| `agent.toml` | Agent ID、名称、版本号、入口类、快捷键等基础信息 |
| `build.toml` | 构建参数、打包选项、pip 镜像源配置 |
| `src/` | 核心业务代码，最常修改的目录 |
| `src/main.py` | 组件定义、生命周期函数、事件回调 |
| `res/` | 图片、图标、配置文件等静态资源 |
| `build/` | 构建输出目录 |
| `xxx.agent` | 最终 Agent 安装包，可部署分发 |

### 10.2 构建流程

在 Booster Studio 中点击锤子图标（只构建 Agent）或一键运行部署按钮：

1. **元数据校验**: 校验 `agent.toml` 中的版本、反向域名 ID 等格式
2. **依赖解析**: 解析 `build.toml` 平台参数，从指定 pip 镜像源下载三方依赖
3. **代码混淆**（可选）: `obfuscation = true` 时对 `src/` 下 Python 源码进行词法混淆
4. **签名**: 专用签名工具读取证书对整包进行国密/安全数字签名
5. **输出**: 生成 `.agent` 文件到 `build/` 目录

### 10.3 开发流程

```
修改代码 → 构建 Agent → 部署到仿真/真机 → 运行验证 → 迭代优化
```

Booster Studio 将环境管理、代码开发、仿真验证和真机部署统一到同一平台，开发者可快速完成"修改—部署—验证"循环。

---

## 十一、线程模型与最佳实践

### 11.1 线程模型

Framework 的回调模型类似 Android 的事件回调模型：**所有用户回调都在主线程串行执行**，而非每个回调运行在独立线程中。框架会等待需要返回结果的回调完成。

**关键约束**:
- 回调应尽快返回，不要在回调中做长时间 IO、sleep、join、future wait
- 不要在回调中等待另一个 Python 回调、App 操作、参数事件或 robot state 事件
- `asyncio.run()` 仍会占住当前回调直到 coroutine 完成

### 11.2 耗时操作建议方案

- 耗时任务投递到开发者自己的后台线程/进程/外部服务
- 回调只做参数校验、状态记录、任务启动并快速返回
- 任务完成后再通过状态发布、组件更新、Toast 或事件通知结果
- 如必须同步等待，设置明确的短超时

### 11.3 开发最佳实践

| 原则 | 说明 |
|------|------|
| 先验证再扩展 | 每次只增加一个小功能，立即部署到仿真验证 |
| 模块职责清晰 | 运动控制、感知处理、任务决策分别组织在不同模块 |
| 优先利用框架能力 | 复用 Framework 提供的机器人控制接口、事件回调和生命周期管理 |
| 回调快速返回 | 避免阻塞主线程，耗时任务交由后台线程处理 |
| 互斥页面谓词 | ComponentStatePageProxy 的页面谓词应设计为互斥 |

### 11.4 典型业务模式

| 模式 | 适用场景 |
|------|---------|
| 按钮触发动作 | 挥手、起立、坐下等简单功能 |
| 按钮更新状态并刷新 UI | 开关控制、模式切换 |
| 按钮触发后台任务 | 视觉识别、长时间动作序列 |
| 状态驱动页面 | 机器人状态变化时显示不同组件 |

---

## 十二、与 BoosterOS SDK 的关系

### 12.1 层级关系

```
┌─────────────────────────────────────────┐
│        Booster Agent Framework          │  ← 应用层
│  UI 组件 / 生命周期 / 参数 / 状态订阅     │
│  通过 call_booster_interface_api() 通信  │
├─────────────────────────────────────────┤
│          BoosterOS SDK                  │  ← 驱动层
│  传感器 / 运动控制 / AI 检测 / 语音      │
│  直接操作机器人硬件                      │
├─────────────────────────────────────────┤
│          机器人硬件 (K1/T1)              │
└─────────────────────────────────────────┘
```

### 12.2 对比

| 维度 | BoosterOS SDK (`boosteros`) | Booster Agent Framework (`booster_agent_framework`) |
|------|------------------------------|-----------------------------------------------------|
| **定位** | 机器人操作系统/驱动层 | App 端高层应用开发框架 |
| **运行位置** | 机器人本体或 PC 端 | App 端（通过 Booster Studio 部署） |
| **核心职责** | 传感器读取、运动控制、AI 检测 | UI 组件、生命周期、参数管理、状态订阅 |
| **安装包** | `pip install boosteros` | 内置于 Booster Studio / Agent 运行时 |
| **机器人通信** | 直接调用 `BoosterRobot` 接口 | 通过 `call_booster_interface_api()` 间接调用 |
| **UI 能力** | 无 | 组件系统、Toast、WebView、状态页面代理 |
| **生命周期** | 无（脚本式） | `on_agent_activated()` / `on_agent_close()` |
| **课程定位** | 底层能力教学 | 应用开发教学 |
| **前置关系** | 先学（底层基础） | 后学（上层应用） |

### 12.3 交叉调用

Agent Framework 通过 `call_booster_interface_api()` 调用底层 SDK 能力，`loco_api_id` 取值来自 `booster_robotics_sdk_python.LocoApiId`：

```python
# Agent Framework 中调用 SDK 的挥手接口
from booster_robotics_sdk_python import LocoApiId, WaveHandParameter, HandIndex, HandAction

status, body = self.call_booster_interface_api(
    LocoApiId.kWaveHand,
    WaveHandParameter(HandIndex.kRightHand, HandAction.kHandOpen).to_json_str(),
    1000,
)
```

> **注意**: 此处引用的是旧版 `booster_robotics_sdk_python` 包的 `LocoApiId`，而非新版 `boosteros` 包。Agent Framework 的机器人状态枚举（如 `RobotMode.WALKING`）也直接引用旧 SDK 命名空间。

---

## 版本更新说明

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-08-10 | V1.0 录入 | 基于官方三份文档（了解/开发第一个 Agent/Python API）完整录入，覆盖 8 大子系统 + 工程结构 + 构建部署 + 最佳实践 |

> **原始文档**:
> - `了解Booster Agent Framework.md`（架构/生命周期/工程结构/部署/进阶/最佳实践）
> - `开发第一个 Booster Agent.md`（Booster Studio 开发流程/创建/构建/部署/验证）
> - `Booster Agent Framework Python API.md`（完整 Python API 参考）
>
> **后续更新**: 当收到新版本文档时，将更新本文档并记录版本变更历史。
