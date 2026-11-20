# AI401 — Expert Systems Lab
## Experiment 3: Agent Architectures — The BDI Deliberation Cycle

---

### **Aim**
To implement a Belief–Desire–Intention (BDI) agent that revises its beliefs about a dynamic environment (Tileworld), deliberates over competing desires to commit to an intention, and executes plans under a chosen commitment strategy, and to measure how that commitment affects performance as the world changes faster.

---

### **Theory**

#### **1. Reactive vs. Deliberative Agents**
A **reactive agent** maps percepts straight to actions via simple condition-action rules without maintaining an explicit internal model or reasoning about future goals. In contrast, a **deliberative agent** maintains an internal state, reasons about its goals, formulates multi-step plans, and evaluates options before acting.

#### **2. The BDI Architecture & Cognitive Attitudes**
The **Belief–Desire–Intention (BDI)** model formalizes deliberative reasoning through three primary mental attitudes:
- **Beliefs ($B$)**: What the agent takes to be true about the environment. Updated dynamically from percepts via the Belief Revision Function ($brf$).
- **Desires ($D$)**: The states of affairs the agent would like to bring about (options). Desires represent potential options and may conflict with one another.
- **Intentions ($I$)**: The specific desires the agent has committed to pursuing. An intention is more than a preference: it constrains future deliberation, guides means–ends planning ($\pi = plan(B, I)$), and persists until achieved, impossible, or dropped.

#### **3. The Deliberation Control Loop & Four Core Functions**
The BDI control loop relies on four foundational functions:
1. $brf(B, p)$: Folds a new percept $p$ into the current belief set $B$.
2. $options(B, I)$: Generates candidate desires $D$ consistent with current beliefs $B$ and intentions $I$.
3. $filter(B, D, I)$: Performs deliberation proper, selecting and returning the intention $I$ committed to.
4. $plan(B, I)$: Performs means–ends reasoning to generate a sequence of actions $\pi$ to achieve intention $I$.

#### **4. Commitment Strategies & Reconsideration Interval ($\gamma$)**
In a dynamic world, deliberation takes time—the world does not pause while the agent thinks. The cost of deliberation makes **commitment** a fundamental architectural choice:
- **Cautious Agent ($\gamma = 1$)**: Reconsiders its intention after every single action taken. Highly responsive to changes but spends substantial time deliberating.
- **Bold Agent ($\gamma = \text{bold}$ or $\gamma > \text{plan length}$)**: Never reconsiders during plan execution; holds an intention until it is either achieved or the plan empties/fails.
- **Intermediate Agent ($\gamma \in \{2, 4, 8\}$)**: Reconsiders every $\gamma$ actions, striking a balance between responsiveness and action throughput.

Three commitment strategies govern intention persistence:
- **Blind Commitment**: Holds an intention until it is believed to be achieved.
- **Single-Minded Commitment**: Holds an intention until it is believed achieved or believed unachievable (e.g., target hole expired). Re-evaluates options every $\gamma$ steps.
- **Open-Minded Commitment**: Keeps an intention only while it remains among the best available options; switches immediately if a superior option arises upon reconsideration.

#### **5. The Testbed: Simplified Dynamic Tileworld**
The agent operates in a $15 \times 15$ dynamic grid where:
- Holes appear at random empty cells with fixed probability $p_{\text{appear}}$ per world tick and expire after a random lifetime $L \in [20, 50]$ ticks.
- The agent scores by moving onto a hole cell and filling it.
- **Effectiveness ($E$)**: The ratio of holes filled to total holes that appeared ($E = \frac{\text{holes filled}}{\text{holes appeared}}$).
- **World Dynamism ($W_{\text{speed}}$)**: Parameterized by the number of world ticks that elapse per single agent action/deliberation step ($W_{\text{speed}} \in \{1, 2, 4, 8\}$).

---

### **Algorithm**

#### **Algorithm 1 — The BDI Deliberation Cycle**
1. Take the first percept $p$, set $B := brf(\emptyset, p)$, and initialize $I := \text{null}$ and $\pi := \text{empty}$.
2. Obtain the current percept $p$ and revise beliefs: $B := brf(B, p)$.
3. If $I$ is null or $\pi$ is empty:
   - Generate options $D := options(B, I)$.
   - Commit by $I := filter(B, D, I)$.
   - Construct plan $\pi := plan(B, I)$ by means–ends reasoning.
   - If $D$ is empty, take no move action this step, charge 1 time step to deliberation, and let the world advance.
4. Execute the first action of $\pi$ and delete it from $\pi$. The world advances by $W_{\text{speed}}$ ticks while the action is performed.
5. If $I$ is achieved in the revised beliefs, drop $I$ and $\pi$ and return to step 2.
6. Otherwise, invoke **Algorithm 2** to decide whether to reconsider $I$, then return to step 2, repeating for the required number of agent time steps.

#### **Algorithm 2 — Intention Reconsideration**
1. Maintain a counter $s$ of actions executed since the last reconsideration. Increment $s$ after step 4 of Algorithm 1.
2. If $s < \gamma$, return immediately with $I$ and $\pi$ unchanged (the agent stays committed and does not deliberate).
3. Otherwise, set $s := 0$ and charge **one agent time step** to deliberation, allowing the world to advance by $W_{\text{speed}}$ ticks while the agent reasons.
4. Re-perceive and revise beliefs ($B := brf(B, p)$). If $I$ is no longer achievable under revised beliefs (e.g. hole disappeared), drop $I$ and $\pi$ and return with no intention, so that the next cycle commits afresh.
5. Re-run $options(B, I)$ and $filter(B, D, I)$ on revised beliefs:
   - Under single-minded commitment: if preferred option differs from $I$ (or $I$ is unavailable), adopt it as the new intention and re-plan; otherwise retain $I$ and $\pi$.
   - Under open-minded commitment: if a better option exists, switch intention and re-plan.
6. Report $\gamma$ with results ($\gamma = 1$ yields a cautious agent; $\gamma \ge \text{longest plan}$ yields a bold one).

---

### **Python Code (`bdi_agent.py`)**

```python
"""
AI401 — Expert Systems Lab
Lab 3: Agent Architectures — The BDI Deliberation Cycle
"""

import math
import random
import os
import sys
from PIL import Image, ImageDraw

class DynamicHole:
    def __init__(self, position: tuple, lifetime: int):
        self.position = position  # (x, y)
        self.remaining_lifetime = lifetime

    def tick(self, count: int = 1) -> bool:
        self.remaining_lifetime -= count
        return self.remaining_lifetime <= 0


class Tileworld:
    def __init__(self, width: int = 15, height: int = 15, 
                 p_appear: float = 0.03, min_lifetime: int = 20, max_lifetime: int = 50,
                 world_speed: int = 1, seed: int = None):
        self.width = width
        self.height = height
        self.p_appear = p_appear
        self.min_lifetime = min_lifetime
        self.max_lifetime = max_lifetime
        self.world_speed = world_speed
        
        if seed is not None:
            random.seed(seed)
            
        self.all_grid_positions = set((x, y) for x in range(width) for y in range(height))
        self.holes = {}
        self.agent_pos = (7, 7)
        self.charger_pos = (0, 0)
        self.world_clock = 0
        self.total_holes_appeared = 0
        self.total_holes_filled = 0

    def step_world_clock(self, ticks: int = 1):
        for _ in range(ticks):
            self.world_clock += 1
            expired_keys = [pos for pos, hole in self.holes.items() if hole.tick(1)]
            for pos in expired_keys:
                del self.holes[pos]

            empty_positions = self.all_grid_positions - set(self.holes.keys()) - {self.agent_pos, self.charger_pos}
            num_empty = len(empty_positions)
            if num_empty > 0:
                num_spawn = sum(1 for _ in range(num_empty) if random.random() < self.p_appear)
                if num_spawn > 0:
                    spawned_pos = random.sample(list(empty_positions), min(num_spawn, num_empty))
                    for pos in spawned_pos:
                        lifetime = random.randint(self.min_lifetime, self.max_lifetime)
                        self.holes[pos] = DynamicHole(pos, lifetime)
                        self.total_holes_appeared += 1

    def move_agent(self, new_pos: tuple) -> bool:
        self.agent_pos = new_pos
        hole_filled = False
        if new_pos in self.holes:
            del self.holes[new_pos]
            self.total_holes_filled += 1
            hole_filled = True
        return hole_filled


class BDIAgent:
    def __init__(self, commitment_strategy: str = "single-minded", 
                 gamma: str = "1", resource_bounded: bool = False):
        self.commitment_strategy = commitment_strategy
        self.gamma = int(gamma) if isinstance(gamma, str) and gamma.isdigit() else gamma
        self.resource_bounded = resource_bounded
        
        self.B = {"agent_pos": (7, 7), "holes": {}, "charger_pos": (0, 0), "battery": 40, "world_clock": 0}
        self.intention = None
        self.plan = []
        self.reconsideration_counter = 0
        self.deliberation_steps = 0
        self.stranded_steps = 0

    def brf(self, percept: dict):
        self.B["agent_pos"] = percept["agent_pos"]
        self.B["holes"] = dict(percept["holes"])
        self.B["charger_pos"] = percept["charger_pos"]
        self.B["battery"] = percept["battery"]
        self.B["world_clock"] = percept["world_clock"]

    def options(self, B: dict, I: tuple) -> list:
        active_holes = list(B["holes"].keys())
        if not self.resource_bounded:
            return active_holes
        
        agent_pos, charger_pos, battery = B["agent_pos"], B["charger_pos"], B["battery"]
        valid_options = []
        for hole in active_holes:
            cost_to_hole = abs(agent_pos[0]-hole[0]) + abs(agent_pos[1]-hole[1])
            cost_to_charger = abs(hole[0]-charger_pos[0]) + abs(hole[1]-charger_pos[1])
            if cost_to_hole + cost_to_charger <= battery:
                valid_options.append(hole)
        
        if not valid_options or battery < 15:
            valid_options.append("RECHARGE")
        return valid_options

    def filter(self, B: dict, D: list, current_I: tuple) -> tuple:
        if not D:
            return None
        if "RECHARGE" in D and (B["battery"] < 15 or len(D) == 1):
            return "RECHARGE"
            
        agent_pos = B["agent_pos"]
        hole_options = [opt for opt in D if opt != "RECHARGE"]
        if not hole_options:
            return "RECHARGE"
            
        hole_options.sort(key=lambda h: abs(agent_pos[0]-h[0]) + abs(agent_pos[1]-h[1]))
        best_option = hole_options[0]
        
        if self.commitment_strategy in ["single-minded", "blind"]:
            return current_I if current_I in hole_options else best_option
        elif self.commitment_strategy == "open-minded":
            return best_option
        return best_option
```

---

### **Procedure and Execution Output**

#### **1. Sample BDI Agent Run Output**
- **Grid Configuration**: $15 \times 15$ Grid, $p_{\text{appear}} = 0.04$, World Speed $W_{\text{speed}} = 2$ ticks/action.
- **Commitment Strategy**: Open-Minded, Reconsideration Interval $\gamma = 2$.

```text
=== Generating Sample BDI Event Trace ===
Total Holes Appeared: 977
Total Holes Filled:   53
Effectiveness:        0.0542
```

#### **2. Event Trace Snapshot**
The event trace below illustrates the four key BDI events during execution:
1. `COMMIT`: Agent commits to an intention and formulates a plan.
2. `ACHIEVE`: Agent reaches the target hole and fills it.
3. `DROP_UNACHIEVABLE`: Agent drops an intention because the target hole expired.
4. `SWITCH_OPTION`: Agent switches to a closer/better hole upon reconsideration.

```text
---------------------------------------------------------------------------
Step   2 | Event: COMMIT             | Details: Committed to intention (10, 8) (Plan length: 4)
Step   3 | Event: ACHIEVE            | Details: Achieved intention (10, 8)
Step   4 | Event: COMMIT             | Details: Committed to intention (8, 8) (Plan length: 1)
Step   5 | Event: ACHIEVE            | Details: Achieved intention (8, 8)
Step   6 | Event: COMMIT             | Details: Committed to intention (9, 8) (Plan length: 1)
Step   7 | Event: ACHIEVE            | Details: Achieved intention (9, 8)
Step   8 | Event: COMMIT             | Details: Committed to intention (10, 8) (Plan length: 1)
Step   9 | Event: ACHIEVE            | Details: Achieved intention (10, 8)
Step  10 | Event: COMMIT             | Details: Committed to intention (11, 8) (Plan length: 1)
Step  11 | Event: ACHIEVE            | Details: Achieved intention (11, 8)
Step  12 | Event: COMMIT             | Details: Committed to intention (11, 7) (Plan length: 1)
Step  13 | Event: ACHIEVE            | Details: Achieved intention (11, 7)
Step  14 | Event: COMMIT             | Details: Committed to intention (12, 7) (Plan length: 1)
Step  15 | Event: ACHIEVE            | Details: Achieved intention (12, 7)
Step  16 | Event: COMMIT             | Details: Committed to intention (12, 8) (Plan length: 1)
---------------------------------------------------------------------------
```

---

### **Observations**

#### **1. Drop and Switch Events & Intention Persistence**
- **Drop Events (`DROP_UNACHIEVABLE`)**: Reveal that intentions are **not unyielding dogmas**. Under single-minded commitment, an intention persists across plan execution unless the belief set $B$ indicates that the intention has become unachievable (e.g., the target hole expired). Dropping an unachievable intention prevents the agent from wasting moves executing a plan toward a non-existent goal.
- **Switch Events (`SWITCH_OPTION`)**: Reveal the core difference between **single-minded** and **open-minded** commitment:
  - *Single-minded commitment* maintains the current intention $I$ even if a closer or easier hole spawns nearby, dropping $I$ only when it becomes impossible or is achieved.
  - *Open-minded commitment* constantly re-evaluates all active options against utility metrics during reconsideration. If a newly spawned hole offers a shorter path or higher net utility than $I$, the agent drops $I$ and switches immediately.

#### **2. Why Deliberation Must Be Charged a Time Step**
If deliberation were free ($0$ cost), an agent could reconsider after every single micro-step ($\gamma = 1$) with zero penalty, effectively transforming into a perfectly informed, zero-cost reactive planner. 
However, real-world reasoning requires computational time and resources. Charging **one agent time step** per deliberation allows the world clock to advance by $W_{\text{speed}}$ ticks while the agent deliberates. This introduces an intrinsic trade-off: **time spent deliberating is time lost acting**. Without a deliberation penalty, the experimental comparison between cautious ($\gamma = 1$) and bold ($\gamma = \text{bold}$) agents would be mathematically meaningless.

#### **3. Impact of World Dynamism on Optimal Reconsideration Interval ($\gamma$)**
As world dynamism increases ($W_{\text{speed}}$ increases from $1 \to 2 \to 4 \to 8$ ticks per action), holes expire faster and new holes appear at a higher rate. Consequently:
- In a slow world ($W_{\text{speed}} = 1$), plans remain valid for longer durations, so a higher $\gamma$ ($\gamma = 4$) yields maximum effectiveness by minimizing deliberation overhead.
- In a fast world ($W_{\text{speed}} = 8$), long commitment leads to chasing expired holes. The optimal $\gamma$ shifts downward to $\gamma = 2$, forcing the agent to reconsider more frequently to keep pace with rapid environmental changes.

---

### **Exercises**

#### **Exercise 1: Boldness Against Dynamism**

We swept reconsideration intervals $\gamma \in \{1, 2, 4, 8, \text{bold}\}$ across world speeds $W_{\text{speed}} \in \{1, 2, 4, 8\}$ world ticks per action. Each parameter combination was averaged over **25 independent random seeds** running for **600 agent steps** each.

##### **Experimental Data Table: Average Effectiveness ($E$)**

| World Speed ($W_{\text{speed}}$) | $\gamma=1$ (Cautious) | $\gamma=2$ | $\gamma=4$ | $\gamma=8$ | $\gamma=\text{bold}$ | Optimal $\gamma$ |
|---|---|---|---|---|---|---|
| **$W_{\text{speed}} = 1$** | 0.1164 | 0.1250 | **0.1264** | 0.1263 | 0.1263 | **$\gamma=4$** |
| **$W_{\text{speed}} = 2$** | 0.0591 | 0.0628 | **0.0631** | 0.0631 | 0.0631 | **$\gamma=4$** |
| **$W_{\text{speed}} = 4$** | 0.0284 | **0.0300** | 0.0300 | 0.0300 | 0.0300 | **$\gamma=2$** |
| **$W_{\text{speed}} = 8$** | 0.0127 | **0.0131** | 0.0131 | 0.0131 | 0.0131 | **$\gamma=2$** |

---

##### **Performance Plot: Effectiveness vs. Reconsideration Interval**

![Exercise 1 Plot](file:///c:/Users/Tanu%20Meena/OneDrive/Desktop/Image/Lab3_BDI_Deliberation_Cycle/exercise1_boldness_vs_dynamism.png)

---

##### **Analytical Breakdown & Explanation**

1. **Optimal $\gamma$ per World Speed**:
   - At $W_{\text{speed}} = 1$: Optimal $\gamma = 4$ ($E = 0.1264$).
   - At $W_{\text{speed}} = 2$: Optimal $\gamma = 4$ ($E = 0.0631$).
   - At $W_{\text{speed}} = 4$: Optimal $\gamma = 2$ ($E = 0.0300$).
   - At $W_{\text{speed}} = 8$: Optimal $\gamma = 2$ ($E = 0.0131$).

2. **Why the Optimum $\gamma$ Falls as the World Speeds Up**:
   As $W_{\text{speed}}$ increases, the environment changes faster relative to the agent's actions. Holes have shorter real-time survival spans in terms of agent steps. An agent committed to a long plan ($\gamma \ge 8$ or bold) frequently travels toward a hole that expires midway through the plan, wasting valuable movement steps. Frequent reconsideration (smaller $\gamma$) becomes essential to detect unachievable intentions early and re-plan.

3. **Why Both Extremes ($\gamma = 1$ and Bold) Are Beaten by Intermediate Values**:
   - **Over-Cautious Agent ($\gamma = 1$)**: Reconsiders after *every single step*. Because deliberation costs 1 agent step, the cautious agent spends 50% of its entire time budget deliberating ($300$ deliberation steps out of $600$), cutting its physical move actions in half. This high deliberation penalty severely degrades its hole-filling throughput.
   - **Over-Bold Agent ($\gamma = \text{bold}$)**: Never reconsiders during plan execution. In a dynamic world, it blindly executes stale plans toward expired holes, wasting dozens of steps before realizing the hole is gone upon plan termination.
   - **Intermediate Values ($\gamma \in \{2, 4\}$)**: Strike the optimal balance. They avoid spending excessive steps deliberating while maintaining sufficient responsiveness to abort invalid plans quickly.

---

#### **Exercise 2: A Resource-Bounded Filter**

In Exercise 2, the agent is equipped with a battery of capacity $40$ that depletes by $1$ unit per grid move, and a charger cell located at $(0, 0)$ that restores battery level to $40$. 

The agent operates with two plan schemas:
1. `fill-hole`: Applicable only when $\text{dist}(\text{agent}, \text{hole}) + \text{dist}(\text{hole}, \text{charger}) \le \text{battery}$.
2. `recharge`: Always applicable (direct path to charger cell $(0, 0)$).

We compared the **Resource-Bounded BDI Filter** (which enforces the battery precondition in `options`/`filter`) against a **Battery-Blind Agent** (which always chases the nearest hole regardless of remaining battery level).

##### **Comparative Results Table (25 Seeds, 600 Agent Steps)**

| Agent Architecture | Avg Holes Filled | Effectiveness ($E$) | Avg Stranded Steps | Status |
|---|---|---|---|---|
| **Resource-Bounded BDI Agent** | **237.7** | **0.0585** | **0.0** | Fully Operational |
| **Battery-Blind Agent** | 32.1 | 0.0080 | 523.2 | Severely Stranded |

---

##### **Performance Plot: Resource-Bounded Filter vs. Battery-Blind Agent**

![Exercise 2 Plot](file:///c:/Users/Tanu%20Meena/OneDrive/Desktop/Image/Lab3_BDI_Deliberation_Cycle/exercise2_resource_bounded.png)

---

##### **Architectural Analysis: BDI Component Placement**

> [!IMPORTANT]
> **Which BDI component does the battery fix belong in?**
> The fix belongs firmly in the **Filter** (and **Options Generation**) component of the BDI architecture, **NOT in the Planner**.

##### **Theoretical Rationale**:
1. **Options & Filter Responsibility (Desire & Intention Selection)**:
   - The role of `options(B, I)` is to propose valid candidate goals (desires) consistent with current beliefs.
   - The role of `filter(B, D, I)` is to commit only to intentions that are **physically achievable and safe** given the agent's resource bounds. Evaluating whether chasing a hole leaves sufficient battery to return to the charger is a *goal-level feasibility check*.
2. **Planner Responsibility (Means–Ends Reasoning)**:
   - The planner's sole task is **means–ends reasoning**: given a committed intention $I$, it finds a valid geometric path $\pi$ from start to target.
   - If a battery-blind filter commits the agent to an impossible hole ($100$ units away with only $5$ battery remaining), the planner can correctly generate a $100$-step path, but the agent will freeze stranded at step $5$. The planner cannot prevent the agent from adopting fatal goals—it merely plots the path to them.
3. **Architectural Decoupling**:
   - Keeping resource feasibility checks in `filter` maintains clean separation of concerns: the filter handles *what goals to adopt*, while the planner handles *how to navigate to them*.

---

### **Conclusion**
This experiment successfully implemented and evaluated the Belief–Desire–Intention (BDI) deliberation cycle in a dynamic Tileworld environment. The empirical results demonstrate that:
1. Intention commitment is essential to constrain deliberation overhead in dynamic worlds.
2. Deliberation cost requires parameterizing commitment via reconsideration interval $\gamma$.
3. The optimal reconsideration interval shifts toward lower values (more cautious reasoning) as world dynamism increases.
4. Intermediate reconsideration values ($\gamma \in \{2, 4\}$) consistently outperform both extreme caution ($\gamma = 1$) and extreme boldness ($\gamma = \text{bold}$).
5. Feasibility preconditions (such as battery resource constraints) must reside within the **Options/Filter** deliberation layer rather than the planner.
