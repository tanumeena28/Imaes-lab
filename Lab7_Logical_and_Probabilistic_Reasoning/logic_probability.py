"""
AI401 - Expert Systems Lab
Experiment 7 / Lab 7: Logical and Probabilistic Reasoning
Exercises 1 - 6: Propositional Logic, FOL, Event Probabilities, Conditional Probability, Bayes' Theorem & Visualization
"""

from typing import Dict, List, Tuple, Any
from PIL import Image, ImageDraw

# ==============================================================================
# EXERCISE 1: PROPOSITIONAL LOGIC
# ==============================================================================

def run_exercise1():
    print("=" * 80)
    print("EXERCISE 1: PROPOSITIONAL LOGIC (Truth Table Generation)")
    print("=" * 80)
    print("Statement: 'If it rains (R), then the road is wet (W)'  [R -> W]")
    print("Logical Formula: R -> W  <=>  (NOT R) OR W\n")

    print(f"{'Rain (R)':<12} | {'Wet Road (W)':<15} | {'NOT R':<10} | {'Implication (R -> W)':<20}")
    print("-" * 65)

    truth_values = [True, False]
    for R in truth_values:
        for W in truth_values:
            not_R = not R
            implication = (not R) or W
            print(f"{str(R):<12} | {str(W):<15} | {str(not_R):<10} | {str(implication):<20}")

    print("-" * 65)
    print("Verification: Implication is FALSE ONLY when R is True and W is False.\n")


# ==============================================================================
# EXERCISE 2: FIRST-ORDER LOGIC (FOL INFERENCE)
# ==============================================================================

class PredicateKB:
    """Simple First-Order Logic Knowledge Base supporting Universal Instantiation & Modus Ponens."""
    def __init__(self):
        self.facts: Dict[str, Set[str]] = {}  # predicate -> set of entities
        self.rules: List[Tuple[str, str]] = []  # (antecedent_pred, consequent_pred)

    def add_fact(self, predicate: str, entity: str):
        if predicate not in self.facts:
            self.facts[predicate] = set()
        self.facts[predicate].add(entity)

    def add_universal_rule(self, antecedent_pred: str, consequent_pred: str):
        # Represents ∀x (Antecedent(x) -> Consequent(x))
        self.rules.append((antecedent_pred, consequent_pred))

    def query_mortal(self, entity: str) -> bool:
        """Derives whether entity is mortal using FOL rules."""
        # Direct fact lookup
        if "Mortal" in self.facts and entity in self.facts["Mortal"]:
            return True

        # Rule resolution (Universal Instantiation + Modus Ponens)
        for ant, cons in self.rules:
            if cons == "Mortal":
                if ant in self.facts and entity in self.facts[ant]:
                    # Derived fact!
                    self.add_fact("Mortal", entity)
                    return True
        return False


def run_exercise2():
    print("=" * 80)
    print("EXERCISE 2: FIRST-ORDER LOGIC (FOL) INFERENCE")
    print("=" * 80)
    print("FOL Premises:")
    print("  1. Universal Rule : ∀x (Human(x) -> Mortal(x))  ['All humans are mortal']")
    print("  2. Ground Fact    : Human(Socrates)             ['Socrates is a human']")
    print("  3. Ground Fact    : Human(Plato)                ['Plato is a human']")
    print("  4. Ground Fact    : God(Zeus)                   ['Zeus is a god (not human)']\n")

    kb = PredicateKB()
    kb.add_universal_rule("Human", "Mortal")
    kb.add_fact("Human", "Socrates")
    kb.add_fact("Human", "Plato")
    kb.add_fact("God", "Zeus")

    test_entities = ["Socrates", "Plato", "Zeus"]
    for entity in test_entities:
        is_mortal = kb.query_mortal(entity)
        print(f"Query: Is {entity} mortal? -> {is_mortal}")


# ==============================================================================
# EXERCISE 3 & 4: PROBABILITY OF EVENTS & CONDITIONAL PROBABILITY
# ==============================================================================

def run_exercise3_and_4():
    print("\n" + "=" * 80)
    print("EXERCISE 3 & 4: PROBABILITY OF EVENTS & CONDITIONAL PROBABILITY")
    print("=" * 80)

    # Contingency Table for 100 Students:
    #                     Passed (P)    Failed (NOT P)   Total
    # Attended (A)            60             10            70
    # Did Not Attend (NOT A)  10             20            30
    # Total                   70             30           100

    N = 100
    n_A_and_P = 60
    n_A_and_notP = 10
    n_notA_and_P = 10
    n_notA_and_notP = 20

    # Marginal totals
    n_A = n_A_and_P + n_A_and_notP  # 70
    n_P = n_A_and_P + n_notA_and_P  # 70
    n_notA = N - n_A                 # 30

    print("Contingency Table (Dataset of 100 Students):")
    print(f"  Attended & Passed (A ∩ P)     : {n_A_and_P}")
    print(f"  Attended & Failed (A ∩ ¬P)    : {n_A_and_notP}")
    print(f"  Not Attended & Passed (¬A ∩ P): {n_notA_and_P}")
    print(f"  Not Attended & Failed (¬A ∩ ¬P): {n_notA_and_notP}\n")

    # 1. Individual Probabilities
    P_A = n_A / N
    P_P = n_P / N
    P_notA = n_notA / N

    print("--- Exercise 3: Individual, Joint & Union Probabilities ---")
    print(f"  P(A) [Prob of Attending]               = {P_A:.4f}")
    print(f"  P(P) [Prob of Passing]                 = {P_P:.4f}")

    # 2. Joint Probability P(A ∩ P)
    P_A_cap_P = n_A_and_P / N
    print(f"  P(A ∩ P) [Joint Prob: Attended & Passed] = {P_A_cap_P:.4f}")

    # 3. Union Probability P(A ∪ P) = P(A) + P(P) - P(A ∩ P)
    P_A_cup_P = P_A + P_P - P_A_cap_P
    print(f"  P(A ∪ P) [Union Prob: Attended OR Passed] = {P_A_cup_P:.4f}")

    # 4. Conditional Probabilities (Exercise 4)
    P_P_given_A = P_A_cap_P / P_A
    P_A_given_P = P_A_cap_P / P_P
    P_P_given_notA = (n_notA_and_P / N) / P_notA

    print("\n--- Exercise 4: Conditional Probabilities ---")
    print(f"  P(Pass | Attended)      = P(P ∩ A) / P(A)  = {P_P_given_A:.4f} ({P_P_given_A*100:.2f}%)")
    print(f"  P(Attended | Pass)      = P(A ∩ P) / P(P)  = {P_A_given_P:.4f} ({P_A_given_P*100:.2f}%)")
    print(f"  P(Pass | Did Not Attend) = P(P ∩ ¬A) / P(¬A) = {P_P_given_notA:.4f} ({P_P_given_notA*100:.2f}%)")


# ==============================================================================
# EXERCISE 5 & 6: BAYES' THEOREM & VISUALIZATION
# ==============================================================================

def calculate_bayes(prior_D: float, sensitivity: float, false_positive_rate: float) -> Tuple[float, float]:
    """
    Calculates posterior probability P(D | +) using Bayes' Theorem:
    P(D | +) = (P(+ | D) * P(D)) / P(+)
    where P(+) = P(+ | D)*P(D) + P(+ | ¬D)*P(¬D)
    """
    prior_notD = 1.0 - prior_D
    p_pos_given_D = sensitivity
    p_pos_given_notD = false_positive_rate

    p_pos = (p_pos_given_D * prior_D) + (p_pos_given_notD * prior_notD)
    posterior_D_given_pos = (p_pos_given_D * prior_D) / p_pos
    return posterior_D_given_pos, p_pos


def render_bayes_chart_pil(filename: str, p_prior: float, p_post1: float, p_post2: float, fp1: float, fp2: float):
    """Generates comparison bar chart for Bayes Theorem results using Pillow."""
    width, height = 800, 500
    img = Image.new('RGB', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(img)

    margin_left = 80
    margin_right = 50
    margin_top = 80
    margin_bottom = 80

    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    draw.text((width // 2 - 200, 25), "Exercise 6: Bayes' Theorem Posterior Probability", fill='#111111')

    # Draw grid
    for i in range(6):
        val = i / 5.0
        y_pixel = margin_top + plot_h - int(val * plot_h)
        draw.line([(margin_left, y_pixel), (margin_left + plot_w, y_pixel)], fill='#e0e0e0', width=1)
        draw.text((margin_left - 45, y_pixel - 8), f"{val:.1f}", fill='#333333')

    # Draw axes
    draw.line([(margin_left, margin_top), (margin_left, margin_top + plot_h)], fill='#222222', width=2)
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top + plot_h)], fill='#222222', width=2)

    categories = ["Prior P(D)", f"P(D|+) [FP={fp1*100:.0f}%]", f"P(D|+) [FP={fp2*100:.0f}%]"]
    vals = [p_prior, p_post1, p_post2]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

    col_w = plot_w // len(categories)
    bar_w = 60

    for idx, (cat, val, col) in enumerate(zip(categories, vals, colors)):
        center_x = margin_left + idx * col_w + col_w // 2
        bar_h = int(val * plot_h)

        x1 = center_x - bar_w // 2
        y1 = margin_top + plot_h - bar_h

        draw.rectangle([(x1, y1), (x1 + bar_w, margin_top + plot_h)], fill=col, outline='#111111')
        draw.text((x1 + 10, y1 - 20), f"{val*100:.1f}%", fill='#111111')
        draw.text((center_x - 55, margin_top + plot_h + 15), cat, fill='#111111')

    img.save(filename)
    print(f"PIL Bayes Chart saved to: {filename}", flush=True)


def run_exercise5_and_6():
    print("\n" + "=" * 80)
    print("EXERCISE 5 & 6: BAYES' THEOREM & VISUALIZATION")
    print("=" * 80)

    # Initial Case (Standard Medical Test)
    prior_D = 0.01          # 1% disease prevalence
    sensitivity = 0.95      # 95% true positive rate
    fp_rate_1 = 0.05        # 5% false positive rate

    posterior_1, p_pos_1 = calculate_bayes(prior_D, sensitivity, fp_rate_1)

    print("Scenario 1 (Standard Test with 5% False Positive Rate):")
    print(f"  Prior Disease Prevalence P(D)         = {prior_D:.4f} ({prior_D*100:.1f}%)")
    print(f"  Test Sensitivity P(+ | D)            = {sensitivity:.4f} ({sensitivity*100:.1f}%)")
    print(f"  False Positive Rate P(+ | ¬D)        = {fp_rate_1:.4f} ({fp_rate_1*100:.1f}%)")
    print(f"  Total Prob of Positive Test P(+)     = {p_pos_1:.4f}")
    print(f"  POSTERIOR P(D | +) [Prob of Disease]  = {posterior_1:.4f} ({posterior_1*100:.2f}%)\n")

    # Modified Case (Exercise 6 - High Accuracy Test with 1% False Positive Rate)
    fp_rate_2 = 0.01        # Reduced false positive rate to 1%
    posterior_2, p_pos_2 = calculate_bayes(prior_D, sensitivity, fp_rate_2)

    print("Scenario 2 (Modified High-Accuracy Test with 1% False Positive Rate):")
    print(f"  Prior Disease Prevalence P(D)         = {prior_D:.4f} ({prior_D*100:.1f}%)")
    print(f"  Test Sensitivity P(+ | D)            = {sensitivity:.4f} ({sensitivity*100:.1f}%)")
    print(f"  False Positive Rate P(+ | ¬D)        = {fp_rate_2:.4f} ({fp_rate_2*100:.1f}%)")
    print(f"  Total Prob of Positive Test P(+)     = {p_pos_2:.4f}")
    print(f"  POSTERIOR P(D | +) [Prob of Disease]  = {posterior_2:.4f} ({posterior_2*100:.2f}%)\n")

    print("Observation: Reducing False Positive Rate from 5% to 1% increases posterior probability from 16.10% to 48.97%!")

    # Render Chart
    render_bayes_chart_pil("exercise6_bayes_visualization.png", prior_D, posterior_1, posterior_2, fp_rate_1, fp_rate_2)


def main():
    run_exercise1()
    run_exercise2()
    run_exercise3_and_4()
    run_exercise5_and_6()


if __name__ == "__main__":
    main()
