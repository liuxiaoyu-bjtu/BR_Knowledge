"""
源码探源：定位 boosteros 包，并展示 `distance_m` 在源码里是怎么算出来的。

为什么需要它：
  SDK 文档只说 DetectionResult 有 `distance_m` 字段，但没说原理。
  要判断它是「深度图统计量 / 单目几何 / 仿真直接给的 ground truth」，
  最准的办法是直接看源码实现。

用法：
      python probe_distance_source.py

它做了三件事：
  1. 打印 boosteros 包的安装路径（你也可以用编辑器直接打开看）
  2. 在包内递归搜索 distance_m，并把命中行的前后若干行一起打印出来
  3. 如果连 distance_m 都没搜到（可能是 C++ 扩展 / protobuf / 动态属性），
     会提示改用 `distance` 再搜一次，并建议把包路径发回来人工排查

手动替代方式（等价）：
  1) python -c "import boosteros,os; print(os.path.dirname(boosteros.__file__))"
  2) 用编辑器打开上面打印的路径，全局搜索 distance_m
"""
import os
import re

import boosteros


def main():
    pkg_root = os.path.dirname(boosteros.__file__)
    print(f"boosteros 包根目录:\n  {pkg_root}\n")

    patterns = [re.compile(r"distance_m", re.IGNORECASE),
                re.compile(r"\bdistance\b", re.IGNORECASE)]

    for p in patterns:
        hits = []
        for dirpath, _, files in os.walk(pkg_root):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(dirpath, fn)
                try:
                    with open(path, encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except Exception:
                    continue
                for idx, line in enumerate(lines):
                    if p.search(line):
                        start = max(0, idx - 6)
                        end = min(len(lines), idx + 7)
                        hits.append((path, idx + 1, lines[start:end]))

        label = "distance_m" if "distance_m" in p.pattern else "distance (fallback)"
        if not hits:
            print(f"[无命中] 以 `{label}` 搜索没有结果。")
            continue

        print(f"============ 以 `{label}` 搜索，命中 {len(hits)} 处 ============\n")
        for path, lineno, ctx in hits:
            print(f"### {path}:{lineno}")
            for j, cl in enumerate(ctx, start=lineno - 6):
                marker = ">>>" if p.search(cl) else "   "
                print(f"{j:5} {marker} {cl.rstrip()}")
            print()
        return  # 找到 distance_m 就停止

    print("提示：包内 Python 源码未出现 distance 相关代码，"
          "distance_m 可能来自编译扩展 / protobuf / 运行时动态赋值。"
          "请把上面的包根目录路径发回，我们一起进一步排查。")


if __name__ == "__main__":
    main()
