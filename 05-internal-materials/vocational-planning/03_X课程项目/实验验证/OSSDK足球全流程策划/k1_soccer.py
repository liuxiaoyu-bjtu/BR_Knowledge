"""K1 足球应用草案：只通过 BoosterOS SDK 访问机器人。

本文件属于课程应用代码，不是 BoosterOS SDK 的新增 API。导入时不连接机器人。
默认只观察；运动、坐标解释和踢球供数分别由教师配置。未做真机验证。
依赖：Python >= 3.10、numpy；连接真机时另需已有 boosteros 及视觉依赖。
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field, replace
import json
import math
from pathlib import Path
import threading
import time
from typing import Any

import numpy as np

VERSION = "0.1.1-draft"


def wrap(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def stamp(value: Any) -> float:
    """保留传感器时间；没有时间戳时拒绝，绝不以收到消息的时间冒充。"""
    header = getattr(value, "header", None)
    candidate = getattr(value, "timestamp", None)
    if candidate is None and header is not None:
        candidate = getattr(header, "timestamp", None)
    if candidate is None or not math.isfinite(float(candidate)):
        raise ValueError("missing_sensor_timestamp")
    return float(candidate)


def to_odom(xy: tuple[float, float], pose: tuple[float, float, float]) -> tuple[float, float]:
    x, y, yaw = pose
    c, s = math.cos(yaw), math.sin(yaw)
    return x + c * xy[0] - s * xy[1], y + s * xy[0] + c * xy[1]


def from_odom(xy: tuple[float, float], pose: tuple[float, float, float]) -> tuple[float, float]:
    dx, dy = xy[0] - pose[0], xy[1] - pose[1]
    c, s = math.cos(pose[2]), math.sin(pose[2])
    return c * dx + s * dy, -s * dx + c * dy


@dataclass(frozen=True)
class Calibration:
    """核实记录由教师填写。布尔值是配置条件，不能代替原始实测证据。"""
    camera_id: str = "head"
    trunk_frame: str = "trunk"
    body_from_trunk: list[list[float]] | None = None
    tf_direction_verified: bool = False
    control_origin_verified: bool = False
    clocks_verified: bool = False
    rgb_depth_registered: bool = False
    depth_verified: bool = False
    depth_scale_m: float | None = None
    depth_invalid_raw: tuple[float, ...] = (0.0, 65535.0)
    ball_radius_m: float | None = None
    geometry_verified: bool = False
    ground_plane_body: tuple[float, float, float, float] | None = None
    motion_profile_verified: bool = False
    kick_feed_verified: bool = False
    evidence: str = ""

    @classmethod
    def load(cls, path: str | Path) -> "Calibration":
        return cls(**json.loads(Path(path).read_text(encoding="utf-8-sig")))

    def coordinate_error(self) -> str:
        if not (self.tf_direction_verified and self.control_origin_verified and self.clocks_verified):
            return "coordinate_or_clock_unverified"
        if not self.evidence.strip():
            return "missing_calibration_evidence"
        if self.body_from_trunk is None:
            return "missing_body_from_trunk"
        a = np.asarray(self.body_from_trunk, dtype=float)
        if a.shape != (4, 4) or not np.isfinite(a).all():
            return "invalid_body_from_trunk"
        if not np.allclose(a[3], [0, 0, 0, 1]) or not np.allclose(a[:3, :3].T @ a[:3, :3], np.eye(3), atol=1e-4):
            return "non_rigid_body_from_trunk"
        if not np.isclose(np.linalg.det(a[:3, :3]), 1, atol=1e-4):
            return "reflected_body_frame"
        if self.ball_radius_m is None or not 0 < self.ball_radius_m < 0.5:
            return "missing_or_invalid_ball_radius"
        return ""


@dataclass(frozen=True)
class SoccerConfig:
    """数值为离线开发起始值，现场确认后才可作为课程参数。"""
    labels: tuple[str, ...] = ("Ball",)
    confidence: float = 0.55
    head_pitch: float = 0.45
    head_yaws: tuple[float, ...] = (0.0, -0.60, 0.60)
    head_settle_s: float = 0.7
    observation_wait_s: float = 6.0
    body_sector_rad: float = math.pi / 3
    body_yaw_rate: float = 0.15
    body_turn_timeout_s: float = 10.0
    max_body_sectors: int = 5
    approach_step_s: float = 0.3
    approach_vx: float = 0.08
    approach_yaw_rate: float = 0.20
    turn_first_rad: float = 0.20
    handoff_distance_m: float = 0.75
    max_sensor_skew_s: float = 0.12
    max_frame_receipt_age_s: float = 0.3
    max_ball_age_s: float = 3.0
    kick_max_ball_age_s: float = 0.35
    depth_min_m: float = 0.15
    depth_max_m: float = 6.0
    min_depth_points: int = 24
    sphere_radius_tolerance_m: float = 0.025
    sphere_residual_m: float = 0.015
    max_ball_distance_m: float = 6.0
    max_total_time_s: float = 90.0
    max_path_m: float = 1.0
    control_period_s: float = 0.05
    kick_timeout_s: float = 8.0
    kick_min_dwell_s: float = 1.5
    verify_timeout_s: float = 4.0
    ball_moved_m: float = 0.3
    direction_rad: float = 0.0
    power: float = 1.0
    allow_kick: bool = False

    def validate(self) -> None:
        values = asdict(self)
        for key, value in values.items():
            if isinstance(value, (float, int)) and not isinstance(value, bool) and not math.isfinite(value):
                raise ValueError(f"non_finite_config:{key}")
        positive = ("head_settle_s", "observation_wait_s", "body_sector_rad", "body_yaw_rate",
                    "body_turn_timeout_s", "approach_step_s", "approach_vx", "approach_yaw_rate",
                    "handoff_distance_m", "max_sensor_skew_s", "max_frame_receipt_age_s",
                    "max_ball_age_s", "kick_max_ball_age_s", "max_total_time_s", "max_path_m",
                    "control_period_s", "kick_timeout_s", "verify_timeout_s", "ball_moved_m",
                    "depth_min_m", "sphere_radius_tolerance_m", "sphere_residual_m", "max_ball_distance_m")
        if any(values[key] <= 0 for key in positive):
            raise ValueError("non_positive_config")
        if not 0 < self.confidence <= 1 or not 1 <= self.power <= 10:
            raise ValueError("invalid_confidence_or_power")
        if not self.labels or not self.head_yaws or any(not math.isfinite(y) for y in self.head_yaws):
            raise ValueError("empty_or_invalid_search_config")
        if self.max_body_sectors < 0 or self.min_depth_points < 4 or self.depth_min_m >= self.depth_max_m:
            raise ValueError("invalid_depth_or_search_config")
        if self.body_sector_rad >= math.pi or self.kick_min_dwell_s < 0 or self.kick_min_dwell_s >= self.kick_timeout_s:
            raise ValueError("invalid_turn_or_kick_timing")


@dataclass(frozen=True)
class BallTarget:
    bbox: tuple[float, float, float, float]  # x, y, width, height；原图像素
    confidence: float

    @property
    def center(self) -> tuple[float, float]:
        x, y, w, h = self.bbox
        return x + w / 2, y + h / 2


def select_ball(results: list[Any], size: tuple[int, int], cfg: SoccerConfig,
                previous: BallTarget | None = None) -> BallTarget | None:
    """筛类别、置信度、边界，再优先保持同一目标；不直接取列表首项。"""
    width, height = size
    candidates = []
    for result in results:
        try:
            b = result.bbox
            x, y, w, h = map(float, (b.x, b.y, b.width, b.height))
            confidence = float(result.confidence)
            if result.class_name not in cfg.labels or not cfg.confidence <= confidence <= 1:
                continue
            if not all(math.isfinite(v) for v in (x, y, w, h, confidence)):
                continue
            if x < 0 or y < 0 or w <= 1 or h <= 1 or x + w > width or y + h > height:
                continue
            target = BallTarget((x, y, w, h), confidence)
            if previous is not None:
                distance = math.dist(target.center, previous.center) / max(width, height)
                ratio = w * h / (previous.bbox[2] * previous.bbox[3])
                if distance > 0.30 or not 0.25 <= ratio <= 4:
                    continue
            candidates.append(target)
        except (AttributeError, TypeError, ValueError):
            continue
    if previous is not None:
        return min(candidates, key=lambda t: math.dist(t.center, previous.center), default=None)
    return max(candidates, key=lambda t: (t.confidence, t.bbox[2] * t.bbox[3]), default=None)


@dataclass(frozen=True)
class Capture:
    sequence: int
    generation: int
    sensor_time: float
    received_mono: float
    size: tuple[int, int]
    camera_frame: str
    info_frame: str
    k: np.ndarray
    distortion: tuple[float, ...]
    trunk_from_camera: np.ndarray
    tf_time: float
    odom_pose: tuple[float, float, float]
    odom_time: float
    stationary: bool
    depth: np.ndarray | None = None
    depth_time: float | None = None
    depth_frame: str = ""


@dataclass(frozen=True)
class BallEstimate:
    valid: bool = False
    reason: str = "no_observation"
    sequence: int = 0
    generation: int = 0
    capture_time: float = 0.0
    received_mono: float = 0.0
    x: float | None = None
    y: float | None = None
    z: float | None = None
    method: str = "none"
    ball_odom: tuple[float, float] | None = None
    age_s: float = math.inf
    predicted: bool = False


def ray_ground_center(u: float, v: float, k: np.ndarray, body_from_camera: np.ndarray,
                      plane: tuple[float, float, float, float], radius: float) -> np.ndarray:
    """接地点射线与 n·p+d=0 求交，再沿地面法向移到球心；不假设 trunk 的 z=0 是地面。"""
    n = np.asarray(plane[:3], dtype=float)
    length = float(np.linalg.norm(n))
    if length < 1e-6 or not np.isfinite(plane).all():
        raise ValueError("invalid_ground_plane")
    n, d = n / length, float(plane[3]) / length
    ray = np.linalg.solve(k, [u, v, 1.0])
    ray /= np.linalg.norm(ray)
    origin = body_from_camera[:3, 3]
    direction = body_from_camera[:3, :3] @ ray
    denominator = float(n @ direction)
    if abs(denominator) < 0.08:
        raise ValueError("ray_near_horizon")
    scale = -(float(n @ origin) + d) / denominator
    if scale <= 0:
        raise ValueError("ground_behind_camera")
    return origin + scale * direction + radius * n


def depth_sphere_center(cap: Capture, target: BallTarget, cal: Calibration, cfg: SoccerConfig) -> np.ndarray:
    if not (cal.depth_verified and cal.rgb_depth_registered and cal.depth_scale_m is not None):
        raise ValueError("depth_semantics_unverified")
    if not math.isfinite(cal.depth_scale_m) or cal.depth_scale_m <= 0:
        raise ValueError("invalid_depth_scale")
    if cap.depth is None or cap.depth_time is None:
        raise ValueError("no_matched_depth")
    if cap.depth_frame != cap.camera_frame or abs(cap.depth_time - cap.sensor_time) > cfg.max_sensor_skew_s:
        raise ValueError("depth_frame_or_time_mismatch")
    if cap.depth.shape != (cap.size[1], cap.size[0]):
        raise ValueError("registered_depth_size_mismatch")
    x, y, w, h = target.bbox
    u, v = target.center
    left, right = int(x + 0.15 * w), int(x + 0.85 * w)
    top, bottom = int(y + 0.15 * h), int(y + 0.85 * h)
    step = max(1, int(max(w, h) / 30))
    vv, uu = np.mgrid[top:bottom:step, left:right:step]
    raw = cap.depth[vv, uu].astype(float)
    z = raw * cal.depth_scale_m
    valid = np.isfinite(z) & (z > cfg.depth_min_m) & (z < cfg.depth_max_m)
    valid &= ((uu - u) / (w / 2)) ** 2 + ((vv - v) / (h / 2)) ** 2 <= 0.65 ** 2
    for invalid in cal.depth_invalid_raw:
        valid &= raw != invalid
    if np.count_nonzero(valid) < cfg.min_depth_points:
        raise ValueError("insufficient_ball_depth")
    valid &= abs(z - np.median(z[valid])) <= 2 * float(cal.ball_radius_m)
    if np.count_nonzero(valid) < cfg.min_depth_points:
        raise ValueError("insufficient_foreground_depth")
    pixels = np.column_stack([uu[valid], vv[valid], np.ones(np.count_nonzero(valid))])
    points = np.linalg.solve(cap.k, pixels.T).T * z[valid, None]
    a = np.column_stack([2 * points, np.ones(len(points))])
    solution, _, rank, _ = np.linalg.lstsq(a, np.sum(points ** 2, axis=1), rcond=None)
    center = solution[:3]
    fitted_radius = math.sqrt(max(0, float(center @ center + solution[3])))
    residual = float(np.sqrt(np.mean((np.linalg.norm(points - center, axis=1) - fitted_radius) ** 2)))
    if rank < 4 or not np.isfinite(center).all() or not cfg.depth_min_m < center[2] < cfg.depth_max_m:
        raise ValueError("invalid_sphere_fit")
    if abs(fitted_radius - float(cal.ball_radius_m)) > cfg.sphere_radius_tolerance_m or residual > cfg.sphere_residual_m:
        raise ValueError("sphere_fit_quality_rejected")
    return center


def locate_ball(cap: Capture, target: BallTarget | None, cal: Calibration, cfg: SoccerConfig) -> BallEstimate:
    base = BallEstimate(sequence=cap.sequence, generation=cap.generation, capture_time=cap.sensor_time,
                        received_mono=cap.received_mono)
    if target is None:
        return replace(base, reason="no_selected_ball")
    error = cal.coordinate_error()
    if error:
        return replace(base, reason=error)
    try:
        if not cap.camera_frame or cap.camera_frame != cap.info_frame:
            raise ValueError("camera_info_frame_mismatch")
        if not all(math.isfinite(t) for t in (cap.sensor_time, cap.tf_time, cap.odom_time)):
            raise ValueError("invalid_capture_time")
        if len(cap.odom_pose) != 3 or not all(math.isfinite(v) for v in cap.odom_pose):
            raise ValueError("invalid_capture_odom")
        if max(abs(cap.tf_time - cap.sensor_time), abs(cap.odom_time - cap.sensor_time)) > cfg.max_sensor_skew_s:
            raise ValueError("capture_pose_time_mismatch")
        if cap.k.shape != (3, 3) or not np.isfinite(cap.k).all() or cap.k[0, 0] <= 0 or cap.k[1, 1] <= 0:
            raise ValueError("invalid_intrinsics")
        if any(not math.isfinite(d) or abs(d) > 1e-8 for d in cap.distortion):
            raise ValueError("image_requires_undistortion")
        transform = np.asarray(cal.body_from_trunk) @ cap.trunk_from_camera
        if transform.shape != (4, 4) or not np.isfinite(transform).all():
            raise ValueError("invalid_capture_transform")
        if (not np.allclose(transform[3], [0, 0, 0, 1])
                or not np.allclose(transform[:3, :3].T @ transform[:3, :3], np.eye(3), atol=1e-4)
                or not np.isclose(np.linalg.det(transform[:3, :3]), 1, atol=1e-4)):
            raise ValueError("non_rigid_capture_transform")
        try:
            point = depth_sphere_center(cap, target, cal, cfg)
            center = (transform @ np.append(point, 1))[:3]
            method = "depth_sphere"
        except ValueError as depth_error:
            if not (cal.geometry_verified and cal.ground_plane_body is not None and cap.stationary):
                raise ValueError(f"{depth_error};geometry_unavailable") from depth_error
            x, y, w, h = target.bbox
            center = ray_ground_center(x + w / 2, y + h, cap.k, transform,
                                       cal.ground_plane_body, float(cal.ball_radius_m))
            method = "ground_geometry"
        x, y, z = map(float, center)
        if not np.isfinite(center).all() or x < 0 or math.hypot(x, y) > cfg.max_ball_distance_m:
            raise ValueError("ball_out_of_model_range")
        return replace(base, valid=True, reason="ok", x=x, y=y, z=z, method=method,
                       ball_odom=to_odom((x, y), cap.odom_pose))
    except (ValueError, TypeError, np.linalg.LinAlgError) as exc:
        return replace(base, reason=str(exc))


def current_ball(ball: BallEstimate, pose: tuple[float, float, float], odom_time: float,
                 now_mono: float, cfg: SoccerConfig, *, kicking: bool = False) -> BallEstimate:
    if not ball.valid or ball.ball_odom is None:
        return ball
    sensor_age = odom_time - ball.capture_time
    age = max(now_mono - ball.received_mono, sensor_age)
    limit = cfg.kick_max_ball_age_s if kicking else cfg.max_ball_age_s
    if sensor_age < -cfg.max_sensor_skew_s or age < 0 or age > limit:
        return replace(ball, valid=False, age_s=age, reason="ball_expired_or_clock_reset")
    x, y = from_odom(ball.ball_odom, pose)
    # x=0 是合法坐标；不能将其用作丢球标志，也不能凭空补发零值。
    # x<0 仍超出本版前方寻球/踢球场景，并非 SDK 对负坐标的限制。
    if x < 0 or math.hypot(x, y) > cfg.max_ball_distance_m:
        return replace(ball, valid=False, age_s=age, reason="current_ball_out_of_range")
    return replace(ball, x=x, y=y, age_s=age, predicted=sensor_age > cfg.max_sensor_skew_s)


@dataclass(frozen=True)
class Observation:
    capture: Capture
    target: BallTarget | None
    ball: BallEstimate


@dataclass(frozen=True)
class Action:
    kind: str
    values: tuple[float, ...] = ()
    reason: str = ""


class SoccerPlanner:
    """无机器人依赖的有限状态机；时间由调用方传入，便于离线回放。"""
    TERMINAL = {"FINISHED", "STOPPED", "ERROR"}

    def __init__(self, cfg: SoccerConfig):
        cfg.validate()
        self.cfg = cfg
        self.state = "HEAD_SEARCH"
        self.reason = "not_started"
        self.generation = 0
        self.floor = 0.0
        self.started: float | None = None
        self.deadline = 0.0
        self.head_index = 0
        self.head_issued = False
        self.sectors = 0
        self.turn_origin = 0.0
        self.path_m = 0.0
        self.last_pose: tuple[float, float, float] | None = None
        self.resume = "LOCALIZE"
        self.kick_start = 0.0
        self.initial_ball_odom: tuple[float, float] | None = None
        self.kick_last_sequence = -1
        self.kick_finish_reason = ""

    def finish(self, state: str, reason: str) -> list[Action]:
        previous = self.state
        self.state, self.reason = state, reason
        self.generation += 1
        actions = [Action("kick_end", reason=reason)] if previous == "KICK" else []
        return actions + [Action("velocity", (0, 0, 0), reason)]

    def capture_allowed(self, now: float) -> bool:
        return (self.state in {"HEAD_SEARCH", "LOCALIZE", "KICK", "VERIFY"}
                and (self.state != "HEAD_SEARCH" or self.head_issued) and now >= self.floor)

    def _settle(self, now: float, resume: str) -> list[Action]:
        self.state, self.resume = "SETTLE", resume
        self.floor = now + self.cfg.head_settle_s
        self.generation += 1
        return [Action("velocity", (0, 0, 0), "settle")]

    def _verify(self, now: float, reason: str) -> list[Action]:
        self.state, self.reason, self.kick_finish_reason = "VERIFY", reason, reason
        self.generation += 1
        self.floor = now + self.cfg.head_settle_s
        self.deadline = self.floor + self.cfg.verify_timeout_s
        return [Action("kick_end", reason=reason), Action("velocity", (0, 0, 0), reason)]

    def step(self, now: float, observation: Observation | None, ball: BallEstimate,
             pose: tuple[float, float, float]) -> list[Action]:
        c = self.cfg
        if self.state in self.TERMINAL:
            return []
        if not all(math.isfinite(v) for v in pose):
            return self.finish("ERROR", "invalid_odom_pose")
        if self.started is None:
            self.started = now
        if self.last_pose is not None:
            self.path_m += math.dist(pose[:2], self.last_pose[:2])
        self.last_pose = pose
        if now - self.started >= c.max_total_time_s:
            return self.finish("FINISHED", "total_timeout")
        if self.path_m >= c.max_path_m:
            return self.finish("FINISHED", "path_limit")
        fresh = (observation is not None and observation.capture.generation == self.generation
                 and observation.capture.received_mono >= self.floor)
        usable = fresh and ball.valid
        if self.state == "HEAD_SEARCH":
            if not self.head_issued:
                self.generation += 1
                self.floor, self.deadline = now + c.head_settle_s, now + c.head_settle_s + c.observation_wait_s
                self.head_issued = True
                return [Action("velocity", (0, 0, 0)), Action("head", (c.head_pitch, c.head_yaws[self.head_index]))]
            if usable or (fresh and observation.target is not None):
                self.state, self.deadline = "LOCALIZE", now + c.observation_wait_s
                return []
            if fresh and observation.target is None:
                self.deadline = now  # 新图已明确未选到球，可以推进观察点
            if now >= self.deadline:
                self.head_index += 1
                self.head_issued = False
                if self.head_index == len(c.head_yaws):
                    self.head_index = 0
                    if self.sectors >= c.max_body_sectors:
                        return self.finish("FINISHED", "search_exhausted")
                    self.state, self.turn_origin = "BODY_TURN", pose[2]
                    self.deadline = now + c.body_turn_timeout_s
                    self.generation += 1
                    return [Action("velocity", (0, 0, c.body_yaw_rate))]
            return []
        if self.state == "BODY_TURN":
            if wrap(pose[2] - self.turn_origin) >= c.body_sector_rad:
                self.sectors += 1
                return self._settle(now, "HEAD_SEARCH")
            if now >= self.deadline:
                return self.finish("ERROR", "body_turn_timeout")
            return [Action("velocity", (0, 0, c.body_yaw_rate))]
        if self.state == "SETTLE":
            if now >= self.floor:
                self.state = self.resume
                self.deadline = now + c.observation_wait_s
            return []
        if self.state == "LOCALIZE":
            if usable:
                if math.hypot(float(ball.x), float(ball.y)) <= c.handoff_distance_m:
                    if not c.allow_kick:
                        return self.finish("FINISHED", "ready_for_kick_without_activation")
                    if ball.age_s > c.kick_max_ball_age_s:
                        return self.finish("FINISHED", "kick_feed_too_old")
                    self.state, self.kick_start = "KICK", now
                    self.initial_ball_odom, self.kick_last_sequence = ball.ball_odom, ball.sequence
                    return [Action("kick_begin", (float(ball.x), float(ball.y)))]
                angle = math.atan2(float(ball.y), float(ball.x))
                velocity = (0.0, 0.0, math.copysign(c.approach_yaw_rate, angle)) if abs(angle) > c.turn_first_rad else (c.approach_vx, 0.0, 0.0)
                self.state, self.deadline = "APPROACH", now + c.approach_step_s
                self.generation += 1
                return [Action("velocity", velocity)]
            if now >= self.deadline:
                self.state, self.head_index, self.head_issued = "HEAD_SEARCH", 0, False
                self.generation += 1
            return []
        if self.state == "APPROACH":
            if now >= self.deadline:
                return self._settle(now, "LOCALIZE")
            return []
        if self.state == "KICK":
            if now - self.kick_start >= c.kick_timeout_s:
                return self._verify(now, "kick_timeout")
            if not ball.valid or ball.age_s > c.kick_max_ball_age_s:
                return self._verify(now, "kick_ball_feed_lost")
            new_visual = fresh and ball.sequence != self.kick_last_sequence
            if new_visual:
                self.kick_last_sequence = ball.sequence
                if (self.initial_ball_odom is not None and ball.ball_odom is not None
                        and now - self.kick_start >= c.kick_min_dwell_s
                        and math.dist(ball.ball_odom, self.initial_ball_odom) >= c.ball_moved_m):
                    return self._verify(now, "ball_moved_observed")
            return [Action("kick_update", (float(ball.x), float(ball.y)))]
        if self.state == "VERIFY":
            if usable and self.initial_ball_odom is not None and ball.ball_odom is not None:
                moved = math.dist(ball.ball_odom, self.initial_ball_odom) >= c.ball_moved_m
                return self.finish("FINISHED", "ball_moved_observed" if moved else "ball_not_moved_observed")
            if now >= self.deadline:
                return self.finish("FINISHED", f"unconfirmed:{self.kick_finish_reason}")
        return []


class SoccerApp:
    """start/status/stop 为课程接口。慢推理独立运行；控制线程负责唯一的身体命令出口。"""

    def __init__(self, robot: Any, detector: Any, calibration: Calibration | None = None,
                 config: SoccerConfig | None = None):
        self.robot, self.detector = robot, detector
        self.calibration, self.config = calibration or Calibration(), config or SoccerConfig()
        self.config.validate()
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._rgb: deque = deque(maxlen=2)
        self._depth: deque = deque(maxlen=32)
        self._subscriptions: list[Any] = []
        self._events: deque = deque(maxlen=1000)
        self._observation: Observation | None = None
        self._planner = SoccerPlanner(self.config)
        self._threads: list[threading.Thread] = []
        self._manager: Any = None
        self._manager_may_be_active = False
        self._motion = False
        self._status_state, self._reason = "IDLE", "not_started"
        self._worker_error = ""
        self._generation_session = 0

    def _event(self, event: str, **values: Any) -> None:
        with self._lock:
            self._events.append({"monotonic": time.monotonic(), "event": event, **values})

    def _on_image(self, image: Any, *, depth: bool = False) -> None:
        if self._stop.is_set():
            return
        try:
            item = (stamp(image), time.monotonic(), image)
            with self._lock:
                (self._depth if depth else self._rgb).append(item)
        except (ValueError, TypeError) as exc:
            self._event("image_rejected", reason=str(exc))

    def _preflight_motion(self) -> None:
        cal = self.calibration
        error = cal.coordinate_error()
        if error or not cal.motion_profile_verified:
            raise ValueError(error or "motion_profile_unverified")
        if not ((cal.depth_verified and cal.rgb_depth_registered and cal.depth_scale_m is not None)
                or (cal.geometry_verified and cal.ground_plane_body is not None)):
            raise ValueError("no_verified_localization_method")
        if self.config.allow_kick and not (cal.kick_feed_verified and cal.depth_verified and cal.rgb_depth_registered):
            raise ValueError("kick_requires_verified_dynamic_depth_feed")
        if self.robot.get_mode() != "walk":
            raise RuntimeError("teacher_must_prepare_standing_walk_first")
        joints = {j.name: j for j in self.robot.list_joints()}
        for name, requested in (("aahead_pitch_joint", [self.config.head_pitch]), ("aahead_yaw_joint", self.config.head_yaws)):
            # 名称来自本机 list_joints 实测；不匹配时拒绝猜测。
            if name not in joints:
                raise ValueError(f"head_joint_not_found:{name}")
            limits = joints[name].limits
            if any(not limits.min <= value <= limits.max for value in requested):
                raise ValueError(f"head_target_out_of_limits:{name}")

    def start(self, *, enable_motion: bool = False) -> None:
        if any(t.is_alive() for t in self._threads):
            raise RuntimeError("previous_workers_still_running")
        if self._manager_may_be_active:
            raise RuntimeError("previous_kick_shutdown_unconfirmed")
        if enable_motion:
            self._preflight_motion()
        self._generation_session += 1
        self._motion = bool(enable_motion)
        self._stop.clear()
        self._worker_error = ""
        self._planner = SoccerPlanner(self.config)
        self._observation = None
        self._rgb.clear()
        self._depth.clear()
        self._status_state, self._reason = ("HEAD_SEARCH" if enable_motion else "OBSERVE_ONLY"), "running"
        try:
            self._subscriptions.append(self.robot.subscribe_image(self._on_image,
                camera_id=self.calibration.camera_id, img_type="rgb", queue_size=1, overflow="drop_oldest"))
            self._subscriptions.append(self.robot.subscribe_image(lambda image: self._on_image(image, depth=True),
                camera_id=self.calibration.camera_id, img_type="depth", queue_size=1, overflow="drop_oldest"))
        except Exception:
            self._stop.set()
            self._unsubscribe()
            raise
        self._threads = [threading.Thread(target=self._infer_loop, daemon=True, name="soccer-inference"),
                         threading.Thread(target=self._control_loop, daemon=True, name="soccer-control")]
        for worker in self._threads:
            worker.start()
        self._event("started", enable_motion=self._motion, version=VERSION)

    def _capture(self, item: tuple, generation: int, sequence: int) -> Capture:
        sensor_time, received, image = item
        info = self.robot.get_camera_info(camera_id=self.calibration.camera_id)
        if (info.width, info.height) != (image.width, image.height):
            raise ValueError("camera_info_size_mismatch")
        frame = image.header.frame_id
        transform = self.robot.get_transform(target_frame=self.calibration.trunk_frame, source_frame=frame)
        odom = self.robot.get_odom()
        pose = tuple(map(float, odom.pose_2d))
        if len(pose) != 3 or not all(math.isfinite(v) for v in pose):
            raise ValueError("invalid_capture_odom")
        with self._lock:
            matched = min(self._depth, key=lambda d: abs(d[0] - sensor_time), default=None)
            stationary = self._planner.state in {"HEAD_SEARCH", "LOCALIZE", "VERIFY"} if self._motion else self.calibration.geometry_verified
        return Capture(sequence, generation, sensor_time, received, (image.width, image.height), frame,
                       info.header.frame_id, np.asarray(info.k, dtype=float).reshape(3, 3), tuple(info.d),
                       np.asarray(transform.to_matrix(), dtype=float), stamp(transform), pose, stamp(odom), stationary,
                       None if matched is None else np.array(matched[2].to_numpy(), copy=True),
                       None if matched is None else matched[0], "" if matched is None else matched[2].header.frame_id)

    def _infer_loop(self) -> None:
        last_stamp, sequence, previous, previous_generation = -math.inf, 0, None, -1
        while not self._stop.is_set():
            with self._lock:
                now = time.monotonic()
                allowed = not self._motion or self._planner.capture_allowed(now)
                item = self._rgb[-1] if self._rgb else None
                generation, floor = self._planner.generation, self._planner.floor
            if (not allowed or item is None or item[0] <= last_stamp
                    or now - item[1] > self.config.max_frame_receipt_age_s
                    or (self._motion and item[1] < floor)):
                self._stop.wait(0.02)
                continue
            last_stamp, sequence = item[0], sequence + 1
            if generation != previous_generation:
                previous, previous_generation = None, generation
            try:
                capture_error = ""
                try:
                    cap = self._capture(item, generation, sequence)
                except Exception as exc:
                    capture_error = f"capture_unavailable:{type(exc).__name__}:{exc}"
                    cap = Capture(sequence, generation, item[0], item[1],
                                  (item[2].width, item[2].height), item[2].header.frame_id, "",
                                  np.eye(3), (), np.eye(4), item[0], (0, 0, 0), item[0], False)
                results = self.detector.detect(item[2].to_numpy(), confidence=self.config.confidence)
                if self._stop.is_set():
                    break
                target = select_ball(results, cap.size, self.config, previous)
                if target is not None or self._planner.state != "KICK":
                    previous = target
                estimate = (BallEstimate(reason=capture_error, sequence=sequence, generation=generation,
                                         capture_time=cap.sensor_time, received_mono=cap.received_mono)
                            if capture_error else locate_ball(cap, target, self.calibration, self.config))
                with self._lock:
                    if generation != self._planner.generation and self._motion:
                        continue
                    self._observation = Observation(cap, target, estimate)
                self._event("observation", sequence=sequence, capture_time=cap.sensor_time,
                            detected=target is not None, valid=estimate.valid, reason=estimate.reason,
                            method=estimate.method, x=estimate.x, y=estimate.y)
            except Exception as exc:
                self._worker_error = f"inference_or_capture:{type(exc).__name__}:{exc}"
                self._event("worker_error", reason=self._worker_error)
                self._stop.set()

    def _current(self, *, kicking: bool = False) -> tuple[BallEstimate, tuple, float]:
        odom = self.robot.get_odom()
        pose, odom_time = tuple(map(float, odom.pose_2d)), stamp(odom)
        if len(pose) != 3 or not all(math.isfinite(v) for v in pose):
            raise ValueError("invalid_current_odom")
        if self.calibration.clocks_verified:
            # odom 时间与本地单调时钟的前进速度另由控制循环检查。
            with self._lock:
                ball = self._observation.ball if self._observation else BallEstimate()
            return current_ball(ball, pose, odom_time, time.monotonic(), self.config, kicking=kicking), pose, odom_time
        return BallEstimate(reason="clocks_unverified"), pose, odom_time

    def _end_kick(self) -> None:
        if self._manager_may_be_active and self._manager is not None:
            self._manager.stop()
            self._manager_may_be_active = False

    def _execute(self, action: Action, source: BallEstimate | None = None) -> None:
        if not self._motion:
            return
        if action.kind == "kick_end":
            self._end_kick()
        elif action.kind == "velocity":
            if self._manager_may_be_active:
                raise RuntimeError("ordinary_velocity_conflicts_with_kick")
            self.robot.set_velocity(*action.values)
        elif action.kind == "head":
            self.robot.set_head_angle(pitch=action.values[0], yaw=action.values[1])
        elif action.kind == "kick_begin":
            self.robot.set_velocity(0.0, 0.0, 0.0)
            if self._manager is None:
                from boosteros.robots.booster import SoccerKickManager
                self._manager = SoccerKickManager(self.robot)
            self._manager_may_be_active = True  # start部分成功后异常也必须尝试关闭
            self._manager.start()
            ball, _, _ = self._current(kicking=True)
            if self._stop.is_set() or not ball.valid:
                raise RuntimeError("ball_expired_or_stop_requested_during_manager_start")
            self._manager.update_command(direction=self.config.direction_rad, power=self.config.power)
            self._manager.update_ball(x=ball.x, y=ball.y)
            source = ball
        elif action.kind == "kick_update":
            self._manager.update_ball(x=action.values[0], y=action.values[1])
        else:
            raise ValueError(f"unknown_action:{action.kind}")
        self._event("action", kind=action.kind, values=action.values, reason=action.reason,
                    source_sequence=None if source is None else source.sequence,
                    capture_time=None if source is None else source.capture_time,
                    age_s=None if source is None else source.age_s,
                    predicted=False if source is None else source.predicted)

    def _control_loop(self) -> None:
        started, clock_anchor = time.monotonic(), None
        try:
            while not self._stop.is_set():
                now = time.monotonic()
                if now - started >= self.config.max_total_time_s:
                    self._reason = "total_timeout"
                    break
                if self._motion:
                    ball, pose, sensor_now = self._current(kicking=self._planner.state == "KICK")
                    if clock_anchor is None:
                        clock_anchor = sensor_now, now
                    sensor_before, mono_before = clock_anchor
                    if abs((sensor_now - sensor_before) - (now - mono_before)) > max(0.5, 3 * self.config.max_sensor_skew_s):
                        raise RuntimeError("odom_clock_discontinuity_or_stale")
                    with self._lock:
                        actions = self._planner.step(now, self._observation, ball, pose)
                        self._status_state, self._reason = self._planner.state, self._planner.reason
                    for action in actions:
                        self._execute(action, ball)
                        if self._stop.is_set():
                            break
                    if self._planner.state in self._planner.TERMINAL:
                        break
                self._stop.wait(self.config.control_period_s)
        except Exception as exc:
            self._status_state, self._reason = "ERROR", f"control:{type(exc).__name__}:{exc}"
            self._event("control_error", reason=self._reason)
        finally:
            self._stop.set()
            errors = []
            if self._motion:
                try:
                    self._end_kick()
                except Exception as exc:
                    errors.append(f"kick_stop:{exc}")
                # 即使关闭管理器报错，也单独尝试零速度，保留两项调用结果。
                try:
                    self.robot.set_velocity(0.0, 0.0, 0.0)
                except Exception as exc:
                    errors.append(f"zero_velocity:{exc}")
            self._unsubscribe()
            if errors or self._worker_error:
                self._status_state, self._reason = "ERROR", ";".join(errors + ([self._worker_error] if self._worker_error else []))
            elif self._status_state not in self._planner.TERMINAL:
                self._status_state = "STOPPED"
                if self._reason == "running":
                    self._reason = "stop_requested"
            self._event("control_exited", reason=self._reason, physical_stop_confirmed=False)

    def _unsubscribe(self) -> None:
        with self._lock:
            subscriptions, self._subscriptions = self._subscriptions, []
        for subscription in subscriptions:
            try:
                subscription.unsubscribe()
            except Exception as exc:
                self._event("unsubscribe_error", reason=str(exc))

    def stop(self, timeout_s: float = 3.0) -> dict:
        self._stop.set()
        deadline = time.monotonic() + max(0, timeout_s)
        for worker in self._threads:
            if worker is not threading.current_thread():
                worker.join(max(0, deadline - time.monotonic()))
        return self.status()

    def status(self) -> dict:
        with self._lock:
            observation = self._observation
            workers = {worker.name: worker.is_alive() for worker in self._threads}
            stopping = self._stop.is_set() and any(workers.values())
            return {"version": VERSION, "state": "STOPPING" if stopping else self._status_state,
                    "reason": self._reason, "enable_motion": self._motion,
                    "detected": observation is not None and observation.target is not None,
                    "last_observation": None if observation is None else asdict(observation.ball),
                    "workers_alive": workers, "physical_kick_confirmed": False,
                    "physical_stop_confirmed": False, "path_odom_m": self._planner.path_m}

    def save_log(self, path: str | Path) -> None:
        with self._lock:
            content = {"status": self.status(), "config": asdict(self.config),
                       "calibration": asdict(self.calibration), "events": list(self._events)}
        # 不写 NaN/Infinity；未知值明确保存为 null。
        def clean(value: Any) -> Any:
            if isinstance(value, float) and not math.isfinite(value):
                return None
            if isinstance(value, dict):
                return {key: clean(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [clean(item) for item in value]
            return value
        Path(path).write_text(json.dumps(clean(content), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    print(f"k1_soccer {VERSION}: 请导入 SoccerApp；本文件直接运行不会连接或驱动机器人。")
