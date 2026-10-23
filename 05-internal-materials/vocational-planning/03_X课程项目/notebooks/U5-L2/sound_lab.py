# sound_lab.py
import warnings

warnings.filterwarnings("ignore", message=".*Unable to import Axes3D.*", category=UserWarning)

import os
import math
from array import array
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np

from boosteros.types import AudioData, Header

def synthesize_tone(
    freq: float = 440.0,
    duration: float = 1.0,
    wave_type: str = "sine",
    sample_rate: int = 16000,
    amplitude: int = 26000
) -> bytes:
    """
    根据物理参数与波形类型合成 PCM 字节数据。
    wave_type 支持: 'sine'(正弦波), 'square'(方波), 'sawtooth'(锯齿波), 'bell'(钟琴声)
    """
    samples = array("h")
    total_samples = int(sample_rate * duration)

    for i in range(total_samples):
        t = i / sample_rate
        phase = (t * freq) % 1.0

        if wave_type == "sine":
            val = math.sin(2 * math.pi * freq * t)
        elif wave_type == "square":
            val = 1.0 if phase < 0.5 else -1.0
        elif wave_type == "sawtooth":
            val = 2.0 * phase - 1.0
        elif wave_type == "bell":
            envelope = math.exp(-t * 4.0)
            harmonic = (
                1.0 * math.sin(2 * math.pi * freq * t)
                + 0.5 * math.sin(2 * math.pi * 2 * freq * t)
                + 0.25 * math.sin(2 * math.pi * 3 * freq * t)
            )
            val = harmonic * envelope / 1.75
        else:
            val = 0.0

        samples.append(int(amplitude * val))

    return samples.tobytes()


_playback_stream = None  # 保留未结束的播放流，防止下一次调用覆盖它


def play_sound(robot, pcm_data: bytes, sample_rate: int = 16000, volume: float = 0.8) -> None:
    """按顺序播放单声道PCM；成功后返回，失败或超时则报告异常。"""
    global _playback_stream
    terminal_states = ("SUCCEEDED", "FAILED", "CANCELLED")
    if _playback_stream is not None and _playback_stream.wait(timeout=0.0) not in terminal_states:
        raise RuntimeError("上一次播放尚未结束，请保留sound_lab模块中的_playback_stream检查状态，暂不重复播放。")
    header = Header()
    audio = AudioData(
        header=header,
        data=pcm_data,
        coding_format="pcm",
        sample_rate=sample_rate,
        channels=1,
        sample_format="S16LE",
    )

    stream = robot.audio_manager.play_stream(
        sample_rate=sample_rate,
        channels=1,
        sample_format="S16LE",
        volume=volume,
    )

    _playback_stream = stream

    try:
        chunk_bytes = 4096
        for start in range(0, len(audio.data), chunk_bytes):
            chunk = audio.data[start : start + chunk_bytes]
            chunk_audio = (
                audio.with_data(chunk)
                if hasattr(audio, "with_data")
                else AudioData(
                    header=header,
                    data=chunk,
                    coding_format="pcm",
                    sample_rate=sample_rate,
                    channels=1,
                    sample_format="S16LE",
                )
            )
            stream.write(chunk_audio)
    finally:
        stream.close()

    status = stream.wait(timeout=10.0)
    if status not in terminal_states:
        accepted = stream.cancel()
        status = stream.wait(timeout=5.0)
        raise RuntimeError(f"播放等待超时；取消请求提交：{accepted}，当前状态：{status}。声音可能未完整播放。")
    if status != "SUCCEEDED":
        raise RuntimeError(f"播放未成功，状态：{status}")

# ----------------- 加载同目录下的中文字体文件 -----------------
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "wqy-microhei.ttc")
if os.path.exists(FONT_PATH):
    zh_font = FontProperties(fname=FONT_PATH)
else:
    # 兼容直接在当前工作目录查找
    zh_font = FontProperties(fname="fonts/wqy-microhei.ttc") if os.path.exists("fonts/wqy-microhei.ttc") else None

plt.rcParams['axes.unicode_minus'] = False


def plot_waves(wave_configs: list, window_ms: float = 10.0, sample_rate: int = 16000) -> None:
    """
    绘制前几毫秒内的声波周期形态。
    """
    duration = window_ms / 1000.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    num_waves = len(wave_configs)

    fig, axes = plt.subplots(num_waves, 1, figsize=(9, 2.2 * num_waves), sharex=True)
    if num_waves == 1:
        axes = [axes]

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    wave_label_map = {
        "sine": "正弦波",
        "square": "方波",
        "sawtooth": "锯齿波",
        "bell": "钟琴声",
    }

    for idx, (ax, item) in enumerate(zip(axes, wave_configs)):
        freq = item.get("freq", 440)
        wtype = item.get("wave_type", "sine")
        phase = (t * freq) % 1.0

        if wtype == "sine":
            y = np.sin(2 * np.pi * freq * t)
        elif wtype == "square":
            y = np.sign(np.sin(2 * np.pi * freq * t))
        elif wtype == "sawtooth":
            y = 2.0 * phase - 1.0
        elif wtype == "bell":
            y = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(4 * np.pi * freq * t)) * np.exp(-t * 20.0)
        else:
            y = np.zeros_like(t)

        color = colors[idx % len(colors)]
        ax.plot(t * 1000, y, color=color, lw=1.8)

        # 设置中文标题与坐标轴
        sound_name = item.get("name", f"声音 {idx + 1}")
        type_str = wave_label_map.get(wtype, wtype)
        title_text = f"{sound_name} [{type_str}, 频率: {freq} Hz]"

        ax.set_title(title_text, loc="left", fontsize=11, fontproperties=zh_font)
        ax.set_ylabel("振幅 (Amplitude)", fontsize=10, fontproperties=zh_font)
        ax.grid(True, linestyle="--", alpha=0.5)

    axes[-1].set_xlabel("时间 (毫秒 / ms)", fontsize=10, fontproperties=zh_font)
    plt.tight_layout()
    plt.show()