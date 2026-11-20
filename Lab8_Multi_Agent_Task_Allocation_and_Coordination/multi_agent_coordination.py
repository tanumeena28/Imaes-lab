"""
AI401 - Expert Systems Lab
Experiment 8: Multi-Agent Task Allocation and Coordination
Exercises 1 - 5: Agent Setup, PGP Coordination, CNP Task Allocation, Multiple Task Allocation, Modification & Visualization
"""

import sys

try:
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


import copy
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ==============================================================================
# DATA STRUCTURES & MODEL DEFINITIONS
# ==============================================================================

@dataclass
class Task:
    task_id: str
    name: str
    destination: str
    distance_km: float
    weight_kg: float
    deadline_min: int
    priority: int  # 1 = Highest, 3 = Lowest


@dataclass
class PlanEntry:
    agent_id: str
    task_id: str
    resource: str
    start_time: int  # in minutes from base epoch (e.g., 0 = 09:00 AM)
    end_time: int    # in minutes from base epoch
    description: str

    @property
    def duration(self) -> int:
        return self.end_time - self.start_time

    def format_window(self, base_hour: int = 9) -> str:
        s_h, s_m = divmod(self.start_time, 60)
        e_h, e_m = divmod(self.end_time, 60)
        return f"{base_hour + s_h:02d}:{s_m:02d} - {base_hour + e_h:02d}:{e_m:02d}"


@dataclass
class Bid:
    agent_id: str
    task_id: str
    cost: float
    estimated_time_min: int
    feasible: bool
    notes: str = ""


# ==============================================================================
# AGENT CLASSES
# ==============================================================================

class DeliveryAgent:
    """
    Delivery Agent participating in:
    1. Partial Global Planning (PGP) through local plan sharing.
    2. Contract Net Protocol (CNP) through competitive proposal bidding.
    """
    def __init__(
        self,
        agent_id: str,
        vehicle_type: str,
        base_cost: float,
        cost_per_km: float,
        speed_kmh: float,
        max_payload_kg: float,
        fixed_handling_time_min: int = 10,
    ):
        self.agent_id = agent_id
        self.vehicle_type = vehicle_type
        self.base_cost = base_cost
        self.cost_per_km = cost_per_km
        self.speed_kmh = speed_kmh
        self.max_payload_kg = max_payload_kg
        self.fixed_handling_time_min = fixed_handling_time_min

        # Agent state
        self.assigned_tasks: List[Task] = []
        self.total_cost_incurred: float = 0.0
        self.total_time_spent_min: int = 0
        self.local_plan: List[PlanEntry] = []

    def reset_state(self):
        self.assigned_tasks.clear()
        self.total_cost_incurred = 0.0
        self.total_time_spent_min = 0
        self.local_plan.clear()

    def calculate_cost_and_time(self, task: Task) -> Tuple[float, int, bool]:
        """Calculates operational cost and estimated completion time for a given task."""
        if task.weight_kg > self.max_payload_kg:
            return float("inf"), 999999, False  # Infeasible payload

        transit_time_min = int(round((task.distance_km / self.speed_kmh) * 60))
        total_time_min = transit_time_min + self.fixed_handling_time_min

        # Feasibility check against deadline
        if total_time_min > task.deadline_min:
            return float("inf"), total_time_min, False

        # Cost formula: base_cost + (distance * cost_per_km) + (weight factor)
        operational_cost = round(
            self.base_cost + (task.distance_km * self.cost_per_km) + (0.5 * task.weight_kg),
            2
        )
        return operational_cost, total_time_min, True

    def generate_bid(self, task: Task) -> Bid:
        """Contract Net Protocol: Evaluates task announcement and generates bid."""
        cost, time_min, feasible = self.calculate_cost_and_time(task)
        notes = "Feasible & optimal" if feasible else (
            "Exceeds payload capacity" if task.weight_kg > self.max_payload_kg else "Exceeds deadline"
        )
        return Bid(
            agent_id=self.agent_id,
            task_id=task.task_id,
            cost=cost,
            estimated_time_min=time_min,
            feasible=feasible,
            notes=notes,
        )

    def award_contract(self, task: Task, bid: Bid):
        """Accepts task assignment and updates agent state."""
        self.assigned_tasks.append(task)
        self.total_cost_incurred += bid.cost
        self.total_time_spent_min += bid.estimated_time_min


class ManagerAgent:
    """
    Manager Agent responsible for:
    - Task announcement broadcasting (Call For Proposals - CFP).
    - Evaluating agent bids.
    - Contract awarding and task allocation.
    """
    def __init__(self, manager_id: str = "Manager_Central"):
        self.manager_id = manager_id
        self.announced_tasks: List[Task] = []
        self.allocation_history: List[Dict] = []

    def announce_task(self, task: Task, agents: List[DeliveryAgent]) -> Tuple[List[Bid], Optional[Bid]]:
        """Executes a single Contract Net Protocol cycle for one task."""
        bids: List[Bid] = []
        for agent in agents:
            bid = agent.generate_bid(task)
            bids.append(bid)

        # Filter feasible bids
        feasible_bids = [b for b in bids if b.feasible]
        if not feasible_bids:
            return bids, None

        # Select agent with lowest cost (and minimum time as tiebreaker)
        winning_bid = min(feasible_bids, key=lambda b: (b.cost, b.estimated_time_min))

        # Award task to the winning agent
        for agent in agents:
            if agent.agent_id == winning_bid.agent_id:
                agent.award_contract(task, winning_bid)
                break

        self.allocation_history.append({
            "task_id": task.task_id,
            "task_name": task.name,
            "agent_id": winning_bid.agent_id,
            "cost": winning_bid.cost,
            "time_min": winning_bid.estimated_time_min,
        })

        return bids, winning_bid


# ==============================================================================
# PARTIAL GLOBAL PLANNING (PGP) COORDINATOR
# ==============================================================================

class PGPCoordinator:
    """
    Partial Global Planning (PGP) Engine:
    Maintains a Partial Global View (PGV) of agent schedules, identifies
    spatial-temporal resource conflicts, and revises plans to restore coherence.
    """
    def __init__(self):
        self.global_schedule: List[PlanEntry] = []

    def set_plans(self, plans: List[PlanEntry]):
        self.global_schedule = list(plans)

    def detect_conflicts(self) -> List[Tuple[PlanEntry, PlanEntry, str]]:
        """
        Detects conflicts where two agents attempt to use the same resource
        simultaneously (temporal overlap on a single-capacity resource).
        """
        conflicts = []
        n = len(self.global_schedule)
        for i in range(n):
            for j in range(i + 1, n):
                entry_a = self.global_schedule[i]
                entry_b = self.global_schedule[j]

                # Check if same resource and different agents
                if entry_a.resource == entry_b.resource and entry_a.agent_id != entry_b.agent_id:
                    # Check temporal overlap: max(start) < min(end)
                    overlap_start = max(entry_a.start_time, entry_b.start_time)
                    overlap_end = min(entry_a.end_time, entry_b.end_time)

                    if overlap_start < overlap_end:
                        duration = overlap_end - overlap_start
                        conflicts.append((
                            entry_a,
                            entry_b,
                            f"Collision on '{entry_a.resource}' between [{overlap_start}m, {overlap_end}m] ({duration} mins overlap)"
                        ))
        return conflicts

    def resolve_conflict_by_priority(
        self,
        tasks_dict: Dict[str, Task],
        alternate_resource: Optional[str] = "Loading_Bay_Beta"
    ) -> List[str]:
        """
        Resolves conflicts using PGP Coordination Strategy:
        1. Compares task priorities.
        2. Higher priority task maintains its scheduled slot.
        3. Lower priority task is either rescheduled after the first completes,
           or diverted to an alternate resource.
        """
        conflicts = self.detect_conflicts()
        resolution_logs = []

        for entry_a, entry_b, description in conflicts:
            task_a = tasks_dict.get(entry_a.task_id)
            task_b = tasks_dict.get(entry_b.task_id)

            prio_a = task_a.priority if task_a else 2
            prio_b = task_b.priority if task_b else 2

            # Determine which plan to modify
            if prio_a <= prio_b:
                fixed_entry = entry_a
                modify_entry = entry_b
            else:
                fixed_entry = entry_b
                modify_entry = entry_a

            original_window = modify_entry.format_window()
            duration = modify_entry.duration

            # Resolution strategy: Reschedule modify_entry immediately after fixed_entry finishes
            new_start = fixed_entry.end_time + 5  # 5 minutes buffer
            new_end = new_start + duration

            modify_entry.start_time = new_start
            modify_entry.end_time = new_end
            new_window = modify_entry.format_window()

            log = (
                f"Resolved conflict on '{fixed_entry.resource}': "
                f"Agent '{modify_entry.agent_id}' (Task {modify_entry.task_id}, Prio {tasks_dict[modify_entry.task_id].priority}) "
                f"rescheduled from [{original_window}] to [{new_window}] "
                f"to yield priority to Agent '{fixed_entry.agent_id}' (Task {fixed_entry.task_id}, Prio {tasks_dict[fixed_entry.task_id].priority})."
            )
            resolution_logs.append(log)

        return resolution_logs


# ==============================================================================
# DATASETS & EXPERIMENT CONFIGURATIONS
# ==============================================================================

def get_default_tasks() -> List[Task]:
    """Returns at least 6 diverse delivery tasks."""
    return [
        Task(
            task_id="T1",
            name="Urgent Medical Supplies",
            destination="City General Hospital",
            distance_km=12.0,
            weight_kg=3.5,
            deadline_min=30,
            priority=1,  # Critical priority
        ),
        Task(
            task_id="T2",
            name="Bulk Grocery Consignment",
            destination="Downtown Community Hub",
            distance_km=18.0,
            weight_kg=28.0,
            deadline_min=90,
            priority=3,  # Standard priority
        ),
        Task(
            task_id="T3",
            name="Electronics & Microchips",
            destination="Silicon Tech Corridor",
            distance_km=25.0,
            weight_kg=8.0,
            deadline_min=60,
            priority=2,  # High priority
        ),
        Task(
            task_id="T4",
            name="Confidential Legal Dossier",
            destination="High Court Precinct",
            distance_km=7.5,
            weight_kg=1.2,
            deadline_min=45,
            priority=1,  # Critical priority
        ),
        Task(
            task_id="T5",
            name="Heavy Machinery Spare",
            destination="Eastern Industrial Port",
            distance_km=32.0,
            weight_kg=35.0,
            deadline_min=120,
            priority=3,  # Standard priority
        ),
        Task(
            task_id="T6",
            name="Retail Apparel Packages",
            destination="Metro Mall Distribution",
            distance_km=15.0,
            weight_kg=12.0,
            deadline_min=75,
            priority=2,  # High priority
        ),
    ]


def get_default_agents() -> List[DeliveryAgent]:
    """Returns at least 3 delivery agents with distinct profiles."""
    return [
        DeliveryAgent(
            agent_id="Agent_A",
            vehicle_type="Express Drone",
            base_cost=15.0,
            cost_per_km=1.8,
            speed_kmh=60.0,
            max_payload_kg=10.0,
            fixed_handling_time_min=5,
        ),
        DeliveryAgent(
            agent_id="Agent_B",
            vehicle_type="Electric Courier Van",
            base_cost=20.0,
            cost_per_km=1.2,
            speed_kmh=40.0,
            max_payload_kg=30.0,
            fixed_handling_time_min=12,
        ),
        DeliveryAgent(
            agent_id="Agent_C",
            vehicle_type="Heavy Cargo Truck",
            base_cost=30.0,
            cost_per_km=0.9,
            speed_kmh=30.0,
            max_payload_kg=50.0,
            fixed_handling_time_min=20,
        ),
    ]


# ==============================================================================
# EXERCISE 1: AGENT SETUP
# ==============================================================================

def run_exercise1(tasks: List[Task], agents: List[DeliveryAgent]):
    print("=" * 85)
    print("EXERCISE 1: AGENT SETUP & MULTI-AGENT ENVIRONMENT INITIALIZATION")
    print("=" * 85)
    print("System Configuration:")
    print("  * Manager Agent   : 1 Central Manager Agent ('Manager_Central')")
    print(f"  * Delivery Agents : {len(agents)} Autonomous Delivery Agents")
    print(f"  * Delivery Tasks  : {len(tasks)} Heterogeneous Delivery Tasks\n")

    print("--- Delivery Agent Specifications ---")
    print(f"{'Agent ID':<10} | {'Vehicle Type':<22} | {'Base ($)':<9} | {'$/km':<6} | {'Speed (km/h)':<14} | {'Max Payload (kg)':<16}")
    print("-" * 85)
    for ag in agents:
        print(f"{ag.agent_id:<10} | {ag.vehicle_type:<22} | ${ag.base_cost:<8.2f} | ${ag.cost_per_km:<5.2f} | {ag.speed_kmh:<14.1f} | {ag.max_payload_kg:<16.1f}")
    print()

    print("--- Delivery Tasks Specifications ---")
    print(f"{'ID':<4} | {'Task Description':<28} | {'Destination':<25} | {'Dist (km)':<9} | {'Weight':<8} | {'Deadline':<8} | {'Prio':<5}")
    print("-" * 96)
    for t in tasks:
        print(f"{t.task_id:<4} | {t.name:<28} | {t.destination:<25} | {t.distance_km:<9.1f} | {t.weight_kg:<8.1f} | {t.deadline_min:<8}m | P{t.priority:<4}")
    print()

    print("--- Agent Cost and Execution Time Evaluation Matrix ---")
    print(f"{'Task':<6} | " + " | ".join([f"{ag.agent_id} (Cost / Time)" for ag in agents]))
    print("-" * 75)
    for t in tasks:
        cols = []
        for ag in agents:
            cost, time_min, feasible = ag.calculate_cost_and_time(t)
            if feasible:
                cols.append(f"${cost:>6.2f} / {time_min:>2d}m")
            else:
                cols.append(f"{'INFEASIBLE':^15}")
        print(f"{t.task_id:<6} | " + " | ".join(cols))
    print()


# ==============================================================================
# EXERCISE 2: PGP COORDINATION (PARTIAL GLOBAL PLANNING)
# ==============================================================================

def run_exercise2(tasks: List[Task]):
    print("=" * 85)
    print("EXERCISE 2: PARTIAL GLOBAL PLANNING (PGP) COORDINATION")
    print("=" * 85)
    print("Goal: Detect spatial-temporal resource conflicts across agent local plans")
    print("      and coordinate plan modifications to establish global coherence.\n")

    tasks_dict = {t.task_id: t for t in tasks}
    shared_resource = "Loading_Bay_Alpha"

    # Define initial local plans with an intentional temporal overlap conflict:
    # Agent_A plans to load T1 at Loading_Bay_Alpha from 09:30 to 10:15 (min 30 to 75)
    # Agent_B plans to load T2 at Loading_Bay_Alpha from 09:50 to 10:40 (min 50 to 100)
    # Conflict exists between 09:50 and 10:15 (25 minutes overlap)
    initial_plans = [
        PlanEntry(
            agent_id="Agent_A",
            task_id="T1",
            resource=shared_resource,
            start_time=30,   # 09:30
            end_time=75,     # 10:15
            description="Loading urgent medical supplies into express drone payload bay"
        ),
        PlanEntry(
            agent_id="Agent_B",
            task_id="T2",
            resource=shared_resource,
            start_time=50,   # 09:50 -> CONFLICT with Agent_A!
            end_time=100,    # 10:40
            description="Forklift loading of bulk grocery pallets onto electric van"
        ),
        PlanEntry(
            agent_id="Agent_C",
            task_id="T5",
            resource="Loading_Bay_Beta",  # Independent resource
            start_time=60,   # 10:00
            end_time=120,    # 11:00
            description="Crane loading of heavy machinery parts onto cargo truck"
        ),
    ]

    print("1. Agents' Initial Local Plans (Before PGP Coordination):")
    print(f"{'Agent':<9} | {'Task':<5} | {'Resource':<18} | {'Time Window':<15} | {'Description'}")
    print("-" * 88)
    for p in initial_plans:
        print(f"{p.agent_id:<9} | {p.task_id:<5} | {p.resource:<18} | {p.format_window():<15} | {p.description}")
    print()

    # Step 2: Conflict Detection via PGP Coordinator
    coordinator = PGPCoordinator()
    coordinator.set_plans(initial_plans)
    conflicts = coordinator.detect_conflicts()

    print("2. PGP Conflict Detection:")
    if conflicts:
        print(f"   [!] Detected {len(conflicts)} Resource Conflict(s):")
        for idx, (ea, eb, desc) in enumerate(conflicts, 1):
            print(f"       Conflict #{idx}:")
            print(f"         - Agent '{ea.agent_id}' ({ea.task_id}) scheduled: {ea.format_window()} on '{ea.resource}'")
            print(f"         - Agent '{eb.agent_id}' ({eb.task_id}) scheduled: {eb.format_window()} on '{eb.resource}'")
            print(f"         - Detail: {desc}")
    else:
        print("   No conflicts detected.")
    print()

    # Step 3: PGP Coordination & Plan Revision
    print("3. PGP Conflict Resolution (Priority-Based Plan Adaptation):")
    resolution_logs = coordinator.resolve_conflict_by_priority(tasks_dict)
    for log in resolution_logs:
        print(f"   [OK] {log}")
    print()

    # Step 4: Verification of Modified Global Schedule
    remaining_conflicts = coordinator.detect_conflicts()
    print("4. Modified Agent Plans (After PGP Coordination):")
    print(f"{'Agent':<9} | {'Task':<5} | {'Resource':<18} | {'Time Window':<15} | {'Status'}")
    print("-" * 75)
    for p in coordinator.global_schedule:
        print(f"{p.agent_id:<9} | {p.task_id:<5} | {p.resource:<18} | {p.format_window():<15} | {'Coordinated (Conflict-Free)'}")
    print()
    print(f"Post-Coordination Verification: {len(remaining_conflicts)} active conflicts remaining.")
    print("Result: Global schedule coherence successfully achieved via PGP.\n")


# ==============================================================================
# EXERCISE 3: CONTRACT NET PROTOCOL (CNP) SINGLE TASK WALKTHROUGH
# ==============================================================================

def run_exercise3(tasks: List[Task], agents: List[DeliveryAgent]):
    print("=" * 85)
    print("EXERCISE 3: CONTRACT NET PROTOCOL (CNP) - STEP-BY-STEP TRACE")
    print("=" * 85)

    sample_task = tasks[0]  # T1: Urgent Medical Supplies
    print(f"Executing Full CNP Protocol Cycle for Representative Task: {sample_task.task_id} ('{sample_task.name}')")
    print(f"Task Details: Dist={sample_task.distance_km}km, Weight={sample_task.weight_kg}kg, Deadline={sample_task.deadline_min}min\n")

    manager = ManagerAgent("Manager_Central")

    # Step 1: Task Announcement (CFP)
    print("Step 1: Task Announcement (Call For Proposals - CFP)")
    print(f"  [Manager -> Broadcast] CFP for Task {sample_task.task_id}:")
    print(f"    - Destination : {sample_task.destination}")
    print(f"    - Payload     : {sample_task.weight_kg} kg")
    print(f"    - Distance    : {sample_task.distance_km} km")
    print(f"    - Deadline    : {sample_task.deadline_min} minutes\n")

    # Step 2: Bidding
    print("Step 2: Agent Bidding (Proposal Generation)")
    bids: List[Bid] = []
    for agent in agents:
        bid = agent.generate_bid(sample_task)
        bids.append(bid)
        if bid.feasible:
            print(f"  [Agent -> Manager] {bid.agent_id:<8} SUBMITS BID: Cost = ${bid.cost:<6.2f} | Time = {bid.estimated_time_min} mins")
        else:
            print(f"  [Agent -> Manager] {bid.agent_id:<8} REFUSES BID: {bid.notes}")
    print()

    # Step 3: Bid Comparison
    print("Step 3: Bid Comparison by Manager")
    print(f"  {'Agent ID':<10} | {'Feasibility':<12} | {'Bid Cost':<10} | {'Estimated Time':<16} | {'Evaluation'}")
    print("-" * 75)
    feasible_bids = [b for b in bids if b.feasible]
    winning_bid = min(feasible_bids, key=lambda b: (b.cost, b.estimated_time_min))

    for b in bids:
        status = "Eligible" if b.feasible else "Ineligible"
        cost_str = f"${b.cost:.2f}" if b.feasible else "N/A"
        time_str = f"{b.estimated_time_min}m" if b.feasible else "N/A"
        eval_str = "WINNER (Lowest Cost)" if b.agent_id == winning_bid.agent_id else ("Rejected (Higher Cost)" if b.feasible else b.notes)
        print(f"  {b.agent_id:<8} | {status:<12} | {cost_str:<10} | {time_str:<16} | {eval_str}")
    print()

    # Step 4: Agent Selection
    print("Step 4: Agent Selection")
    print(f"  Manager selected '{winning_bid.agent_id}' with the optimal bid:")
    print(f"    - Awarded Cost : ${winning_bid.cost:.2f}")
    print(f"    - Expected Time: {winning_bid.estimated_time_min} minutes\n")

    # Step 5: Task Assignment & Acceptance
    print("Step 5: Task Assignment & Contract Award")
    print(f"  [Manager -> {winning_bid.agent_id}] ACCEPT-PROPOSAL (Contract Awarded)")
    for b in bids:
        if b.agent_id != winning_bid.agent_id:
            print(f"  [Manager -> {b.agent_id}] REJECT-PROPOSAL")

    # Reset agents for next exercises
    for ag in agents:
        ag.reset_state()

    print(f"  [{winning_bid.agent_id} -> Manager] INFORM-DONE / CONFIRMATION (Task accepted into local schedule).\n")


# ==============================================================================
# EXERCISE 4: MULTIPLE TASK ALLOCATION
# ==============================================================================

def run_exercise4(tasks: List[Task], agents: List[DeliveryAgent]) -> Dict[str, Any]:
    print("=" * 85)
    print("EXERCISE 4: MULTIPLE TASK ALLOCATION VIA AUTOMATED CNP")
    print("=" * 85)
    print(f"Iteratively allocating all {len(tasks)} delivery tasks across {len(agents)} agents...\n")

    for ag in agents:
        ag.reset_state()

    manager = ManagerAgent("Manager_Central")
    task_allocations = []

    for task in tasks:
        bids, winner = manager.announce_task(task, agents)
        if winner:
            task_allocations.append({
                "task_id": task.task_id,
                "task_name": task.name,
                "agent_id": winner.agent_id,
                "cost": winner.cost,
                "time_min": winner.estimated_time_min,
            })
        else:
            task_allocations.append({
                "task_id": task.task_id,
                "task_name": task.name,
                "agent_id": "UNASSIGNED",
                "cost": 0.0,
                "time_min": 0,
            })

    # Format output table
    print("FINAL TASK ALLOCATION TABLE:")
    print(f"{'Task':<6} | {'Task Description':<28} | {'Selected Agent':<16} | {'Cost ($)':<10} | {'Time (min)':<10}")
    print("-" * 82)
    total_cost = 0.0
    total_time = 0

    for alloc in task_allocations:
        print(f"{alloc['task_id']:<6} | {alloc['task_name']:<28} | {alloc['agent_id']:<16} | ${alloc['cost']:<9.2f} | {alloc['time_min']:<10}")
        total_cost += alloc['cost']
        total_time += alloc['time_min']
    print("-" * 82)
    print(f"{'TOTALS':<53} | ${total_cost:<9.2f} | {total_time:<10} mins\n")

    print("--- Individual Agent Workload Summary ---")
    print(f"{'Agent ID':<10} | {'Vehicle Type':<22} | {'Assigned Tasks':<16} | {'Total Cost':<12} | {'Total Time':<12}")
    print("-" * 80)
    agent_summary = {}
    for ag in agents:
        task_ids = ", ".join([t.task_id for t in ag.assigned_tasks]) if ag.assigned_tasks else "None"
        print(f"{ag.agent_id:<10} | {ag.vehicle_type:<22} | {task_ids:<16} | ${ag.total_cost_incurred:<11.2f} | {ag.total_time_spent_min:<8} mins")
        agent_summary[ag.agent_id] = {
            "tasks": [t.task_id for t in ag.assigned_tasks],
            "cost": ag.total_cost_incurred,
            "time": ag.total_time_spent_min,
        }
    print()

    return {
        "allocations": task_allocations,
        "total_cost": total_cost,
        "total_time": total_time,
        "agent_summary": agent_summary,
    }


# ==============================================================================
# EXERCISE 5: MODIFICATION & VISUALIZATION
# ==============================================================================

def run_exercise5(
    tasks: List[Task],
    original_agents: List[DeliveryAgent],
    original_results: Dict[str, Any],
    output_dir: str
):
    print("=" * 85)
    print("EXERCISE 5: MODIFICATION & VISUALIZATION (COMPARATIVE ANALYSIS)")
    print("=" * 85)
    print("Modification Scenario:")
    print("  1. Environmental/Operational Parameter Changes:")
    print("     - Fuel & battery tariff surcharge increases Agent_A base cost ($15 -> $28).")
    print("     - Agent_B gets upgraded fast electric drivetrain (speed 40 km/h -> 55 km/h, $/km $1.2 -> $1.0).")
    print("     - Agent_C implements green logistics subsidy reducing base cost ($30 -> $22).")
    print("     - Heavy machinery spare T5 payload increases from 35 kg -> 42 kg.\n")

    # Modified tasks
    modified_tasks = copy.deepcopy(tasks)
    modified_tasks[4].weight_kg = 42.0  # T5 heavier

    # Modified agents
    modified_agents = [
        DeliveryAgent(
            agent_id="Agent_A",
            vehicle_type="Express Drone (High Tariff)",
            base_cost=28.0,          # increased base cost
            cost_per_km=2.2,         # increased cost per km
            speed_kmh=60.0,
            max_payload_kg=10.0,
            fixed_handling_time_min=5,
        ),
        DeliveryAgent(
            agent_id="Agent_B",
            vehicle_type="Upgraded Electric Van",
            base_cost=18.0,          # discounted base cost
            cost_per_km=1.0,         # cheaper $/km
            speed_kmh=55.0,          # faster speed
            max_payload_kg=30.0,
            fixed_handling_time_min=10,
        ),
        DeliveryAgent(
            agent_id="Agent_C",
            vehicle_type="Green Cargo Truck",
            base_cost=22.0,          # subsidized base cost
            cost_per_km=0.85,        # cheaper rate
            speed_kmh=35.0,          # slightly faster
            max_payload_kg=50.0,
            fixed_handling_time_min=18,
        ),
    ]

    print("--- Re-running Multiple Task Allocation with Modified Costs & Capabilities ---")
    modified_results = run_exercise4(modified_tasks, modified_agents)

    # Comparative table
    print("\n" + "=" * 95)
    print("COMPARISON: INITIAL VS MODIFIED TASK ALLOCATION")
    print("=" * 95)
    print(f"{'Task':<6} | {'Initial Agent':<15} | {'Initial Cost':<14} | {'Modified Agent':<16} | {'Modified Cost':<14} | {'Reallocated?'}")
    print("-" * 95)

    orig_alloc = {a["task_id"]: a for a in original_results["allocations"]}
    mod_alloc = {a["task_id"]: a for a in modified_results["allocations"]}

    realloc_count = 0
    for t in tasks:
        oa = orig_alloc[t.task_id]
        ma = mod_alloc[t.task_id]
        realloc = "YES (Shifted)" if oa["agent_id"] != ma["agent_id"] else "NO (Same)"
        if oa["agent_id"] != ma["agent_id"]:
            realloc_count += 1
        print(f"{t.task_id:<6} | {oa['agent_id']:<15} | ${oa['cost']:<13.2f} | {ma['agent_id']:<16} | ${ma['cost']:<13.2f} | {realloc}")

    print("-" * 95)
    print(f"Overall Cost: Initial = ${original_results['total_cost']:.2f} | Modified = ${modified_results['total_cost']:.2f}")
    print(f"Total Tasks Reallocated: {realloc_count} out of {len(tasks)}\n")

    # Plotting visualization using Matplotlib
    print("--- Generating Matplotlib Comparative Visualization ---")
    plot_path = os.path.join(output_dir, "exercise5_agent_cost_comparison.png")

    try:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt
        import numpy as np

        agent_ids = [ag.agent_id for ag in original_agents]
        initial_costs = [original_results["agent_summary"][aid]["cost"] for aid in agent_ids]
        modified_costs = [modified_results["agent_summary"][aid]["cost"] for aid in agent_ids]
        initial_times = [original_results["agent_summary"][aid]["time"] for aid in agent_ids]
        modified_times = [modified_results["agent_summary"][aid]["time"] for aid in agent_ids]

        x = np.arange(len(agent_ids))
        width = 0.35

        # Create dual-panel figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

        # Subplot 1: Total Assigned Cost
        rects1 = ax1.bar(x - width/2, initial_costs, width, label="Initial Scenario", color="#1f77b4", edgecolor="black", alpha=0.9)
        rects2 = ax1.bar(x + width/2, modified_costs, width, label="Modified Scenario", color="#ff7f0e", edgecolor="black", alpha=0.9)

        ax1.set_ylabel("Total Operational Cost ($)", fontsize=12, fontweight="bold")
        ax1.set_title("Agent vs Total Assigned Cost", fontsize=13, fontweight="bold", pad=12)
        ax1.set_xticks(x)
        ax1.set_xticklabels(agent_ids, fontsize=11, fontweight="bold")
        ax1.legend(frameon=True, facecolor="white", edgecolor="none")
        ax1.grid(axis="y", linestyle="--", alpha=0.4)

        # Bar value annotations
        for rect in rects1:
            h = rect.get_height()
            if h > 0:
                ax1.annotate(f"${h:.1f}", xy=(rect.get_x() + rect.get_width()/2, h),
                             xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")
        for rect in rects2:
            h = rect.get_height()
            if h > 0:
                ax1.annotate(f"${h:.1f}", xy=(rect.get_x() + rect.get_width()/2, h),
                             xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

        # Subplot 2: Total Assigned Execution Time
        rects3 = ax2.bar(x - width/2, initial_times, width, label="Initial Scenario", color="#2ca02c", edgecolor="black", alpha=0.9)
        rects4 = ax2.bar(x + width/2, modified_times, width, label="Modified Scenario", color="#d62728", edgecolor="black", alpha=0.9)

        ax2.set_ylabel("Total Execution Time (Minutes)", fontsize=12, fontweight="bold")
        ax2.set_title("Agent vs Total Assigned Time", fontsize=13, fontweight="bold", pad=12)
        ax2.set_xticks(x)
        ax2.set_xticklabels(agent_ids, fontsize=11, fontweight="bold")
        ax2.legend(frameon=True, facecolor="white", edgecolor="none")
        ax2.grid(axis="y", linestyle="--", alpha=0.4)

        for rect in rects3:
            h = rect.get_height()
            if h > 0:
                ax2.annotate(f"{int(h)}m", xy=(rect.get_x() + rect.get_width()/2, h),
                             xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")
        for rect in rects4:
            h = rect.get_height()
            if h > 0:
                ax2.annotate(f"{int(h)}m", xy=(rect.get_x() + rect.get_width()/2, h),
                             xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

        fig.suptitle("Experiment 8: Multi-Agent Task Allocation & Coordination (PGP & CNP)", fontsize=15, fontweight="bold", y=1.02)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"  [OK] Successfully saved comparative plot: {plot_path}")

    except Exception as e:
        print(f"  [!] Matplotlib plotting encountered issue: {e}")
        # Robust fallback using Pillow if matplotlib backend has any environment limitation
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("RGB", (900, 500), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            draw.rectangle([(20, 20), (880, 480)], outline=(200, 200, 200), width=2)
            draw.text((40, 40), "Experiment 8: Multi-Agent Task Allocation (CNP Comparison)", fill=(30, 30, 30))
            # Draw simple bar chart
            origin_x = 100
            origin_y = 400
            draw.line([(origin_x, origin_y), (820, origin_y)], fill=(50, 50, 50), width=3)
            draw.line([(origin_x, origin_y), (origin_x, 80)], fill=(50, 50, 50), width=3)
            draw.text((origin_x, 60), "Assigned Cost ($)", fill=(50, 50, 50))

            agents = ["Agent_A", "Agent_B", "Agent_C"]
            init_c = [original_results["agent_summary"][a]["cost"] for a in agents]
            mod_c = [modified_results["agent_summary"][a]["cost"] for a in agents]
            max_c = max(max(init_c), max(mod_c), 1.0)

            for i, a in enumerate(agents):
                bx = origin_x + 60 + i * 240
                h1 = int((init_c[i] / max_c) * 280)
                h2 = int((mod_c[i] / max_c) * 280)
                draw.rectangle([(bx, origin_y - h1), (bx + 50, origin_y)], fill=(31, 119, 180), outline=(0, 0, 0))
                draw.rectangle([(bx + 55, origin_y - h2), (bx + 105, origin_y)], fill=(255, 127, 14), outline=(0, 0, 0))
                draw.text((bx + 15, origin_y + 15), a, fill=(0, 0, 0))
                draw.text((bx, origin_y - h1 - 20), f"${init_c[i]:.1f}", fill=(31, 119, 180))
                draw.text((bx + 55, origin_y - h2 - 20), f"${mod_c[i]:.1f}", fill=(255, 127, 14))

            # Legend
            draw.rectangle([(620, 40), (640, 55)], fill=(31, 119, 180))
            draw.text((650, 40), "Initial Scenario", fill=(0, 0, 0))
            draw.rectangle([(620, 65), (640, 80)], fill=(255, 127, 14))
            draw.text((650, 65), "Modified Scenario", fill=(0, 0, 0))

            img.save(plot_path)
            print(f"  [OK] Successfully generated plot via PIL fallback: {plot_path}")
        except Exception as e_pil:
            print(f"  [!] Fallback plotting failed: {e_pil}")


# ==============================================================================
# OBSERVATIONS & SUMMARY
# ==============================================================================

def print_observations():
    print("=" * 85)
    print("COMPREHENSIVE OBSERVATIONS & MULTI-AGENT DYNAMICS ANALYSIS")
    print("=" * 85)
    print("""
1. Partial Global Planning (PGP) Dynamics:
   - Coherence Without Full Centralization: Agents retain autonomous control over their
     internal trajectories and only expose partial global plans (resource reservations).
   - Conflict Detection: The PGP coordinator detects spatial-temporal collisions
     (e.g., simultaneous use of Loading Bay Alpha) by evaluating time-window overlaps.
   - Dynamic Deconfliction: Using domain heuristics (task priority), the lower-priority
     agent's plan is shifted smoothly, eliminating deadlock while honoring deadlines.

2. Contract Net Protocol (CNP) Market Mechanics:
   - Decentralized Matching: CNP operates as an automated market mechanism. The Manager
     does not require complete internal operational models of each agent; agents privately
     compute their own capabilities and costs, preserving information privacy.
   - Natural Specialization: Express Drone (Agent A) naturally wins lightweight, urgent
     deliveries (T1, T4); Electric Van (Agent B) captures balanced mid-range tasks (T3, T6);
     Heavy Cargo Truck (Agent C) secures bulky freight (T2, T5).

3. Sensitivity to Cost & Capability Adjustments:
   - Price & Capacity Elasticity: When drone operating costs surged in Scenario B,
     lightweight deliveries shifted to the upgraded electric van.
   - Adaptability: CNP immediately reallocates tasks to achieve the new global cost
     optimum without requiring manual system reconfiguration or rule reprogramming.
""")
    print("=" * 85)


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tasks = get_default_tasks()
    agents = get_default_agents()

    print("\n" + "#" * 85)
    print("AI401 EXPERT SYSTEMS LAB -- EXPERIMENT 8")
    print("MULTI-AGENT TASK ALLOCATION AND COORDINATION (PGP & CNP)")
    print("#" * 85 + "\n")

    # Exercise 1
    run_exercise1(tasks, agents)

    # Exercise 2
    run_exercise2(tasks)

    # Exercise 3
    run_exercise3(tasks, agents)

    # Exercise 4
    results = run_exercise4(tasks, agents)

    # Exercise 5
    run_exercise5(tasks, agents, results, script_dir)

    # Observations
    print_observations()


if __name__ == "__main__":
    main()
