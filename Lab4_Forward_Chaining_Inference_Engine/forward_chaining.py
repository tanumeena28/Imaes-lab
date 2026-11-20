"""
AI401 - Expert Systems Lab
Experiment 3 / Lab 4: Forward Chaining Inference Engine (Data-Driven Reasoning)
ZOOKEEPER Animal Identification System
"""

from typing import List, Set, Dict, Tuple, Optional
from enum import Enum

class ResolutionStrategy(Enum):
    FIRST_MATCH = "FIRST_MATCH"  # Sequential / Depth-First: Fire first rule in conflict set per cycle
    FIRE_ALL = "FIRE_ALL"        # Parallel / Breadth-First: Fire all rules in conflict set per cycle


class Rule:
    """
    Represents an IF-THEN Production Rule.
    - id: Unique rule identifier (e.g. 'R1')
    - conditions: List of condition strings. Supports 'NOT <fact>' for negation.
    - conclusion: Fact derived when the rule fires.
    - description: Human readable summary of the rule logic.
    """
    def __init__(self, rule_id: str, conditions: List[str], conclusion: str, description: str = ""):
        self.id = rule_id
        self.conditions = conditions
        self.conclusion = conclusion
        self.description = description or f"IF {' AND '.join(conditions)} THEN {conclusion}"

    def __repr__(self) -> str:
        return f"[{self.id}] IF {' AND '.join(self.conditions)} THEN {self.conclusion}"


class KnowledgeBase:
    """
    Manages the rule base and taxonomy abstraction levels for the ZOOKEEPER system.
    """
    def __init__(self):
        self.rules: List[Rule] = []
        self.taxonomic_levels: Dict[str, int] = {}
        self.known_species: Set[str] = set()

    def add_rule(self, rule: Rule):
        self.rules.append(rule)

    def set_taxonomy(self, levels: Dict[str, int], species: Set[str]):
        self.taxonomic_levels = levels
        self.known_species = species


def build_zookeeper_kb() -> KnowledgeBase:
    """
    Constructs the classic ZOOKEEPER production rule base with taxonomy support.
    """
    kb = KnowledgeBase()

    # Rule Base Definition
    rules = [
        # Mammal Identification Rules
        Rule("R1", ["has_hair"], "is_mammal", "Mammal rule 1: Animals with hair are mammals"),
        Rule("R2", ["gives_milk"], "is_mammal", "Mammal rule 2: Animals that give milk are mammals"),

        # Bird Identification Rules
        Rule("R3", ["has_feathers"], "is_bird", "Bird rule 1: Animals with feathers are birds"),
        Rule("R4", ["flies", "lays_eggs"], "is_bird", "Bird rule 2: Animals that fly and lay eggs are birds"),

        # Carnivore Identification Rules
        Rule("R5", ["eats_meat"], "is_carnivore", "Carnivore rule 1: Meat eaters are carnivores"),
        Rule("R6", ["has_pointed_teeth", "has_claws", "has_forward_eyes"], "is_carnivore", 
             "Carnivore rule 2: Pointed teeth, claws, and forward eyes indicate carnivore"),

        # Ungulate Identification Rules
        Rule("R7", ["is_mammal", "has_hoofs"], "is_ungulate", "Ungulate rule 1: Mammals with hoofs are ungulates"),
        Rule("R8", ["is_mammal", "chews_cud"], "is_ungulate", "Ungulate rule 2: Mammals that chew cud are ungulates"),

        # Specific Animal Species Rules
        Rule("R9", ["is_mammal", "is_carnivore", "tawny_color", "dark_spots"], "cheetah",
             "Cheetah rule: Tawny carnivore mammal with dark spots is a cheetah"),
        Rule("R10", ["is_mammal", "is_carnivore", "tawny_color", "black_stripes"], "tiger",
             "Tiger rule: Tawny carnivore mammal with black stripes is a tiger"),
        Rule("R11", ["is_ungulate", "long_neck", "long_legs", "dark_spots"], "giraffe",
             "Giraffe rule: Ungulate with long neck, long legs, and dark spots is a giraffe"),
        Rule("R12", ["is_ungulate", "black_stripes", "NOT is_carnivore"], "zebra",
             "Zebra rule: Ungulate with black stripes and not carnivore is a zebra"),
        Rule("R13", ["is_bird", "does_not_fly", "long_neck", "long_legs", "black_and_white_color"], "ostrich",
             "Ostrich rule: Flightless bird with long neck, long legs, and B&W feathers is an ostrich"),
        Rule("R14", ["is_bird", "does_not_fly", "swims", "black_and_white_color"], "penguin",
             "Penguin rule: Flightless swimming bird with B&W feathers is a penguin"),
        Rule("R15", ["is_bird", "good_flyer"], "albatross",
             "Albatross rule: Bird that is a good flyer is an albatross"),
    ]

    for r in rules:
        kb.add_rule(r)

    # Abstraction Level Taxonomy (0 = Perceptual Feature, 1 = Class, 2 = Sub-Class/Order, 3 = Final Species)
    taxonomy_levels = {
        "is_mammal": 1,
        "is_bird": 1,
        "is_carnivore": 2,
        "is_ungulate": 2,
        "cheetah": 3,
        "tiger": 3,
        "giraffe": 3,
        "zebra": 3,
        "ostrich": 3,
        "penguin": 3,
        "albatross": 3,
    }

    species_set = {"cheetah", "tiger", "giraffe", "zebra", "ostrich", "penguin", "albatross"}
    kb.set_taxonomy(taxonomy_levels, species_set)

    return kb


class CycleRecord:
    """
    Stores execution metrics and facts for a single cycle of forward chaining.
    """
    def __init__(self, cycle_num: int, working_memory_before: Set[str], conflict_set: List[Rule], fired_rules: List[Rule], new_facts: List[str]):
        self.cycle_num = cycle_num
        self.working_memory_before = set(working_memory_before)
        self.conflict_set = list(conflict_set)
        self.fired_rules = list(fired_rules)
        self.new_facts = list(new_facts)


class ForwardChainingEngine:
    """
    Forward Chaining Inference Engine implementing data-driven reasoning.
    Supports FIRST_MATCH (Sequential) and FIRE_ALL (Parallel) conflict resolution.
    """
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def is_rule_applicable(self, rule: Rule, wm: Set[str]) -> bool:
        """
        Evaluates rule conditions against working memory (WM):
        - Conclusion must NOT already exist in WM (refractoriness).
        - All positive conditions must be in WM.
        - All negated conditions ('NOT fact') must be absent from WM.
        """
        if rule.conclusion in wm:
            return False

        for condition in rule.conditions:
            if condition.startswith("NOT "):
                negated_fact = condition[4:].strip()
                if negated_fact in wm:
                    return False
            else:
                if condition not in wm:
                    return False

        return True

    def find_conflict_set(self, wm: Set[str]) -> List[Rule]:
        """Finds all rules satisfied by WM whose conclusions are new."""
        return [rule for rule in self.kb.rules if self.is_rule_applicable(rule, wm)]

    def run(self, initial_facts: Set[str], strategy: ResolutionStrategy = ResolutionStrategy.FIRST_MATCH) -> Tuple[Set[str], List[Rule], List[CycleRecord], Optional[str], Optional[Tuple[str, int]]]:
        """
        Executes forward chaining reasoning algorithm:
        1. Initialize Working Memory (WM) with initial facts.
        2. Repeat matching and rule firing until no rules can fire or species identified.
        3. Returns (final_wm, firing_sequence, cycle_records, identified_species, most_specific_class).
        """
        wm = set(initial_facts)
        firing_sequence: List[Rule] = []
        cycle_records: List[CycleRecord] = []
        cycle_num = 1

        identified_species: Optional[str] = None

        while True:
            # Check if species is already identified
            for fact in wm:
                if fact in self.kb.known_species:
                    identified_species = fact
                    break
            
            # Find conflict set
            conflict_set = self.find_conflict_set(wm)

            if not conflict_set:
                # Stop when no rules fire
                break

            rules_to_fire: List[Rule] = []
            if strategy == ResolutionStrategy.FIRST_MATCH:
                # Select first rule from conflict set
                rules_to_fire = [conflict_set[0]]
            elif strategy == ResolutionStrategy.FIRE_ALL:
                # Fire all rules in conflict set
                rules_to_fire = list(conflict_set)

            new_facts = []
            for rule in rules_to_fire:
                wm.add(rule.conclusion)
                firing_sequence.append(rule)
                new_facts.append(rule.conclusion)

            cycle_records.append(CycleRecord(cycle_num, wm - set(new_facts), conflict_set, rules_to_fire, new_facts))
            cycle_num += 1

            # Check again after firing cycle
            for fact in wm:
                if fact in self.kb.known_species:
                    identified_species = fact

        # Find most specific class if no species identified
        most_specific_class: Optional[Tuple[str, int]] = None
        if not identified_species:
            highest_level = -1
            best_class = None
            for fact in wm:
                level = self.kb.taxonomic_levels.get(fact, 0)
                if level > highest_level and fact not in self.kb.known_species:
                    highest_level = level
                    best_class = fact
            if best_class and highest_level > 0:
                most_specific_class = (best_class, highest_level)

        return wm, firing_sequence, cycle_records, identified_species, most_specific_class


def format_cycle_report(records: List[CycleRecord], strategy: ResolutionStrategy):
    """Prints a detailed cycle-by-cycle execution report."""
    print(f"\n--- Strategy: {strategy.value} ---")
    for rec in records:
        print(f"Cycle {rec.cycle_num}:")
        print(f"  WM Before     : {sorted(list(rec.working_memory_before))}")
        print(f"  Conflict Set  : {[r.id for r in rec.conflict_set]}")
        print(f"  Fired Rule(s) : {[r.id for r in rec.fired_rules]}")
        print(f"  New Fact(s)   : {rec.new_facts}")


def run_exercise1():
    print("=" * 80)
    print("EXERCISE 1: IDENTIFYING TIGER, GIRAFFE, AND ZEBRA")
    print("=" * 80)

    kb = build_zookeeper_kb()
    engine = ForwardChainingEngine(kb)

    test_cases = [
        ("Tiger Test", {"has_hair", "eats_meat", "tawny_color", "black_stripes"}),
        ("Giraffe Test", {"gives_milk", "has_hoofs", "long_neck", "long_legs", "dark_spots"}),
        ("Zebra Test", {"has_hair", "chews_cud", "black_stripes", "NOT is_carnivore"}),
    ]

    for name, facts in test_cases:
        print(f"\n>>> Running Test Case: {name}")
        print(f"Initial Observed Features (WM): {sorted(list(facts))}")
        
        final_wm, seq, records, species, _ = engine.run(facts, ResolutionStrategy.FIRST_MATCH)
        format_cycle_report(records, ResolutionStrategy.FIRST_MATCH)

        print("\nResults:")
        print(f"  Firing Sequence : {' -> '.join([r.id for r in seq]) if seq else 'None'}")
        print(f"  Final Working Memory: {sorted(list(final_wm))}")
        print(f"  Identified Animal   : {species if species else 'Unidentified'}")


def run_exercise2():
    print("\n" + "=" * 80)
    print("EXERCISE 2: REPORTING MOST SPECIFIC ESTABLISHED CLASS (INCOMPLETE DATA)")
    print("=" * 80)

    kb = build_zookeeper_kb()
    engine = ForwardChainingEngine(kb)

    test_cases = [
        ("Incomplete Carnivore Facts", {"has_hair", "eats_meat"}),
        ("Incomplete Mammal Facts", {"gives_milk"}),
        ("Unknown / Unmatched Features", {"green_skin", "small_tail"}),
    ]

    for name, facts in test_cases:
        print(f"\n>>> Running Test Case: {name}")
        print(f"Initial Observed Features (WM): {sorted(list(facts))}")

        final_wm, seq, records, species, most_specific = engine.run(facts, ResolutionStrategy.FIRST_MATCH)
        format_cycle_report(records, ResolutionStrategy.FIRST_MATCH)

        print("\nResults:")
        print(f"  Firing Sequence     : {' -> '.join([r.id for r in seq]) if seq else 'None'}")
        print(f"  Final Working Memory: {sorted(list(final_wm))}")
        if species:
            print(f"  Identified Animal   : {species}")
        else:
            print("  Identified Animal   : NONE (No identification rule satisfied)")
            if most_specific:
                cls_name, level = most_specific
                level_str = "Class Level (1)" if level == 1 else "Order Level (2)"
                print(f"  Most Specific Class : '{cls_name}' ({level_str})")
            else:
                print("  Most Specific Class : NONE (No abstraction rules fired)")


def run_exercise3():
    print("\n" + "=" * 80)
    print("EXERCISE 3: COMPARISON OF FIRST_MATCH VS FIRE_ALL STRATEGIES")
    print("=" * 80)

    kb = build_zookeeper_kb()
    engine = ForwardChainingEngine(kb)

    # Case requiring multiple rules to fire in parallel
    test_facts = {"has_hair", "has_pointed_teeth", "has_claws", "has_forward_eyes", "tawny_color", "black_stripes"}

    print(f"Observed Features: {sorted(list(test_facts))}\n")

    # Strategy 1: FIRST_MATCH
    wm1, seq1, recs1, sp1, _ = engine.run(test_facts, ResolutionStrategy.FIRST_MATCH)
    print("--- 1. FIRST_MATCH Strategy (Single Rule per Cycle) ---")
    format_cycle_report(recs1, ResolutionStrategy.FIRST_MATCH)
    print(f"Total Cycles: {len(recs1)} | Firing Sequence: {' -> '.join([r.id for r in seq1])} | Result: {sp1}")

    # Strategy 2: FIRE_ALL
    wm2, seq2, recs2, sp2, _ = engine.run(test_facts, ResolutionStrategy.FIRE_ALL)
    print("\n--- 2. FIRE_ALL Strategy (All Applicable Rules per Cycle) ---")
    format_cycle_report(recs2, ResolutionStrategy.FIRE_ALL)
    print(f"Total Cycles: {len(recs2)} | Firing Sequence: [{', '.join([r.id for r in seq2])}] | Result: {sp2}")

    # Comparison Summary Table
    print("\n" + "-" * 80)
    print("STRATEGY COMPARISON SUMMARY")
    print("-" * 80)
    print(f"{'Metric':<30} | {'FIRST_MATCH (Sequential)':<25} | {'FIRE_ALL (Parallel)':<25}")
    print("-" * 80)
    print(f"{'Total Cycles Elapsed':<30} | {len(recs1):<25} | {len(recs2):<25}")
    print(f"{'Total Rules Fired':<30} | {len(seq1):<25} | {len(seq2):<25}")
    print(f"{'Firing Sequence':<30} | {' -> '.join([r.id for r in seq1]):<25} | {'[' + ', '.join([r.id for r in seq2]) + ']':<25}")
    print(f"{'Final Working Memory Size':<30} | {len(wm1):<25} | {len(wm2):<25}")
    print(f"{'Identified Animal':<30} | {str(sp1):<25} | {str(sp2):<25}")
    print("-" * 80)


def main():
    run_exercise1()
    run_exercise2()
    run_exercise3()


if __name__ == "__main__":
    main()
