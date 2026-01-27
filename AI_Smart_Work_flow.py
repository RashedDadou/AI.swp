import time
from typing import List, Dict
import logging
import numpy as np
from Plane_Layers import PlaneLayer
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from Plane_Layers import PlaneLayer
from Animations import create_pressure_animation

# تهيئة السجل (Logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

"""
Professional animated demo: Invisible Plane Layer
- Slow pressure buildup on the fish through the invisible plane
- Exports GIF
"""

# ────────────────────────────────────────────────
# إعدادات مشتركة
# ────────────────────────────────────────────────
x = np.linspace(-6, 6, 400)
base_height = 1.25

# شكل السمكة الأصلي
y_original = (
    base_height
    + 0.45 * np.sin(1.15 * x)
    + 0.18 * np.cos(5 * x)
    + 0.15 * np.cos(3 * x)
    - 0.12 * (np.abs(x) / 6) ** 1.2
    + 0.3 * np.sin(1.2 * x)
)

# إعدادات الـ animation
frames = 120
max_pressure_frame = 70
fps = 24

class AISmartWorkflow:
    def __init__(self):
        self.tasks: List[Dict] = []
        self.dependencies: Dict[str, List[str]] = {}
        self.integration_rules: Dict[tuple, int] = {}
        self.planes: Dict[str, PlaneLayer] = {}
        self.render_time = 0.0
        # جديد: تخزين chains التلقائية
        self.auto_chains: List[List[str]] = []                               # وقت الرندر
        
    def add_task(
        self,
        name: str,
        complexity: float,
        dependencies: List[str] = None,
        is_plane: bool = False,
        proxy_weight: float = None,
        proxy_pressure_factor: float = 1.0,
        plane_position: List[float] = None,
        plane_force: float = None,
        # ────── الجديد ──────
        interacts_with: str = None,           # اسم المهمة الأخرى
        interaction_type: str = None,         # "touch", "press", "hold", ...
        interaction_force_multiplier: float = 1.0,  # معامل قوة إضافي
    ):
        dependencies = dependencies or []
        
        task = {
            "name": name,
            "complexity": complexity,
            "is_plane": is_plane,
            "dependencies": dependencies,
            "interacts_with": interacts_with,
            "interaction_type": interaction_type,
        }
        self.tasks.append(task)
        self.dependencies[name] = dependencies

        if is_plane:
            if plane_position is None:
                plane_position = [0.0, 0.0, 0.0]
            force = plane_force if plane_force is not None else (proxy_weight or 0.0)

            plane = PlaneLayer(
                name=name,
                position=plane_position,
                force=force
            )
            self.planes[name] = plane
            task["plane"] = plane

        if proxy_weight is not None:
            pressure_factor = proxy_pressure_factor
            deform_bonus = proxy_weight * pressure_factor * 0.38  # متوسط

            task["physics_proxy"] = {
                "weight_kg": proxy_weight,
                "pressure_factor": pressure_factor,
                "deformation_bonus": round(deform_bonus, 2),
            }

            task["complexity"] += deform_bonus

            logging.info(
                f"Physics proxy added to '{name}': weight={proxy_weight}kg → "
                f"+{deform_bonus:.2f} complexity (factor={pressure_factor})"
            )
             
        # ─── الجزء الديناميكي الجديد ───
        if interaction_type and interaction_with:
            self._auto_create_interaction_planes(
                task_name=name,
                interaction_with=interaction_with,
                interaction_type=interaction_type,
                plane_position=plane_position
            )
               
        # ────── الجزء الديناميكي الجديد ──────
        if interacts_with and interaction_type:
            self._auto_create_interaction_planes(
                name,
                interacts_with,
                interaction_type,
                plane_position,
                plane_force,
                interaction_force_multiplier
            )
        # ────── الجزء الديناميكي ──────
        if interacts_with and interaction_type:
            if interacts_with not in self.dependencies:
                logging.warning(f"المهمة '{interacts_with}' غير موجودة بعد – سيتم الإنشاء لاحقًا")
                return

            self._auto_create_interaction_planes(
                task1_name=name,
                task2_name=interacts_with,
                interaction_type=interaction_type,
                base_position=plane_position,
                base_force=plane_force,
                multiplier=interaction_force_multiplier
            )
               
    def add_plane_task(
        self,
        name: str,
        position: List[float],
        force: float,
        depth: float = 1.0,
        dependencies: List[str] = None
    ):
        plane = PlaneLayer(name, position, force, depth)
        self.planes[name] = plane
        self.tasks.append({"name": name, "type": "plane", "plane": plane})
        self.dependencies[name] = dependencies or []

    def add_object_task(self, name: str, complexity: float, dependencies: List[str] = None):
        self.tasks.append({"name": name, "type": "object", "complexity": complexity})
        self.dependencies[name] = dependencies or []

    def _auto_create_interaction_planes(
        self,
        task1_name: str,
        task2_name: str,
        interaction_type: str,
        base_position: List[float] = None,
        base_force: float = None,
        multiplier: float = 1.0,
    ):
        """
        إنشاء طبقات Plane تلقائيًا لكل طرف في التفاعل مع:
        - شرط عدم التكرار
        - قوى حسب نوع التفاعل
        - إضافة تلقائية للـ animation chain
        """
        # تحقق إن المهمتين موجودتين فعلاً
        if task1_name not in [t["name"] for t in self.tasks] or task2_name not in [t["name"] for t in self.tasks]:
            logging.warning(f"مهمة '{task1_name}' أو '{task2_name}' غير موجودة – لا يمكن إنشاء تفاعل")
            return

        # قوى افتراضية من force_map
        base_force = base_force or INTERACTION_FORCE_MAP.get(interaction_type, 5.0)
        force1 = base_force * multiplier
        force2 = force1 * 0.7  # الطرف الثاني أقل قوة (يمكن تخصيصه لاحقًا)

        plane1_name = f"plane_{task1_name}_{interaction_type}"
        plane2_name = f"plane_{task2_name}_{interaction_type}"

        # شرط عدم التكرار (نفس الطبقة ما تُنشأ مرتين)
        if plane1_name in self.planes or plane2_name in self.planes:
            logging.info(f"التفاعل '{interaction_type}' بين {task1_name} و {task2_name} موجود بالفعل – تجاهل")
            return

        # موقع افتراضي إذا ما مررش
        pos1 = base_position or [0.0, 1.0, 0.0]
        pos2 = [pos1[0], pos1[1] - 0.08, pos1[2]]  # قريب جدًا (المنتصف)

        # إنشاء الطبقة الأولى
        self.add_plane_task(
            name=plane1_name,
            position=pos1,
            force=force1,
            depth=0.05,
            dependencies=[task1_name]
        )
        logging.info(f"أُنشئت طبقة تلقائية: {plane1_name} (force={force1:.1f})")

        # إنشاء الطبقة الثانية
        self.add_plane_task(
            name=plane2_name,
            position=pos2,
            force=force2,
            depth=0.05,
            dependencies=[task2_name]
        )
        logging.info(f"أُنشئت طبقة تلقائية: {plane2_name} (force={force2:.1f})")

        # ربط في chain تلقائي
        chain = [plane1_name, plane2_name]
        self.auto_chains.append(chain)  # لتتبع الـ chains التلقائية
        forces = self.simulate_chain(chain)
        logging.info(f"تفاعل '{interaction_type}' أُنشئ تلقائيًا: {task1_name} ↔ {task2_name} → قوى: {forces}")

        # ربط تلقائي في الـ animation (لو الدالة موجودة)
        if hasattr(self, 'animate_interaction'):
            output_file = f"auto_{interaction_type}_{task1_name}_{task2_name}.gif"
            self.animate_interaction(chain, output_file=output_file)
            logging.info(f"تم إنشاء أنيميشن تلقائي: {output_file}")
        
    def simulate_chain(self, chain: List[str]):
        """محاكاة سلسلة تفاعلات مع plane.x2"""
        forces = []
        for i in range(len(chain)-1):
            layer1 = self.planes.get(chain[i])
            layer2 = self.planes.get(chain[i+1])
            if layer1 and layer2:
                effected = layer1.x2_effected(layer2)
                forces.append(effected)
                logging.info(f"{chain[i]} → {chain[i+1]} : {effected:.3f}")
        return forces

    def set_integration_rule(self, group: List[str], priority: int):
        if not group:
            logging.warning("تم تمرير مجموعة دمج فارغة – سيتم تجاهلها")
            return
        
        sorted_group = tuple(sorted(group))
        self.integration_rules[sorted_group] = priority
    
    def optimize_sequence(self) -> List[List[str]]:
        """ترتيب ذكي: planes أولاً + دمج + باقي المهام"""
        sequence = []
        processed = set()

        # 1. كل الـ planes أولاً
        for task in self.tasks:
            if task.get("is_plane", False) and task["name"] not in processed:
                sequence.append([task["name"]])
                processed.add(task["name"])

        # 2. مجموعات الدمج حسب الأولوية
        for group_tuple, prio in sorted(self.integration_rules.items(), key=lambda x: x[1]):
            group = list(group_tuple)
            if all(t in self.dependencies for t in group) and not any(t in processed for t in group):
                sequence.append(group)
                processed.update(group)

        # 3. الباقي فرديًا
        for task in self.tasks:
            if task["name"] not in processed:
                sequence.append([task["name"]])

        return sequence

    def render_sequentially(self, show_animation_log: bool = True):
        """تنفيذ متسلسل + عرض log animation بسيط"""
        sequence = self.optimize_sequence()
        total_time = 0.0
        anim_log = []

        for step in sequence:
            if len(step) > 1:
                step_time = sum(t["complexity"] for t in self.tasks if t["name"] in step) * 0.88
                logging.info(f"دمج مجموعة: {', '.join(step)} → {step_time:.1f}s")
            else:
                task_name = step[0]
                task = next(t for t in self.tasks if t["name"] == task_name)
                step_time = task["complexity"] * (0.75 if task.get("is_plane", False) else 1.1)
                logging.info(f"معالجة: {task_name} → {step_time:.1f}s")

            time.sleep(step_time / 5)  # تسريع المحاكاة
            total_time += step_time

            # جمع بيانات للـ animation log
            if task.get("is_plane", False):
                anim_log.append({
                    "step": task_name if len(step)==1 else " + ".join(step),
                    "time": round(step_time, 1),
                    "weight": task.get("physics_proxy", {}).get("weight_kg"),
                    "deform_bonus": task.get("physics_proxy", {}).get("deformation_bonus")
                })
            elif "physics_proxy" in task:
                anim_log.append({...})  # لو عايز تضيف الـ proxy في خطوة المهمة اللي فيها
                
                anim_log.append({
                    "step": task_name if len(step)==1 else " + ".join(step),
                    "time": round(step_time, 1),
                    "weight": task.get("physics_proxy", {}).get("weight_kg"),
                    "deform_bonus": task.get("physics_proxy", {}).get("deformation_bonus")
                })

        self.render_time = total_time
        logging.info(f"إجمالي وقت التوليد: {total_time:.1f} ثانية")

        if show_animation_log and anim_log:
            self._print_animation_log(anim_log)

        return total_time

    def animate_interaction(self, chain: List[str], output_file="plane_chain.gif"):
        """animation بسيط للسلسلة"""
        if not all(p in self.planes for p in chain):
            logging.warning("بعض العناصر ليست planes")
            return

        fig, ax = plt.subplots(figsize=(10, 4))
        positions = [self.planes[p].position[0] for p in chain]  # x فقط
        forces_accum = [0]

        def update(frame):
            ax.clear()
            current_force = 0
            for i in range(min(frame, len(chain)-1)):
                f = self.planes[chain[i]].x2_effected(self.planes[chain[i+1]])
                current_force += f
                ax.arrow(positions[i], 0, positions[i+1]-positions[i], 0,
                         head_width=0.05, head_length=0.1, fc='blue', ec='blue', alpha=0.6)
                ax.text((positions[i]+positions[i+1])/2, 0.1, f"{f:.2f}×2", fontsize=9)

            forces_accum.append(current_force)
            ax.plot(range(len(forces_accum)), forces_accum, 'r-o', lw=2, label="Accumulated Effect")
            ax.set_xlim(min(positions)-0.5, max(positions)+0.5)
            ax.set_ylim(-0.2, max(forces_accum)*1.3 + 0.5)
            ax.set_title(f"Plane.x2 Effected Chain: {' → '.join(chain)}")
            ax.set_xlabel("Position")
            ax.set_ylabel("Accumulated Interaction Force")
            ax.grid(True, alpha=0.3)
            ax.legend()

        ani = FuncAnimation(fig, update, frames=len(chain)+5, interval=800, repeat=True)
        ani.save(output_file, writer=PillowWriter(fps=1.5), dpi=120)
        plt.close(fig)
        logging.info(f"Animation saved: {output_file}")

    def _print_animation_log(self, steps: List[Dict]):
        """تصدير تمثيل نصي بسيط للـ animation"""
        print("\n--- Simple Plane Animation Log ---")
        for i, s in enumerate(steps, 1):
            weight_str = f"weight={s['weight']}kg" if s['weight'] else "no proxy"
            deform_str = f"+{s['deform_bonus']:.1f} complexity" if s['deform_bonus'] else ""
            print(f"Frame {i:2d} | {s['step']:20} | {s['time']:5.1f}s | {weight_str} {deform_str}")
        print("--- End of animation log ---\n")

# ────────────────────────────────────────────────────────────────
# مثال جديد: النسر على عش فوق السمكة (nest scenario)
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    workflow = AISmartWorkflow()

    # تعريف متغير مشترك (لو مش معرّف في مكان آخر)
    base_height = 1.25

    # ─── سيناريو السمكة والنسر (القديم) ───────────────────────────────
    workflow.add_task("nest_base", complexity=3, dependencies=[])
    workflow.add_task(
        "nest_plane", complexity=2, is_plane=True, dependencies=["nest_base"],
        plane_position=[0.0, base_height + 0.5, 0.0], plane_force=18.0 * 0.25
    )
    workflow.add_task(
        "eagle_plane", complexity=4, is_plane=True, dependencies=["nest_plane"],
        plane_position=[0.0, base_height + 1.0, 0.0], proxy_weight=18.0
    )
    workflow.add_task("fish_body", complexity=5, dependencies=["nest_base", "eagle_plane"])

    workflow.set_integration_rule(["nest_base", "fish_body"], priority=1)

    total_time = workflow.render_sequentially()
    print(f"Rendering completed in {total_time:.1f} seconds with Plane and AI.swp.")

    # محاكاة وأنيميشن السلسلة القديمة
    chain_old = ["nest_plane", "eagle_plane"]
    forces_old = workflow.simulate_chain(chain_old)
    print(f"قوى التراكم (النسر ← العش): {forces_old}")

    layers_old = [
        workflow.planes.get("nest_plane"),
        workflow.planes.get("eagle_plane")
    ]
    layers_old = [l for l in layers_old if l is not None]

    if layers_old:
        create_pressure_animation(
            pressure_layers=layers_old,
            output_file="nest_eagle_fish_demo.gif",
            title="النسر → العش → السمكة",
            custom_text="Plane Layer تنقل الضغط كاملاً إلى السمكة"
        )

    # ─── سيناريو جديد: الفنجان + اليد (مع التفاعل التلقائي) ───────────
    workflow.add_task("table", complexity=3, dependencies=[])
    workflow.add_task("cup", complexity=5, dependencies=["table"])

    # إضافة اليد مع تفاعل تلقائي (سيولّد plane_hand_hold + plane_cup_hold تلقائيًا)
    workflow.add_task(
        name="hand",
        complexity=8,
        dependencies=["cup"],               # ← صححنا depends_on إلى dependencies
        interacts_with="cup",
        interaction_type="hold",
        interaction_force_multiplier=1.3,
        plane_position=[0.0, 1.1, 0.0]
    )

    # استدعاء تلقائي للأنيميشن على آخر تفاعل (اختياري)
    if workflow.auto_chains:
        last_chain = workflow.auto_chains[-1]
        workflow.animate_interaction(
            chain=last_chain,
            output_file=f"auto_hold_hand_cup.gif"
        )
        print(f"تم إنشاء أنيميشن تلقائي للتفاعل: {last_chain}")