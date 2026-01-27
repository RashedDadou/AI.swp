# Animations.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from typing import List, Optional
from Plane_Layers import PlaneLayer

# ────────────────────────────────────────────────
# إعدادات عامة
# ────────────────────────────────────────────────
X = np.linspace(-6, 6, 400)
BASE_HEIGHT = 1.25

# ──── شكل السمكة الأصلي (محافظ عليه تمامًا كما طلب ─────
Y_ORIGINAL = (
    BASE_HEIGHT
    + 0.45 * np.sin(1.15 * X)
    + 0.18 * np.cos(5 * X)
    + 0.15 * np.cos(3 * X)
    - 0.12 * (np.abs(X) / 6) ** 1.2
    + 0.3 * np.sin(1.2 * X)
)

DEFAULT_HALF_WIDTH = 1.8
DEFAULT_FRAMES = 120
DEFAULT_MAX_PRESSURE_FRAME = 70
DEFAULT_FPS = 24
DEFAULT_TALON_DROP_FACTOR = 0.5
DEFAULT_POWER_EXPONENT = 3.0           # من plane_layer_demo (أفضل)
DEFAULT_FILL_THICKNESS = 0.50          # من الديمو (أنيق)
DEFAULT_FILL_COLOR = 'lightsalmon'     # من الديمو
DEFAULT_FILL_ALPHA = 0.38              # من الديمو


def create_pressure_animation(
    pressure_layers: List[PlaneLayer],
    output_file: str = "pressure_animation.gif",
    half_width: float = DEFAULT_HALF_WIDTH,
    frames: int = DEFAULT_FRAMES,
    max_pressure_frame: int = DEFAULT_MAX_PRESSURE_FRAME,
    fps: int = DEFAULT_FPS,
    talon_drop_factor: float = DEFAULT_TALON_DROP_FACTOR,
    power_exponent: float = DEFAULT_POWER_EXPONENT,
    max_depth_multiplier: float = 14.0,
    title: str = "محاكاة ضغط عبر طبقات Plane Layer",
    custom_text: str = None,
) -> None:
    if not pressure_layers:
        raise ValueError("يجب تمرير طبقة ضغط واحدة على الأقل")

    main_layer = pressure_layers[-1]
    plane_center = main_layer.position[0]
    plane_y = main_layer.position[1]
    total_force = sum(layer.force for layer in pressure_layers)

    # معامل ضغط من الديمو الثابت (أقل مبالغة)
    pressure_factor = total_force * 0.018

    fig, ax = plt.subplots(figsize=(12, 7), dpi=120)

    def update(frame):
        ax.clear()

        if frame < max_pressure_frame:
            progress = frame / max_pressure_frame
            progress = progress * progress * (3 - 2 * progress)
            current_pressure = progress
        else:
            current_pressure = 1.0

        # عمق التشوه مع الأس 3 (من الديمو)
        max_depth = pressure_factor * max_depth_multiplier * current_pressure
        mask = (X >= plane_center - half_width) & (X <= plane_center + half_width)
        dist = np.abs(X[mask] - plane_center)
        depth = max_depth * (1 - (dist / half_width) ** power_exponent)

        y_deformed = Y_ORIGINAL.copy()
        y_deformed[mask] -= depth

        # ─── الرسم (مع التحسينات من plane_layer_demo) ─────
        ax.plot(X, Y_ORIGINAL, color='gray', ls='--', lw=1.4, alpha=0.65,
                label='السمكة قبل الضغط' if frame == 0 else None)

        ax.fill_between(X, y_deformed - DEFAULT_FILL_THICKNESS, y_deformed + DEFAULT_FILL_THICKNESS,
                        color=DEFAULT_FILL_COLOR, alpha=DEFAULT_FILL_ALPHA,
                        label='جسم السمكة المشوه' if frame == 0 else None)
        ax.plot(X, y_deformed, color='darkred', lw=2.9,
                label='سطح السمكة بعد الضغط' if frame == 0 else None)

        # رسم الطبقات
        for i, layer in enumerate(pressure_layers):
            y_pos = layer.position[1]
            alpha = max(0.25, 0.5 - i * 0.08)
            lw = 5.5 - i * 0.8
            label = f"{layer.name} ({layer.force:.1f} كجم)" if frame == 0 else None
            ax.hlines(y_pos, plane_center - half_width, plane_center + half_width,
                      color='royalblue', lw=lw, alpha=alpha, label=label)

        # مخالب
        drop = current_pressure * talon_drop_factor
        talon_y_bottom = plane_y + 0.8 - drop
        talon_y_top = talon_y_bottom + 0.75
        talon_xs = np.array([-0.9, -0.3, 0.3, 0.9]) + plane_center
        ax.fill(talon_xs, [talon_y_bottom]*4, [talon_y_top]*4,
                color='saddlebrown', alpha=0.68,
                label='مخالب النسر' if frame == 0 else None)

        # نص
        text = custom_text or f"ضغط: {current_pressure*100:.0f}%\nإجمالي القوة: {total_force:.1f} كجم"
        ax.text(0, plane_y + 1.35, text,
                ha='center', va='bottom', fontsize=10,
                bbox=dict(facecolor='white', edgecolor='navy', alpha=0.85,
                          boxstyle='round,pad=0.4'))

        ax.set_title(title, fontsize=13, pad=12)
        ax.set_xlabel("طول السمكة")
        ax.set_ylabel("الارتفاع")
        ax.set_ylim(0.4, 3.6)
        ax.grid(True, alpha=0.22)
        ax.legend(loc='upper right', fontsize=9, framealpha=0.92)
        ax.set_aspect('equal', adjustable='box')

    ani = FuncAnimation(fig, update, frames=frames, interval=60, blit=False)
    
    fig.tight_layout()
    ani.save(output_file, writer=PillowWriter(fps=fps), dpi=120, bbox_inches='tight')
    
    plt.close(fig)
    print(f"تم حفظ: {output_file}")