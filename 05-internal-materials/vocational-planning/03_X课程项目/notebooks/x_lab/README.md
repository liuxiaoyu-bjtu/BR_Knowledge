# U7/U8配套文件

把`x_lab/`、各课Notebook和`u8_team_template.py`放在同一工作目录。不需要安装本文件夹，Notebook中的Python可以直接导入。

```text
notebooks/
├── U7-L2_足球定位与自动踢球.ipynb
├── U7-L3_多线程协作.ipynb
├── U7-L4_多模态流程衔接.ipynb
├── U8-L2_分主题开发模板.ipynb
├── U8-L3_联调模板.ipynb
├── u8_team_template.py
└── x_lab/
    ├── __init__.py
    ├── ball_position.py
    └── flows.py
```

| 文件 | 提供什么 | 在哪里学习和使用 |
| --- | --- | --- |
| ball_position.py | 按实测对应点建立球位置近似映射；检查分辨率、范围及独立误差 | U7-L2标定、核对；U7-L4和踢球项目复用 |
| flows.py | 检测、有限文本播报、致意、短时踢球及资源收尾的局部参考 | U7-L3/L4、U8-L2/L3 |
| ../u8_team_template.py | 本组程序起点，包含参数、步骤和普通函数 | U8-L2首次复制为u8_team.py，后续保留本组修改 |

这些文件是课程附件，函数名称不属于BoosterOS SDK。可打开查看其中的真实SDK调用。图像推理和机器人调用还需课程中已经使用的`boosteros`及视觉依赖；标定计算使用NumPy。导入附件不会连接机器人，也不会发运动指令。

`ball_calibration.json`由本机实际标定与独立核对生成，不能借用其他机器或姿态的数据。球框下缘中点与地面位置之间是近似关系；头部、站姿、分辨率、球型和地面变化会影响结果。附件没有补偿动态姿态，静态验证不能替代足球步态下的验证。

`u8_team.py`、标定文件、JSON日志和视频是本组产物，按Notebook要求保存。重新复制模板会丢掉本组修改，因此代码先检查文件是否已存在。
