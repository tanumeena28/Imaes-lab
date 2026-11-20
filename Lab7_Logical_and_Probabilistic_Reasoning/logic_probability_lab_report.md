# AI401 — Expert Systems Lab
## Experiment 7 / Lab 7: Logical and Probabilistic Reasoning

---

### **Aim**
To implement basic Propositional Logic, First-Order Logic (FOL) inference, event probabilities, conditional probability, Bayes' Theorem, and probabilistic data visualization in Python.

---

### **Theory**

#### **1. Propositional Logic**
Propositional logic evaluates truth values of atomic statements connected by logical operators ($\land, \lor, \neg, \rightarrow$).
The implication $R \rightarrow W$ ("If it rains, then the road is wet") is logically equivalent to $\neg R \lor W$.

#### **2. First-Order Logic (FOL)**
FOL extends propositional logic by introducing **predicates**, **entities**, and **quantifiers** ($\forall, \exists$).
- **Rule**: $\forall x \, (\text{Human}(x) \rightarrow \text{Mortal}(x))$
- **Fact**: $\text{Human}(\text{Socrates})$
- **Inference Mechanism**: **Universal Instantiation** substitutes $x = \text{Socrates}$, and **Modus Ponens** derives $\text{Mortal}(\text{Socrates})$.

#### **3. Probability Theory & Contingency Tables**
- **Marginal Probability**: $P(A) = \frac{N(A)}{N_{\text{total}}}$
- **Joint Probability**: $P(A \cap P) = \frac{N(A \cap P)}{N_{\text{total}}}$
- **Union Probability**: $P(A \cup P) = P(A) + P(P) - P(A \cap P)$
- **Conditional Probability**: $P(P \mid A) = \frac{P(P \cap A)}{P(A)}$

#### **4. Bayes' Theorem**
Bayes' Theorem updates the prior probability of an event upon receiving new evidence:
$$P(D \mid +) = \frac{P(+ \mid D) \cdot P(D)}{P(+)} = \frac{P(+ \mid D) \cdot P(D)}{P(+ \mid D) \cdot P(D) + P(+ \mid \neg D) \cdot P(\neg D)}$$

---

### **Experimental Implementation & Results**

#### **Exercise 1: Propositional Logic Truth Table**

Truth table for implication $R \rightarrow W \equiv (\neg R) \lor W$:

| Rain ($R$) | Wet Road ($W$) | $\neg R$ | Implication ($R \rightarrow W$) | Verification |
| :--- | :--- | :--- | :--- | :--- |
| `True` | `True` | `False` | **`True`** | Valid |
| `True` | `False` | `False` | **`False`** | Counterexample (Rain without wet road) |
| `False` | `True` | `True` | **`True`** | Vacuously True |
| `False` | `False` | `True` | **`True`** | Vacuously True |

---

#### **Exercise 2: First-Order Logic Inference**

- **Premises**:
  1. $\forall x \, (\text{Human}(x) \rightarrow \text{Mortal}(x))$
  2. $\text{Human}(\text{Socrates})$
  3. $\text{Human}(\text{Plato})$
  4. $\text{God}(\text{Zeus})$
- **Deduction Results**:
  - `Query: Is Socrates mortal?` $\rightarrow$ **`True`** (Derived via Universal Rule)
  - `Query: Is Plato mortal?` $\rightarrow$ **`True`** (Derived via Universal Rule)
  - `Query: Is Zeus mortal?` $\rightarrow$ **`False`** (Zeus is not human)

---

#### **Exercises 3 & 4: Probability Calculations (Dataset of 100 Students)**

##### **Contingency Table**:
- $N = 100$
- Attended & Passed ($A \cap P$): 60
- Attended & Failed ($A \cap \neg P$): 10
- Not Attended & Passed ($\neg A \cap P$): 10
- Not Attended & Failed ($\neg A \cap \neg P$): 20

##### **Calculated Metrics**:
1. **Marginal Probabilities**:
   - $P(A) = \frac{70}{100} = \mathbf{0.7000}$ (70.0% Attendance Rate)
   - $P(P) = \frac{70}{100} = \mathbf{0.7000}$ (70.0% Pass Rate)
2. **Joint Probability**:
   - $P(A \cap P) = \frac{60}{100} = \mathbf{0.6000}$ (60.0% Attended AND Passed)
3. **Union Probability**:
   - $P(A \cup P) = 0.70 + 0.70 - 0.60 = \mathbf{0.8000}$ (80.0% Attended OR Passed)
4. **Conditional Probabilities**:
   - $P(P \mid A) = \frac{0.60}{0.70} = \mathbf{0.8571}$ (**85.71%** pass rate among attendees)
   - $P(A \mid P) = \frac{0.60}{0.70} = \mathbf{0.8571}$ (**85.71%** of passing students attended)
   - $P(P \mid \neg A) = \frac{0.10}{0.30} = \mathbf{0.3333}$ (**33.33%** pass rate among non-attendees)

---

#### **Exercises 5 & 6: Bayes' Theorem & Visualization**

##### **Scenario 1 (Standard Medical Test)**:
- Prior Prevalence $P(D) = 0.01$ (1%)
- Sensitivity $P(+ \mid D) = 0.95$ (95%)
- False Positive Rate $P(+ \mid \neg D) = 0.05$ (5%)
- **Calculation**:
  $$P(D \mid +) = \frac{0.95 \times 0.01}{(0.95 \times 0.01) + (0.05 \times 0.99)} = \frac{0.0095}{0.0590} = \mathbf{0.1610} \text{ (16.10\%)}$$

##### **Scenario 2 (Modified High-Accuracy Test — Exercise 6)**:
- Reduced False Positive Rate $P(+ \mid \neg D) = 0.01$ (1%)
- **Calculation**:
  $$P(D \mid +) = \frac{0.95 \times 0.01}{(0.95 \times 0.01) + (0.01 \times 0.99)} = \frac{0.0095}{0.0194} = \mathbf{0.4897} \text{ (48.97\%)}$$

##### **Visualization Output**:
The bar chart [`exercise6_bayes_visualization.png`](file:///c:/Users/Tanu%20Meena/OneDrive/Desktop/Image/Lab7_Logical_and_Probabilistic_Reasoning/exercise6_bayes_visualization.png) clearly illustrates how reducing false positives from 5% to 1% increases posterior certainty from 16.1% to 48.97%.

---

### **Conclusion**
Lab 7 successfully implemented Propositional Truth Tables, First-Order Inference, Contingency Probability Analysis, and Bayes' Theorem. The results highlight how false positive rates dramatically alter posterior probability under low prior prevalence.
