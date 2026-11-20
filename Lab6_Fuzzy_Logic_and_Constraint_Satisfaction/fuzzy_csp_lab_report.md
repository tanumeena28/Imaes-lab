# AI401 — Expert Systems Lab
## Experiment 6 / Lab 6: Fuzzy Logic and Constraint Satisfaction Problems (CSP)

---

### **Aim**
To implement a fuzzy logic inference system to evaluate student performance based on attendance and marks, and to model and solve a timetable scheduling problem using Constraint Satisfaction Problem (CSP) techniques.

---

### **Theory**

#### **1. Fuzzy Logic System**
Unlike crisp Boolean logic where a statement is strictly 0 (False) or 1 (True), **Fuzzy Logic** handles partial truth values between 0.0 and 1.0. This models human vagueness in linguistic terms such as *"Low Attendance"* or *"Excellent Marks"*.

```
   Crisp Inputs             Fuzzification             Fuzzy Inference           Defuzzification
(Attendance, Marks) ----> Membership Functions ----> Rule Base (Mamdani) ----> Centroid Method ----> Crisp Score
```

##### **Core Steps**:
1. **Fuzzification**: Convert crisp values into fuzzy membership degrees $\mu(x) \in [0, 1]$ using Triangular and Trapezoidal membership functions.
2. **Fuzzy Rule Evaluation**: Evaluate IF-THEN rules using Min-Max Mamdani Inference:
   - **AND ($\land$)**: $\min(\mu_A(x), \mu_B(y))$
   - **OR ($\lor$)**: $\max(\mu_A(x), \mu_B(y))$
3. **Defuzzification**: Convert the aggregated fuzzy output set back into a single crisp value using the **Centroid (Center of Gravity)** method:
   $$\text{Crisp Score} = \frac{\sum y \cdot \mu_{\text{aggregated}}(y)}{\sum \mu_{\text{aggregated}}(y)}$$

---

#### **2. Constraint Satisfaction Problem (CSP)**
A **Constraint Satisfaction Problem (CSP)** is defined by a triple $\langle V, D, C \rangle$:
- **Variables ($V$)**: Objects needing assignment (e.g., Courses $C_1, C_2, C_3, C_4$).
- **Domains ($D$)**: Set of possible values for each variable (e.g., Pairs of $(\text{Slot}, \text{Room})$).
- **Constraints ($C$)**: Rules restricting combinations of values.

##### **Timetable Constraints**:
1. **Room Conflict Constraint**: No two courses can be scheduled in the *same room* at the *same time slot*.
2. **Professor Conflict Constraint**: The *same professor* cannot teach two courses in the *same time slot*.

---

### **Knowledge Base & Constraint Definitions**

#### **Part A: Fuzzy Logic Membership Sets**
- **Attendance ($[0, 100\%]$)**:
  - `Low`: Trapezoid(0, 0, 30, 55)
  - `Medium`: Triangle(35, 60, 85)
  - `High`: Trapezoid(65, 85, 100, 100)
- **Marks ($[0, 100]$)**:
  - `Poor`: Trapezoid(0, 0, 30, 50)
  - `Average`: Triangle(35, 55, 75)
  - `Excellent`: Trapezoid(65, 85, 100, 100)

#### **Fuzzy Rule Base**:
- **R1**: IF `Attendance` is `Low` OR `Marks` is `Poor` THEN `Performance` is `Unsatisfactory`
- **R2**: IF `Attendance` is `Medium` AND `Marks` is `Average` THEN `Performance` is `Satisfactory`
- **R3**: IF `Attendance` is `High` AND `Marks` is `Excellent` THEN `Performance` is `Outstanding`
- **R4**: IF `Attendance` is `High` AND `Marks` is `Average` THEN `Performance` is `Satisfactory`
- **R5**: IF `Attendance` is `Low` AND `Marks` is `Excellent` THEN `Performance` is `Satisfactory`

---

### **Experimental Results & Analysis**

#### **Exercise 1: Fuzzy Student Performance Evaluation**

| Test Case | Inputs (Attendance, Marks) | Rule Firing Strengths | Defuzzified Score | Evaluation |
| :--- | :--- | :--- | :--- | :--- |
| **Case A** | `(20.0%, 30.0/100)` | `Unsat: 1.0, Sat: 0.0, Out: 0.0` | **18.23%** | **Unsatisfactory** |
| **Case B** | `(60.0%, 55.0/100)` | `Unsat: 0.0, Sat: 1.0, Out: 0.0` | **55.00%** | **Satisfactory** |
| **Case C** | `(90.0%, 95.0/100)` | `Unsat: 0.0, Sat: 0.0, Out: 1.0` | **86.57%** | **Outstanding** |
| **Case D** | `(30.0%, 90.0/100)` | `Unsat: 1.0, Sat: 1.0, Out: 0.0` | **31.53%** | **Unsatisfactory** |

---

#### **Exercise 2: Timetable CSP Solution**

Using Backtracking Search over domains $(\text{Slot}, \text{Room})$:

```text
Course          | Professor       | Time Slot       | Room      
-----------------------------------------------------------------
C1_Maths        | Prof_Smith      | Slot1_9AM       | Room_A    
C2_Physics      | Prof_Smith      | Slot2_10AM      | Room_A    
C3_Chem         | Prof_Jones      | Slot1_9AM       | Room_B    
C4_CS           | Prof_Alan       | Slot2_10AM      | Room_B    
-----------------------------------------------------------------
Status: VALID TIMETABLE GENERATED WITHOUT CONSTRAINT VIOLATIONS.
```

##### **Constraint Check**:
- `C1_Maths` and `C3_Chem` are both in `Slot1_9AM`, but in different rooms (`Room_A` vs `Room_B`) $\rightarrow$ **No Room Conflict**.
- `C1_Maths` and `C2_Physics` are both taught by `Prof_Smith`, but in different slots (`Slot1_9AM` vs `Slot2_10AM`) $\rightarrow$ **No Professor Conflict**.

---

#### **Exercise 3: Impact of Modified Rules & Constraints**

##### **1. Modified Fuzzy Rules (Strict Attendance Penalty)**
- When rules were modified to heavily penalize low attendance (`IF Attendance is Low THEN Performance is ALWAYS Unsatisfactory`):
- For a student with `Attendance = 30%` and `Marks = 90`:
  - **Standard System**: Score = `31.53%` (Unsatisfactory)
  - **Strict System**: Score = `18.23%` (Heavily Unsatisfactory)

##### **2. Modified Tight CSP Constraints**
- Adding a tight constraint forcing both `C1_Maths` and `C4_CS` into `(Slot1_9AM, Room_A)`:
  - **Standard CSP**: Solution Found = `YES`
  - **Tight CSP**: Solution Found = `NO` (Unsatisfiable constraint conflict).

---

### **Conclusion**
The Fuzzy Logic Student Performance System and Timetable CSP Solver were successfully created and benchmarked. The fuzzy logic system smoothly interpolated non-linear human evaluation metrics, while the CSP solver efficiently generated conflict-free schedules using backtracking search. Modifying rules and constraints demonstrated the sensitivity of expert system outputs to domain knowledge tuning.
