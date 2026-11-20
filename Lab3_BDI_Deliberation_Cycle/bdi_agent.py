"""
AI401 — Expert Systems Lab
Lab 3: Agent Architectures — The BDI Deliberation Cycle

This script implements:
1. Simplified Tileworld environment (15x15 grid, dynamic hole spawning & expiration).
2. Belief-Desire-Intention (BDI) Agent Architecture (BRF, Options, Filter, Planner).
3. Algorithm 1 (BDI Deliberation Cycle) and Algorithm 2 (Intention Reconsideration under Single-Minded & Open-Minded Commitment).
4. Event tracing for Commit, Achieve, Drop (Unachievable), and Switch (Better Option) events.
5. Exercise 1: Parameter sweep over reconsideration interval gamma in {1, 2, 4, 8, bold} and world speed in {1, 2, 4, 8}.
6. Exercise 2: Resource-bounded filter with battery constraint vs battery-blind agent.
7. Pure PIL High-Resolution Plot Rendering for publication-quality charts.
"""

import math
import random
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# 1. Pure PIL Plot Generator Functions
# ==========================================

def render_line_plot_pil(filename: str, results_table: dict, gammas: list, world_speeds: list):
    width, height = 1000, 600
    img = Image.new('RGB', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(img)
    
    margin_left = 100
    margin_right = 220
    margin_top = 80
    margin_bottom = 80
    
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    
    min_y, max_y = 0.0, 0.70
    
    draw.text((width // 2 - 250, 25), "Exercise 1: BDI Agent Effectiveness vs γ & World Dynamism", fill='#111111')
    
    num_y_ticks = 8
    for i in range(num_y_ticks):
        val = min_y + (max_y - min_y) * i / (num_y_ticks - 1)
        y_pixel = margin_top + plot_h - int((val - min_y) / (max_y - min_y) * plot_h)
        draw.line([(margin_left, y_pixel), (margin_left + plot_w, y_pixel)], fill='#e0e0e0', width=1)
        draw.text((margin_left - 55, y_pixel - 8), f"{val:.2f}", fill='#333333')
        
    num_x = len(gammas)
    x_pixels = []
    gamma_labels = ['γ=1', 'γ=2', 'γ=4', 'γ=8', 'γ=bold']
    for i in range(num_x):
        x_pixel = margin_left + int(i / (num_x - 1) * plot_w)
        x_pixels.append(x_pixel)
        draw.line([(x_pixel, margin_top), (x_pixel, margin_top + plot_h)], fill='#f0f0f0', width=1)
        draw.text((x_pixel - 15, margin_top + plot_h + 15), gamma_labels[i], fill='#333333')

    draw.line([(margin_left, margin_top), (margin_left, margin_top + plot_h)], fill='#222222', width=2)
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top + plot_h)], fill='#222222', width=2)

    draw.text((margin_left + plot_w // 2 - 80, margin_top + plot_h + 45), "Reconsideration Interval γ", fill='#111111')
    draw.text((15, margin_top + plot_h // 2), "Effectiveness E", fill='#111111')

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    leg_x = margin_left + plot_w + 20
    leg_y = margin_top + 20
    draw.rectangle([(leg_x, leg_y), (leg_x + 180, leg_y + 140)], outline='#cccccc', fill='#ffffff', width=1)
    draw.text((leg_x + 10, leg_y + 10), "World Speed", fill='#111111')

    for idx, w in enumerate(world_speeds):
        color = colors[idx]
        points = []
        for i, g in enumerate(gammas):
            eff = results_table[w][g]["effectiveness"]
            y_pixel = margin_top + plot_h - int((eff - min_y) / (max_y - min_y) * plot_h)
            points.append((x_pixels[i], y_pixel))
            
        for p1, p2 in zip(points[:-1], points[1:]):
            draw.line([p1, p2], fill=color, width=3)
            
        for px, py in points:
            r = 5
            draw.ellipse([(px - r, py - r), (px + r, py + r)], fill=color, outline='#ffffff', width=1)
            
        ly = leg_y + 40 + idx * 25
        draw.line([(leg_x + 15, ly + 6), (leg_x + 35, ly + 6)], fill=color, width=3)
        draw.ellipse([(leg_x + 22, ly + 3), (leg_x + 28, ly + 9)], fill=color)
        draw.text((leg_x + 45, ly), f"W_speed = {w}", fill='#222222')

    img.save(filename)
    print(f"PIL Line Plot saved to: {filename}", flush=True)


def render_bar_chart_pil(filename: str, smart_filled: float, smart_stranded: float, blind_filled: float, blind_stranded: float):
    width, height = 800, 500
    img = Image.new('RGB', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(img)

    margin_left = 80
    margin_right = 50
    margin_top = 80
    margin_bottom = 80

    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    draw.text((width // 2 - 220, 25), "Exercise 2: Resource-Bounded Filter vs Battery-Blind Agent", fill='#111111')

    max_val = 140.0

    for i in range(8):
        val = max_val * i / 7.0
        y_pixel = margin_top + plot_h - int((val / max_val) * plot_h)
        draw.line([(margin_left, y_pixel), (margin_left + plot_w, y_pixel)], fill='#e0e0e0', width=1)
        draw.text((margin_left - 45, y_pixel - 8), f"{int(val)}", fill='#333333')

    draw.line([(margin_left, margin_top), (margin_left, margin_top + plot_h)], fill='#222222', width=2)
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top + plot_h)], fill='#222222', width=2)

    group_centers = [margin_left + int(plot_w * 0.28), margin_left + int(plot_w * 0.72)]
    cat_names = ["Resource-Bounded BDI", "Battery-Blind Agent"]

    bar_w = 50
    data = [(smart_filled, smart_stranded), (blind_filled, blind_stranded)]

    for idx, center in enumerate(group_centers):
        filled, stranded = data[idx]

        h_filled = int((filled / max_val) * plot_h)
        x1 = center - bar_w - 5
        y1 = margin_top + plot_h - h_filled
        draw.rectangle([(x1, y1), (x1 + bar_w, margin_top + plot_h)], fill='#2ca02c', outline='#1b661b')
        draw.text((x1 + 10, y1 - 20), f"{filled:.1f}", fill='#1b661b')

        h_stranded = int((stranded / max_val) * plot_h)
        x2 = center + 5
        y2 = margin_top + plot_h - h_stranded
        draw.rectangle([(x2, y2), (x2 + bar_w, margin_top + plot_h)], fill='#d62728', outline='#9e1b1c')
        draw.text((x2 + 10, y2 - 20), f"{stranded:.1f}", fill='#9e1b1c')

        draw.text((center - 70, margin_top + plot_h + 15), cat_names[idx], fill='#111111')

    leg_x = width - 230
    leg_y = margin_top + 10
    draw.rectangle([(leg_x, leg_y), (leg_x + 180, leg_y + 70)], outline='#cccccc', fill='#ffffff')
    draw.rectangle([(leg_x + 15, leg_y + 15), (leg_x + 35, leg_y + 30)], fill='#2ca02c')
    draw.text((leg_x + 45, leg_y + 15), "Holes Filled", fill='#111111')
    draw.rectangle([(leg_x + 15, leg_y + 40), (leg_x + 35, leg_y + 55)], fill='#d62728')
    draw.text((leg_x + 45, leg_y + 40), "Stranded Steps", fill='#111111')

    img.save(filename)
    print(f"PIL Bar Chart saved to: {filename}", flush=True)


# ==========================================
# 2. Tileworld Environment
# ==========================================

class DynamicHole:
    def __init__(self, position: tuple, lifetime: int):
        self.position = position
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
        self.holes = {}  # pos -> DynamicHole
        self.agent_pos = (7, 7)
        self.charger_pos = (0, 0)
        self.world_clock = 0
        self.total_holes_appeared = 0
        self.total_holes_filled = 0

    def step_world_clock(self, ticks: int = 1):
        """Advances world by `ticks` world ticks."""
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

    def get_percept(self, battery: int = 40) -> dict:
        return {
            "agent_pos": self.agent_pos,
            "holes": {pos: h.remaining_lifetime for pos, h in self.holes.items()},
            "charger_pos": self.charger_pos,
            "battery": battery,
            "world_clock": self.world_clock
        }

    def move_agent(self, new_pos: tuple) -> bool:
        self.agent_pos = new_pos
        hole_filled = False
        if new_pos in self.holes:
            del self.holes[new_pos]
            self.total_holes_filled += 1
            hole_filled = True
        return hole_filled

# ==========================================
# 3. Helper Utilities
# ==========================================

def manhattan_distance(pos1: tuple, pos2: tuple) -> int:
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def generate_plan(start: tuple, target: tuple) -> list:
    if start == target:
        return []
    path = []
    curr_x, curr_y = start
    target_x, target_y = target
    
    while curr_x != target_x:
        curr_x += 1 if target_x > curr_x else -1
        path.append((curr_x, curr_y))
    while curr_y != target_y:
        curr_y += 1 if target_y > curr_y else -1
        path.append((curr_x, curr_y))
    return path

# ==========================================
# 4. BDI Agent Architecture
# ==========================================

class BDIAgent:
    def __init__(self, commitment_strategy: str = "single-minded", 
                 gamma: str = "1", resource_bounded: bool = False):
        self.commitment_strategy = commitment_strategy
        if isinstance(gamma, str) and gamma.isdigit():
            self.gamma = int(gamma)
        else:
            self.gamma = gamma
            
        self.resource_bounded = resource_bounded
        
        self.B = {
            "agent_pos": (7, 7),
            "holes": {},
            "charger_pos": (0, 0),
            "battery": 40,
            "world_clock": 0
        }
        self.battery_max = 40
        self.intention = None
        self.plan = []
        self.reconsideration_counter = 0
        self.deliberation_steps = 0
        self.stranded_steps = 0
        self.event_trace = []

    def log_event(self, step: int, event_type: str, details: str):
        self.event_trace.append({
            "step": step,
            "event": event_type,
            "details": details
        })

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
        
        agent_pos = B["agent_pos"]
        charger_pos = B["charger_pos"]
        battery = B["battery"]
        
        valid_options = []
        for hole in active_holes:
            cost_to_hole = manhattan_distance(agent_pos, hole)
            cost_to_charger = manhattan_distance(hole, charger_pos)
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
            
        hole_options.sort(key=lambda h: manhattan_distance(agent_pos, h))
        best_option = hole_options[0]
        
        if self.commitment_strategy == "single-minded":
            if current_I in hole_options:
                return current_I
            return best_option
            
        elif self.commitment_strategy == "open-minded":
            return best_option
            
        elif self.commitment_strategy == "blind":
            if current_I in hole_options:
                return current_I
            return best_option
            
        return best_option

    def plan_means_ends(self, B: dict, I: tuple) -> list:
        if I is None:
            return []
        agent_pos = B["agent_pos"]
        target = B["charger_pos"] if I == "RECHARGE" else I
        return generate_plan(agent_pos, target)

# ==========================================
# 5. Simulation Engine (Algorithm 1 & 2)
# ==========================================

def run_bdi_simulation(agent: BDIAgent, env: Tileworld, max_agent_steps: int = 600, trace_events: bool = False):
    agent_step = 0
    
    percept = env.get_percept(agent.B["battery"])
    agent.brf(percept)
    agent.intention = None
    agent.plan = []
    
    while agent_step < max_agent_steps:
        percept = env.get_percept(agent.B["battery"])
        agent.brf(percept)
        
        if agent.resource_bounded and agent.B["battery"] <= 0 and agent.B["agent_pos"] != env.charger_pos:
            agent.stranded_steps += 1
            agent_step += 1
            env.step_world_clock(env.world_speed)
            continue

        if agent.B["agent_pos"] == env.charger_pos and agent.B["battery"] < agent.battery_max:
            agent.B["battery"] = agent.battery_max
            if agent.intention == "RECHARGE":
                agent.intention = None
                agent.plan = []
        
        # Step 3: Initial Deliberation (charge 1 step)
        if agent.intention is None or not agent.plan:
            agent.deliberation_steps += 1
            agent_step += 1
            env.step_world_clock(env.world_speed)
            
            D = agent.options(agent.B, agent.intention)
            new_I = agent.filter(agent.B, D, agent.intention)
            
            if new_I is not None:
                agent.intention = new_I
                agent.plan = agent.plan_means_ends(agent.B, agent.intention)
                agent.reconsideration_counter = 0
                if trace_events:
                    agent.log_event(agent_step, "COMMIT", f"Committed to intention {agent.intention} (Plan length: {len(agent.plan)})")
            continue

        # Step 4: Execute move action
        if agent.plan:
            next_pos = agent.plan.pop(0)
            agent.reconsideration_counter += 1
            agent_step += 1
            
            if agent.resource_bounded:
                agent.B["battery"] -= 1
                
            hole_filled = env.move_agent(next_pos)
            env.step_world_clock(env.world_speed)
            
            percept = env.get_percept(agent.B["battery"])
            agent.brf(percept)
            
            # Step 5: Check Achievement
            achieved = False
            if agent.intention == "RECHARGE" and agent.B["agent_pos"] == env.charger_pos:
                achieved = True
            elif isinstance(agent.intention, tuple) and (hole_filled or agent.B["agent_pos"] == agent.intention):
                achieved = True
                
            if achieved:
                if trace_events:
                    agent.log_event(agent_step, "ACHIEVE", f"Achieved intention {agent.intention}")
                agent.intention = None
                agent.plan = []
                continue

            # Step 6: Algorithm 2 — Reconsideration
            should_reconsider = False
            if agent.gamma == "bold":
                should_reconsider = False
            elif isinstance(agent.gamma, int):
                if agent.reconsideration_counter >= agent.gamma:
                    should_reconsider = True

            if should_reconsider and agent_step < max_agent_steps:
                agent.reconsideration_counter = 0
                agent.deliberation_steps += 1
                agent_step += 1
                env.step_world_clock(env.world_speed)
                
                percept = env.get_percept(agent.B["battery"])
                agent.brf(percept)
                
                unachievable = False
                if isinstance(agent.intention, tuple) and agent.intention not in agent.B["holes"]:
                    unachievable = True
                    
                if unachievable:
                    if trace_events:
                        agent.log_event(agent_step, "DROP_UNACHIEVABLE", f"Dropped unachievable intention {agent.intention}")
                    agent.intention = None
                    agent.plan = []
                    continue

                D = agent.options(agent.B, agent.intention)
                preferred_option = agent.filter(agent.B, D, agent.intention)
                
                if preferred_option != agent.intention:
                    if trace_events:
                        agent.log_event(agent_step, "SWITCH_OPTION", f"Switched intention from {agent.intention} to preferred {preferred_option}")
                    agent.intention = preferred_option
                    agent.plan = agent.plan_means_ends(agent.B, agent.intention)

    effectiveness = env.total_holes_filled / env.total_holes_appeared if env.total_holes_appeared > 0 else 0.0
    return {
        "holes_filled": env.total_holes_filled,
        "holes_appeared": env.total_holes_appeared,
        "effectiveness": effectiveness,
        "deliberation_steps": agent.deliberation_steps,
        "stranded_steps": agent.stranded_steps,
        "event_trace": agent.event_trace
    }

# ==========================================
# 6. Event Trace Generator
# ==========================================

def generate_sample_event_trace():
    print("=== Generating Sample BDI Event Trace ===", flush=True)
    env = Tileworld(width=15, height=15, p_appear=0.04, world_speed=2, seed=42)
    agent = BDIAgent(commitment_strategy="open-minded", gamma=2, resource_bounded=False)
    
    results = run_bdi_simulation(agent, env, max_agent_steps=120, trace_events=True)
    
    print(f"Total Holes Appeared: {results['holes_appeared']}", flush=True)
    print(f"Total Holes Filled:   {results['holes_filled']}", flush=True)
    print(f"Effectiveness:        {results['effectiveness']:.4f}\n", flush=True)
    print("Event Trace Snapshot (First 15 Events):", flush=True)
    print("-" * 75, flush=True)
    for event in results["event_trace"][:15]:
        print(f"Step {event['step']:3d} | Event: {event['event']:18s} | Details: {event['details']}", flush=True)
    print("-" * 75, flush=True)
    return results

# ==========================================
# 7. Exercise 1: Sweeping Gamma vs Dynamic World Speed
# ==========================================

def run_exercise_1():
    print("\n=======================================================", flush=True)
    print("Running Exercise 1: Boldness against Dynamism", flush=True)
    print("=======================================================", flush=True)
    
    gammas = [1, 2, 4, 8, "bold"]
    world_speeds = [1, 2, 4, 8]
    num_seeds = 25
    steps_per_run = 600

    results_table = {w: {} for w in world_speeds}
    
    for w in world_speeds:
        print(f"\n--- Simulating World Speed W_speed = {w} ticks/action ---", flush=True)
        for g in gammas:
            eff_list = []
            filled_list = []
            appeared_list = []
            
            for seed in range(num_seeds):
                env = Tileworld(width=15, height=15, p_appear=0.03, world_speed=w, seed=1000 + seed)
                agent = BDIAgent(commitment_strategy="single-minded", gamma=g, resource_bounded=False)
                res = run_bdi_simulation(agent, env, max_agent_steps=steps_per_run, trace_events=False)
                eff_list.append(res["effectiveness"])
                filled_list.append(res["holes_filled"])
                appeared_list.append(res["holes_appeared"])
                
            avg_eff = sum(eff_list) / len(eff_list)
            avg_filled = sum(filled_list) / len(filled_list)
            avg_appeared = sum(appeared_list) / len(appeared_list)
            
            results_table[w][g] = {
                "effectiveness": avg_eff,
                "holes_filled": avg_filled,
                "holes_appeared": avg_appeared
            }
            g_str = f"gamma={g}" if isinstance(g, int) else "gamma=bold"
            print(f"  {g_str:12s} -> Avg Effectiveness: {avg_eff:.4f} (Filled: {avg_filled:.1f} / Appeared: {avg_appeared:.1f})", flush=True)

    print("\nSummary Table: Average Effectiveness E (gamma vs W_speed)", flush=True)
    header = "| World Speed (W_speed) | gamma=1 (Cautious) | gamma=2 | gamma=4 | gamma=8 | gamma=bold | Optimal gamma |"
    print(header, flush=True)
    print("|" + "---|"*7, flush=True)
    
    optimal_gammas = {}
    for w in world_speeds:
        row = f"| W_speed = {w} |"
        best_g = None
        best_eff = -1
        for g in gammas:
            eff = results_table[w][g]["effectiveness"]
            row += f" {eff:.4f} |"
            if eff > best_eff:
                best_eff = eff
                best_g = g
        optimal_gammas[w] = best_g
        g_best_str = f"gamma={best_g}" if isinstance(best_g, int) else "gamma=bold"
        row += f" **{g_best_str}** |"
        print(row, flush=True)

    output_dir = os.path.dirname(os.path.abspath(__file__))
    plot_path = os.path.join(output_dir, "exercise1_boldness_vs_dynamism.png")
    render_line_plot_pil(plot_path, results_table, gammas, world_speeds)
    
    return results_table, optimal_gammas

# ==========================================
# 8. Exercise 2: Resource-Bounded Filter
# ==========================================

def run_exercise_2():
    print("\n=======================================================", flush=True)
    print("Running Exercise 2: Resource-Bounded Filter vs Battery-Blind Agent", flush=True)
    print("=======================================================", flush=True)
    
    num_seeds = 25
    steps_per_run = 600
    world_speed = 2
    
    smart_filled = []
    smart_appeared = []
    smart_stranded = []
    
    blind_filled = []
    blind_appeared = []
    blind_stranded = []
    
    for seed in range(num_seeds):
        env_smart = Tileworld(width=15, height=15, p_appear=0.03, world_speed=world_speed, seed=2000 + seed)
        agent_smart = BDIAgent(commitment_strategy="single-minded", gamma=2, resource_bounded=True)
        res_smart = run_bdi_simulation(agent_smart, env_smart, max_agent_steps=steps_per_run)
        smart_filled.append(res_smart["holes_filled"])
        smart_appeared.append(res_smart["holes_appeared"])
        smart_stranded.append(res_smart["stranded_steps"])
        
        env_blind = Tileworld(width=15, height=15, p_appear=0.03, world_speed=world_speed, seed=2000 + seed)
        agent_blind = BDIAgent(commitment_strategy="single-minded", gamma=2, resource_bounded=False)
        agent_blind.resource_bounded = True
        
        def blind_options(B, I):
            holes = list(B["holes"].keys())
            return holes if holes else ["RECHARGE"]
        agent_blind.options = blind_options
        
        res_blind = run_bdi_simulation(agent_blind, env_blind, max_agent_steps=steps_per_run)
        blind_filled.append(res_blind["holes_filled"])
        blind_appeared.append(res_blind["holes_appeared"])
        blind_stranded.append(res_blind["stranded_steps"])

    avg_smart_filled = sum(smart_filled) / num_seeds
    avg_smart_eff = avg_smart_filled / (sum(smart_appeared) / num_seeds)
    avg_smart_stranded = sum(smart_stranded) / num_seeds

    avg_blind_filled = sum(blind_filled) / num_seeds
    avg_blind_eff = avg_blind_filled / (sum(blind_appeared) / num_seeds)
    avg_blind_stranded = sum(blind_stranded) / num_seeds

    print("\nComparative Results for Exercise 2 (25 Seeds, 600 Steps):", flush=True)
    print("-" * 75, flush=True)
    print(f"1. Resource-Bounded BDI Agent  | Avg Holes Filled: {avg_smart_filled:5.1f} | Effectiveness: {avg_smart_eff:.4f} | Stranded Steps: {avg_smart_stranded:5.1f}", flush=True)
    print(f"2. Battery-Blind Agent         | Avg Holes Filled: {avg_blind_filled:5.1f} | Effectiveness: {avg_blind_eff:.4f} | Stranded Steps: {avg_blind_stranded:5.1f}", flush=True)
    print("-" * 75, flush=True)

    output_dir = os.path.dirname(os.path.abspath(__file__))
    plot_path = os.path.join(output_dir, "exercise2_resource_bounded.png")
    render_bar_chart_pil(plot_path, avg_smart_filled, avg_smart_stranded, avg_blind_filled, avg_blind_stranded)

    return {
        "smart": {"filled": avg_smart_filled, "eff": avg_smart_eff, "stranded": avg_smart_stranded},
        "blind": {"filled": avg_blind_filled, "eff": avg_blind_eff, "stranded": avg_blind_stranded}
    }

if __name__ == "__main__":
    generate_sample_event_trace()
    run_exercise_1()
    run_exercise_2()
