"""
AI401 - Expert Systems Lab
Experiment 4 / Lab 5: Backward Chaining Inference Engine with Askable Facts (Goal-Driven Reasoning)
Car-Fault Diagnosis Expert System
"""

from typing import List, Dict, Set, Tuple, Optional, Union

class Rule:
    """
    Represents an IF-THEN Production Rule for Backward Chaining.
    - id: Unique rule identifier (e.g., 'R1')
    - conditions: List of condition strings. Supports 'NOT <fact>' for negation.
    - conclusion: Goal or sub-goal derived when rule holds.
    - description: Human-readable description of rule logic.
    """
    def __init__(self, rule_id: str, conditions: List[str], conclusion: str, description: str = ""):
        self.id = rule_id
        self.conditions = conditions
        self.conclusion = conclusion
        self.description = description or f"IF {' AND '.join(conditions)} THEN {conclusion}"

    def __repr__(self) -> str:
        return f"[{self.id}] IF {' AND '.join(self.conditions)} THEN {self.conclusion}"


def build_car_diagnosis_kb() -> Tuple[List[Rule], Dict[str, str], List[str]]:
    """
    Constructs the Car-Fault Diagnosis Rule Base, Askable Facts, and Candidate Hypotheses.
    """
    rules = [
        # R1: Starter Motor Fault
        Rule("R1", ["clicking_sound", "NOT engine_cranks"], "starter_motor_fault",
             "Starter Motor Rule: Clicking sound without engine cranking indicates starter motor failure."),
        
        # R2: Dead Battery
        Rule("R2", ["NOT lights_working", "NOT engine_cranks"], "dead_battery",
             "Dead Battery Rule: No lights and no engine cranking indicates a dead battery."),

        # R3: Empty Fuel Tank
        Rule("R3", ["engine_cranks", "NOT engine_starts", "fuel_gauge_empty"], "empty_fuel_tank",
             "Empty Fuel Tank Rule: Engine cranks but won't start and fuel gauge is empty."),

        # R4: Bad Spark Plug
        Rule("R4", ["engine_cranks", "NOT engine_starts", "spark_plug_dirty"], "bad_spark_plug",
             "Bad Spark Plug Rule: Engine cranks but won't start and spark plug is fouled."),

        # R5: Alternator Failure
        Rule("R5", ["battery_drains_frequently", "dim_headlights"], "alternator_failure",
             "Alternator Failure Rule: Battery drains frequently and headlights are dim."),
    ]

    # Askable facts with user-friendly questions
    askable_facts = {
        "clicking_sound": "Is there a clicking sound when turning the ignition key?",
        "engine_cranks": "Does the engine crank over when turning the key?",
        "lights_working": "Are the headlights and dashboard lights working normally?",
        "engine_starts": "Does the engine start up successfully?",
        "fuel_gauge_empty": "Is the fuel gauge pointing to empty (E)?",
        "spark_plug_dirty": "Are the spark plugs dirty, oily, or fouled?",
        "battery_drains_frequently": "Does the car battery drain frequently overnight?",
        "dim_headlights": "Are the headlights dim or flickering while driving?",
    }

    # Ordered list of hypotheses (goals) to evaluate
    hypotheses = [
        "starter_motor_fault",
        "dead_battery",
        "empty_fuel_tank",
        "bad_spark_plug",
        "alternator_failure",
    ]

    return rules, askable_facts, hypotheses


class BackwardChainingEngine:
    """
    Goal-Driven Backward Chaining Inference Engine with Askable Facts and WHY Explanation Facility.
    """
    def __init__(self, rules: List[Rule], askable_facts: Dict[str, str], hypotheses: List[str]):
        self.rules = rules
        self.askable_facts = askable_facts
        self.hypotheses = hypotheses
        self.wm: Dict[str, bool] = {}  # Working Memory: fact_name -> True/False
        self.asked_questions: List[Tuple[str, str]] = []  # Log of (fact, answer)
        self.reasoning_stack: List[Tuple[Rule, str]] = []  # Stack of (Rule, Current Goal)

    def reset_wm(self):
        """Clears working memory and logs for a new inference session."""
        self.wm.clear()
        self.asked_questions.clear()
        self.reasoning_stack.clear()

    def ask_user(self, fact: str, goal: str, simulated_inputs: Optional[List[str]] = None) -> bool:
        """
        Asks the user about an askable fact. Supports 'WHY' explanations.
        Can run interactively or with simulated inputs for testing.
        """
        question = self.askable_facts.get(fact, f"Is '{fact}' true?")

        while True:
            if simulated_inputs is not None and len(simulated_inputs) > 0:
                user_input = simulated_inputs.pop(0).strip()
                print(f"[ASK] {question} -> User Input: '{user_input}'")
            else:
                user_input = input(f"[ASK] {question} (yes/no/why): ").strip()

            ans_upper = user_input.upper()

            if ans_upper == "WHY":
                # Display WHY Explanation
                print("\n" + "=" * 60)
                print("  [EXPLANATION FACILITY — 'WHY' RESPONSE]")
                print("=" * 60)
                print(f"  Target Hypothesis Being Evaluated : '{goal}'")
                if self.reasoning_stack:
                    current_rule, current_goal = self.reasoning_stack[-1]
                    print(f"  Current Rule Evaluated            : {current_rule}")
                    print(f"  Rule Description                  : {current_rule.description}")
                print(f"  Reason For Question               : To determine if condition '{fact}' is satisfied.")
                print("=" * 60 + "\n")
                # Loop continues to re-prompt for yes/no after WHY explanation
            elif ans_upper in ["YES", "Y", "TRUE", "1"]:
                self.wm[fact] = True
                self.asked_questions.append((fact, "yes"))
                return True
            elif ans_upper in ["NO", "N", "FALSE", "0"]:
                self.wm[fact] = False
                self.asked_questions.append((fact, "no"))
                return False
            else:
                print("  [!] Invalid response. Please answer 'yes', 'no', or 'why'.")

    def evaluate_goal(self, goal: str, simulated_inputs: Optional[List[str]] = None) -> bool:
        """
        Recursively evaluates whether a goal/sub-goal is true using backward chaining.
        """
        # 1. Check if fact is already known in Working Memory
        if goal.startswith("NOT "):
            negated_fact = goal[4:].strip()
            if negated_fact in self.wm:
                return not self.wm[negated_fact]
        elif goal in self.wm:
            return self.wm[goal]

        # Handle negated goal lookup
        raw_fact = goal[4:].strip() if goal.startswith("NOT ") else goal
        is_negated = goal.startswith("NOT ")

        # 2. Find rules that conclude raw_fact
        matching_rules = [r for r in self.rules if r.conclusion == raw_fact]

        if matching_rules:
            for rule in matching_rules:
                self.reasoning_stack.append((rule, raw_fact))
                all_conditions_satisfied = True

                for cond in rule.conditions:
                    cond_result = self.evaluate_goal(cond, simulated_inputs)
                    if not cond_result:
                        all_conditions_satisfied = False
                        break

                self.reasoning_stack.pop()

                if all_conditions_satisfied:
                    self.wm[raw_fact] = True
                    return not is_negated if is_negated else True

            # If rules failed
            if raw_fact not in self.wm:
                self.wm[raw_fact] = False
            return not is_negated if is_negated else self.wm[raw_fact]

        # 3. If no rules conclude raw_fact, check if it is askable
        if raw_fact in self.askable_facts:
            answer = self.ask_user(raw_fact, goal, simulated_inputs)
            return not answer if is_negated else answer

        # 4. If neither rule nor askable fact, cannot be proven
        self.wm[raw_fact] = False
        return False

    def diagnose(self, hypotheses_order: Optional[List[str]] = None, simulated_inputs: Optional[List[str]] = None) -> Tuple[Optional[str], List[Tuple[str, str]], Dict[str, bool]]:
        """
        Runs backward chaining across candidate hypotheses in specified order.
        Returns (confirmed_fault, asked_questions_log, final_working_memory).
        """
        self.reset_wm()
        active_hypotheses = hypotheses_order or self.hypotheses

        confirmed_fault = None
        for hypothesis in active_hypotheses:
            print(f"\n---> Investigating Hypothesis: '{hypothesis}'")
            if self.evaluate_goal(hypothesis, simulated_inputs):
                confirmed_fault = hypothesis
                print(f"  [SUCCESS] Hypothesis CONFIRMED: '{hypothesis}'")
                break
            else:
                print(f"  [REJECTED] Hypothesis failed: '{hypothesis}'")

        return confirmed_fault, self.asked_questions, self.wm


def run_exercise1():
    print("=" * 80)
    print("EXERCISE 1: STARTER MOTOR FAULT DIAGNOSIS")
    print("=" * 80)

    rules, askable_facts, hypotheses = build_car_diagnosis_kb()
    engine = BackwardChainingEngine(rules, askable_facts, hypotheses)

    # Simulated Inputs for Starter Motor Test:
    # Question 1: clicking_sound -> yes
    # Question 2: engine_cranks -> no
    simulated = ["yes", "no"]

    fault, questions, wm = engine.diagnose(simulated_inputs=simulated)

    print("\nResults Summary:")
    print(f"  Questions Asked   : {[q[0] + '=' + q[1] for q in questions]}")
    print(f"  Working Memory    : {wm}")
    print(f"  Identified Fault  : {fault if fault else 'No Fault Identified'}")


def run_exercise2():
    print("\n" + "=" * 80)
    print("EXERCISE 2: IMPACT OF HYPOTHESIS ORDER ON QUESTION SEQUENCE")
    print("=" * 80)

    rules, askable_facts, hypotheses = build_car_diagnosis_kb()
    engine = BackwardChainingEngine(rules, askable_facts, hypotheses)

    # Order A: Starter Motor first -> [starter_motor_fault, empty_fuel_tank, dead_battery]
    order_a = ["starter_motor_fault", "empty_fuel_tank", "dead_battery"]
    sim_a = ["yes", "no"]  # Triggers starter motor fault on 1st hypothesis

    print("\n>>> Testing Hypothesis Order A: " + str(order_a))
    fault_a, questions_a, _ = engine.diagnose(hypotheses_order=order_a, simulated_inputs=sim_a)

    # Order B: Empty Fuel Tank first -> [empty_fuel_tank, starter_motor_fault, dead_battery]
    # For empty_fuel_tank: engine_cranks -> no (fails empty_fuel_tank), then moves to starter_motor_fault: clicking_sound -> yes
    order_b = ["empty_fuel_tank", "starter_motor_fault", "dead_battery"]
    sim_b = ["no", "yes"]  # engine_cranks=no -> fails R3, then for R1: clicking_sound=yes (engine_cranks=no is cached!)

    print("\n>>> Testing Hypothesis Order B: " + str(order_b))
    fault_b, questions_b, _ = engine.diagnose(hypotheses_order=order_b, simulated_inputs=sim_b)

    print("\nComparison Summary:")
    print(f"  Order A Asked Questions : {[q[0] for q in questions_a]}")
    print(f"  Order B Asked Questions : {[q[0] for q in questions_b]}")
    print("  Observation: Changing hypothesis order changes which questions are asked first due to goal-driven reasoning!")


def run_exercise3():
    print("\n" + "=" * 80)
    print("EXERCISE 3: 'WHY' EXPLANATION FACILITY DEMONSTRATION")
    print("=" * 80)

    rules, askable_facts, hypotheses = build_car_diagnosis_kb()
    engine = BackwardChainingEngine(rules, askable_facts, hypotheses)

    # Simulated Inputs: User types 'why' when asked clicking_sound, then answers 'yes', then 'no' for engine_cranks
    simulated_inputs = ["why", "yes", "no"]

    fault, questions, wm = engine.diagnose(simulated_inputs=simulated_inputs)

    print("\nResults Summary:")
    print(f"  Final Diagnosis : {fault}")
    print(f"  Questions Answered : {questions}")


def main():
    run_exercise1()
    run_exercise2()
    run_exercise3()


if __name__ == "__main__":
    main()
