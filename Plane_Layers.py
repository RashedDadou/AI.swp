import numpy as np
from typing import List, Optional


class PlaneLayer:
    """
    كائن طبقة مرجعية فيزيائية ديناميكية – تدعم التفاعل السطحي والنطاق
    """

    def __init__(
        self,
        name: str,
        position: List[float],
        force: float = 0.0,
        depth: float = 1.0,
        radius: float = 1.0,
        extent: List[float] = None,
        shape_type: str = "plane",
    ):
        self.name = name
        self.position = np.array(position, dtype=float)
        self.force = float(force)
        self.depth = float(depth)
        self.radius = float(radius)
        self.extent = np.array(extent or [radius*2, radius*2, depth], dtype=float)
        self.shape_type = shape_type  # "plane", "sphere", "cylinder", ...

    def interact(self, other: 'PlaneLayer') -> float:
        if other is None:
            return 0.0

        distance = np.linalg.norm(self.position - other.position)
        if distance > self.radius + other.radius:
            return 0.0

        overlap = 1 - (distance / (self.radius + other.radius))
        combined_force = (self.force + other.force) * overlap ** 1.5
        effective_distance = max(distance, 1e-6)

        return combined_force / effective_distance

    def x2_effected(self, other: Optional['PlaneLayer'] = None) -> float:
        if other is None:
            return self.force * 2.0

        base = self.interact(other)
        return base * 2.0 * (1 + 0.3 * (self.depth / other.depth))

    def overlaps_with(self, other: 'PlaneLayer') -> bool:
        distance = np.linalg.norm(self.position - other.position)
        return distance <= self.radius + other.radius

    def __repr__(self) -> str:
        pos = self.position.tolist()
        return f"PlaneLayer({self.name!r}, pos={pos}, force={self.force:.2f}, r={self.radius:.2f})"

    def __str__(self) -> str:
        return f"{self.name} @ {self.position.tolist()} | f={self.force:.2f} | r={self.radius:.2f}"

# اختبار بسيط عند تشغيل الملف مباشرة
if __name__ == "__main__":
    p1 = PlaneLayer("eagle", [0.0, 2.5, 0.0], force=18.0)
    p2 = PlaneLayer("fish_surface", [0.0, 1.25, 0.0], force=0.0)

    print(p1)
    print(p2)

    print(f"interact     : {p1.interact(p2):.4f}")
    print(f"x2_effected  : {p1.x2_effected(p2):.4f}")
    print(f"self x2      : {p1.x2_effected():.4f}")