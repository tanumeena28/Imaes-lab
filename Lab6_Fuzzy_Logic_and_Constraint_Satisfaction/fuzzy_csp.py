"""
AI401 - Expert Systems Lab
Experiment 6 / Lab 6: Fuzzy Logic and Constraint Satisfaction Problems (CSP)
Part 1: Fuzzy Logic Student Performance System
Part 2: Timetable Scheduling CSP Solver
"""

from typing import Dict, List, Tuple, Callable, Optional, Set

# ==============================================================================
# PART 1: FUZZY LOGIC SYSTEM
# ==============================================================================

class MembershipFunction:
    """Base class for Fuzzy Membership Functions."""
    def get_membership(self, x: float) -> float:
        raise NotImplementedError

class TriangularMF(MembershipFunction):
    """Triangular Membership Function defined by vertices (a, b, c)."""
    def __init__(self, a: float, b: float, c: float):
        self.a = a
        self.b = b
        self.c = c

    def get_membership(self, x: float) -> float:
        if x <= self.a or x >= self.c:
            return 0.0
        elif self.a < x <= self.b:
            return (x - self.a) / (self.b - self.a) if self.b != self.a else 1.0
        else:
            return (self.c - x) / (self.c - self.b) if self.c != self.b else 1.0


class TrapezoidalMF(MembershipFunction):
    """Trapezoidal Membership Function defined by (a, b, c, d)."""
    def __init__(self, a: float, b: float, c: float, d: float):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def get_membership(self, x: float) -> float:
        if x <= self.a or x >= self.d:
            return 0.0
        elif self.a < x <= self.b:
            return (x - self.a) / (self.b - self.a) if self.b != self.a else 1.0
        elif self.b < x <= self.c:
            return 1.0
        else:
            return (self.d - x) / (self.d - self.c) if self.d != self.c else 1.0


class FuzzyVariable:
    """Represents a linguistic variable (e.g., Attendance, Marks, Performance)."""
    def __init__(self, name: str, min_val: float, max_val: float):
        self.name = name
        self.min_val = min_val
        self.max_val = max_val
        self.terms: Dict[str, MembershipFunction] = {}

    def add_term(self, term_name: str, mf: MembershipFunction):
        self.terms[term_name] = mf

    def fuzzify(self, x: float) -> Dict[str, float]:
        """Calculates membership degree for each linguistic term."""
        return {term: mf.get_membership(x) for term, mf in self.terms.items()}


class StudentFuzzyEngine:
    """Fuzzy Logic System to determine Student Performance from Attendance and Marks."""
    def __init__(self, strict_rules: bool = False):
        self.strict_rules = strict_rules
        self.setup_variables()

    def setup_variables(self):
        # 1. Attendance Variable (0 - 100%)
        self.attendance = FuzzyVariable("Attendance", 0, 100)
        self.attendance.add_term("Low", TrapezoidalMF(0, 0, 30, 55))
        self.attendance.add_term("Medium", TriangularMF(35, 60, 85))
        self.attendance.add_term("High", TrapezoidalMF(65, 85, 100, 100))

        # 2. Marks Variable (0 - 100)
        self.marks = FuzzyVariable("Marks", 0, 100)
        self.marks.add_term("Poor", TrapezoidalMF(0, 0, 30, 50))
        self.marks.add_term("Average", TriangularMF(35, 55, 75))
        self.marks.add_term("Excellent", TrapezoidalMF(65, 85, 100, 100))

        # 3. Performance Variable (0 - 100%)
        self.performance = FuzzyVariable("Performance", 0, 100)
        self.performance.add_term("Unsatisfactory", TrapezoidalMF(0, 0, 25, 45))
        self.performance.add_term("Satisfactory", TriangularMF(35, 55, 75))
        self.performance.add_term("Outstanding", TrapezoidalMF(65, 85, 100, 100))

    def evaluate(self, attendance_val: float, marks_val: float) -> Tuple[float, str, Dict[str, float]]:
        """
        Evaluates fuzzy rules using Min-Max Mamdani Inference and Centroid Defuzzification.
        """
        att_deg = self.attendance.fuzzify(attendance_val)
        marks_deg = self.marks.fuzzify(marks_val)

        rule_outputs: Dict[str, float] = {
            "Unsatisfactory": 0.0,
            "Satisfactory": 0.0,
            "Outstanding": 0.0,
        }

        if not self.strict_rules:
            # Standard Rule Base
            # Rule 1: IF Attendance is Low OR Marks is Poor THEN Performance is Unsatisfactory
            r1 = max(att_deg["Low"], marks_deg["Poor"])
            rule_outputs["Unsatisfactory"] = max(rule_outputs["Unsatisfactory"], r1)

            # Rule 2: IF Attendance is Medium AND Marks is Average THEN Performance is Satisfactory
            r2 = min(att_deg["Medium"], marks_deg["Average"])
            rule_outputs["Satisfactory"] = max(rule_outputs["Satisfactory"], r2)

            # Rule 3: IF Attendance is High AND Marks is Excellent THEN Performance is Outstanding
            r3 = min(att_deg["High"], marks_deg["Excellent"])
            rule_outputs["Outstanding"] = max(rule_outputs["Outstanding"], r3)

            # Rule 4: IF Attendance is High AND Marks is Average THEN Performance is Satisfactory
            r4 = min(att_deg["High"], marks_deg["Average"])
            rule_outputs["Satisfactory"] = max(rule_outputs["Satisfactory"], r4)

            # Rule 5: IF Attendance is Low AND Marks is Excellent THEN Performance is Satisfactory
            r5 = min(att_deg["Low"], marks_deg["Excellent"])
            rule_outputs["Satisfactory"] = max(rule_outputs["Satisfactory"], r5)
        else:
            # Modified / Strict Rule Base (Exercise 3)
            # Strict Rule 1: IF Attendance is Low THEN Performance is ALWAYS Unsatisfactory regardless of marks!
            r1 = att_deg["Low"]
            rule_outputs["Unsatisfactory"] = max(rule_outputs["Unsatisfactory"], r1)

            # Strict Rule 2: IF Marks is Poor THEN Performance is Unsatisfactory
            r2 = marks_deg["Poor"]
            rule_outputs["Unsatisfactory"] = max(rule_outputs["Unsatisfactory"], r2)

            # Strict Rule 3: IF Attendance is High AND Marks is Excellent THEN Performance is Outstanding
            r3 = min(att_deg["High"], marks_deg["Excellent"])
            rule_outputs["Outstanding"] = max(rule_outputs["Outstanding"], r3)

            # Strict Rule 4: IF Attendance is Medium AND Marks is Average THEN Performance is Satisfactory
            r4 = min(att_deg["Medium"], marks_deg["Average"])
            rule_outputs["Satisfactory"] = max(rule_outputs["Satisfactory"], r4)

        # Centroid Defuzzification over y in [0, 100]
        numerator = 0.0
        denominator = 0.0

        for y in range(0, 101):
            # Aggregated membership degree at output point y
            mu_unsat = min(rule_outputs["Unsatisfactory"], self.performance.terms["Unsatisfactory"].get_membership(y))
            mu_sat = min(rule_outputs["Satisfactory"], self.performance.terms["Satisfactory"].get_membership(y))
            mu_out = min(rule_outputs["Outstanding"], self.performance.terms["Outstanding"].get_membership(y))

            mu_aggregated = max(mu_unsat, mu_sat, mu_out)

            numerator += y * mu_aggregated
            denominator += mu_aggregated

        crisp_score = numerator / denominator if denominator != 0 else 50.0

        # Classify crisp category
        if crisp_score < 40:
            category = "Unsatisfactory"
        elif crisp_score < 70:
            category = "Satisfactory"
        else:
            category = "Outstanding"

        return crisp_score, category, rule_outputs


# ==============================================================================
# PART 2: CONSTRAINT SATISFACTION PROBLEM (CSP) - TIMETABLE SCHEDULING
# ==============================================================================

class TimetableCSP:
    """
    Constraint Satisfaction Problem Solver for Course Timetable Scheduling.
    Variables: Courses (C1: Maths, C2: Physics, C3: Chemistry, C4: CS)
    Domains: Tuples of (TimeSlot, Room)
    """
    def __init__(self, tight_constraints: bool = False):
        self.tight_constraints = tight_constraints

        # Variables: Courses
        self.variables = ["C1_Maths", "C2_Physics", "C3_Chem", "C4_CS"]

        # Domains: Slots (9AM, 10AM, 11AM) and Rooms (Room A, Room B)
        self.slots = ["Slot1_9AM", "Slot2_10AM", "Slot3_11AM"]
        self.rooms = ["Room_A", "Room_B"]

        self.domain = [(slot, room) for slot in self.slots for room in self.rooms]

        # Professors mapping
        self.professors = {
            "C1_Maths": "Prof_Smith",
            "C2_Physics": "Prof_Smith",    # Prof Smith teaches both Maths & Physics
            "C3_Chem": "Prof_Jones",
            "C4_CS": "Prof_Alan",
        }

    def is_valid_assignment(self, var: str, value: Tuple[str, str], assignment: Dict[str, Tuple[str, str]]) -> bool:
        """Checks if assigning value=(slot, room) to var violates any constraint."""
        slot, room = value

        for other_var, (other_slot, other_room) in assignment.items():
            # Constraint 1: Room Conflict — No two courses in same room at same time slot
            if slot == other_slot and room == other_room:
                return False

            # Constraint 2: Professor Conflict — Same professor cannot teach two courses in same time slot
            if self.professors[var] == self.professors[other_var] and slot == other_slot:
                return False

        # Constraint 3 (Exercise 3 - Tight Constraints):
        # In tight_constraints mode, C4_CS must be in Room_A AND Slot1_9AM
        if self.tight_constraints:
            if var == "C4_CS" and (slot != "Slot1_9AM" or room != "Room_A"):
                return False
            # Also force C1_Maths to Room_A Slot1_9AM (creates direct conflict!)
            if var == "C1_Maths" and (slot != "Slot1_9AM" or room != "Room_A"):
                return False

        return True

    def solve(self) -> Optional[Dict[str, Tuple[str, str]]]:
        """Backtracking CSP solver."""
        return self._backtrack({})

    def _backtrack(self, assignment: Dict[str, Tuple[str, str]]) -> Optional[Dict[str, Tuple[str, str]]]:
        if len(assignment) == len(self.variables):
            return assignment

        # Select unassigned variable
        unassigned = [v for v in self.variables if v not in assignment]
        var = unassigned[0]

        for value in self.domain:
            if self.is_valid_assignment(var, value, assignment):
                assignment[var] = value
                result = self._backtrack(assignment)
                if result is not None:
                    return result
                del assignment[var]

        return None


# ==============================================================================
# EXERCISES EXECUTION
# ==============================================================================

def run_exercise1():
    print("=" * 80)
    print("EXERCISE 1: FUZZY LOGIC SYSTEM FOR STUDENT PERFORMANCE")
    print("=" * 80)

    engine = StudentFuzzyEngine(strict_rules=False)

    test_cases = [
        ("Case A: Poor Attendance & Low Marks", 20.0, 30.0),
        ("Case B: Moderate Attendance & Average Marks", 60.0, 55.0),
        ("Case C: High Attendance & Excellent Marks", 90.0, 95.0),
        ("Case D: Low Attendance & Excellent Marks", 30.0, 90.0),
    ]

    for name, att, mrk in test_cases:
        score, cat, rule_outs = engine.evaluate(att, mrk)
        print(f"\n>>> {name}")
        print(f"  Inputs          : Attendance = {att}%, Marks = {mrk}/100")
        print(f"  Rule Firings    : {rule_outs}")
        print(f"  Defuzzified Score: {score:.2f}%")
        print(f"  Final Evaluation: {cat}")


def run_exercise2():
    print("\n" + "=" * 80)
    print("EXERCISE 2: TIMETABLE CONSTRAINT SATISFACTION PROBLEM (CSP)")
    print("=" * 80)

    csp = TimetableCSP(tight_constraints=False)
    solution = csp.solve()

    print("\n>>> Timetable Scheduling Results:")
    if solution:
        print(f"{'Course':<15} | {'Professor':<15} | {'Time Slot':<15} | {'Room':<10}")
        print("-" * 65)
        for var, (slot, room) in solution.items():
            prof = csp.professors[var]
            print(f"{var:<15} | {prof:<15} | {slot:<15} | {room:<10}")
        print("-" * 65)
        print("Status: VALID TIMETABLE GENERATED WITHOUT CONSTRAINT VIOLATIONS.")
    else:
        print("Status: NO VALID TIMETABLE FOUND (CONSTRAINTS UNSATISFIABLE).")


def run_exercise3():
    print("\n" + "=" * 80)
    print("EXERCISE 3: MODIFIED RULES & CONSTRAINTS COMPARISON")
    print("=" * 80)

    print("\n--- 1. Impact of Modified (Strict) Fuzzy Rules ---")
    std_engine = StudentFuzzyEngine(strict_rules=False)
    strict_engine = StudentFuzzyEngine(strict_rules=True)

    # Test student with 30% attendance and 90% marks
    att, mrk = 30.0, 90.0
    score_std, cat_std, _ = std_engine.evaluate(att, mrk)
    score_str, cat_str, _ = strict_engine.evaluate(att, mrk)

    print(f"Test Student: Attendance = {att}%, Marks = {mrk}/100")
    print(f"  Standard Rule System : Score = {score_std:.2f}% ({cat_std})")
    print(f"  Strict Rule System   : Score = {score_str:.2f}% ({cat_str})")
    print("  Observation: Strict rule penalizes low attendance heavily despite excellent marks!")

    print("\n--- 2. Impact of Modified (Tight) CSP Constraints ---")
    std_csp = TimetableCSP(tight_constraints=False)
    tight_csp = TimetableCSP(tight_constraints=True)

    sol_std = std_csp.solve()
    sol_tight = tight_csp.solve()

    print(f"  Standard CSP Solver : Solution Found? {'YES' if sol_std else 'NO'}")
    print(f"  Tight CSP Solver    : Solution Found? {'YES' if sol_tight else 'NO'}")
    print("  Observation: Forcing both C1_Maths and C4_CS into Room_A Slot1_9AM creates an impossible room conflict!")


def main():
    run_exercise1()
    run_exercise2()
    run_exercise3()


if __name__ == "__main__":
    main()
