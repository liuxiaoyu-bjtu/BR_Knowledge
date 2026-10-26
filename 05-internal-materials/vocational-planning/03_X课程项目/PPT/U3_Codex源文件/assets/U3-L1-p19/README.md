# U3-L1第19页实物插图

2026-10-26完成，供用户审阅。对应“取点前确认目标对应——未确认配准时使用深度图中心”。本轮不代表整课确认⑥通过。

## 交付文件

- `U3-L1-p19-illustration.png`：3200×1260高清插图，可单独插入课件。
- `../../../U3-L1_机器人的眼睛_第19页实物插图审阅版.pptx`：29页课件的独立审阅版本，第19页使用本插图；标签、连线、中心十字与灰度图例可编辑。
- `qa-render/U3-L1_机器人的眼睛_第19页实物插图审阅版/slide-19.png`：PowerPoint实际导出的1920×1080页图。
- `scene-final.png`、`depth-clean.png`、`tape-detail.png`：实验场景、纯灰度深度图、刻度放大图。
- `assemble.py`、`build_components.py`、`source/`：装配脚本、几何与刻度脚本、选用的生成底图、基准课件和生成记录。

## 素材来源

| 素材 | 来源与处理 |
| --- | --- |
| K1外观 | 知识库既有产品图：`05-internal-materials/vocational-planning/04_人形机器人基础课程/教学课件/CODEX/L4_人形机器人的关键部件_源文件/assets/k1-side.png`及`CODEX/L1_图像源文件/k1-摄像头.png`，作为模型参考。公开分发授权范围仍待核。 |
| 实验场景 | 用户授权使用SenseNova API；模型`sensenova-u1.5-lite`，参考图编辑接口`https://token.sensenova.cn/v1/images/edits`。经过三轮生成，选用第三版；支架为通用机身支撑示意，不代表K1官方配件。 |
| 卷尺刻度 | 程序绘制1 mm刻度、1 cm分格，再按透视合成到黄色尺带；放大图展示0至20 cm附近的刻度。图上刻度用于说明器材，现场距离由学生填写。 |
| 深度图 | 程序按理想针孔相机的轴向深度Z计算，越近越白、越远越黑；灰度不受物体颜色、光照或阴影影响。 |

实际提交的三轮提示词保存在`source/scene-prompt.txt`、`source/scene-prompt-v2.txt`及`source/scene-prompt-v3.txt`。第三轮以第二轮图像为编辑对象，另输入两张K1原图；迭代关系见`source/scene-generation-metadata.json`。保留选用的第三版底图，未收录被弃用的前两版图像。API凭据不写入交付文件。

## 深度图的含义

纸箱正面与相机成像面平行，整面Z相同，所有有效像素灰度均为180；后方瓶身灰度为114至126，圆弧表面随Z变化；地面向远处逐渐变暗。中心点落在纸箱正面。相机视角中纸箱顶面不可见，侧面摆位图能看见顶面，两个观察角度不同。

几何参数用于构造教学示意，不是K1实测规格或实验读数。左右图表达同一摆位关系，不是标定后逐像素配准的一对图。实测彩色/深度截图、距离记录及改码后的真机补验仍需另补。

## 检查记录

- PPTX结构校验：`All validations PASSED!`，结果见`validation.txt`。校验脚本在Windows上需开启UTF-8，首次按GBK读取时失败，切换UTF-8后通过。
- PowerPoint文字边界检查：0项，见`text-bounds.json`。
- PowerPoint实际导出第19页，核对纸箱落地、头部自由、机身支撑、尺带终点、刻度数字、标签和中心取点，修正了放大图右缘数字截断。
- 包内对比：仅修改原有`slide19.xml`及其关系文件，另新增3个PNG媒体；其余原有包内容逐字节一致，见`qa.json`。
- 灰度断言：纸箱正面灰度一致、中心属于正面、瓶身比纸箱更暗，均通过。

## 再生成

Windows安装Python、Pillow、NumPy、defusedxml，并保留微软雅黑字体。在本目录运行`python -X utf8 assemble.py`，使用选定底图与已保存的深度/刻度素材重建插图和审阅版课件，无需访问图像API。`source/base-deck.pptx`为本次只读输入快照，SHA256见`source/sha256.json`。

需要调整几何或刻度时，先运行`python -X utf8 build_components.py`，再运行装配脚本。脚本向上寻找知识库`INDEX.md`定位仓库；再次装配会覆盖本目录的派生图片及同名审阅版。修改后重新校验，并用`PPT/U2_Codex源文件/render.ps1`导出第19页目检。
