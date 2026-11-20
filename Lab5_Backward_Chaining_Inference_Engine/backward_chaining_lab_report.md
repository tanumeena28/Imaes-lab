# AI401 — Expert Systems Lab
## Experiment 4 / Lab 5: Backward Chaining Inference Engine with Askable Facts (Goal-Driven Reasoning)

---

### **Aim**
To implement a backward chaining inference engine which uses goal-driven reasoning for car-fault diagnosis using askable facts, and to analyze hypothesis ordering impacts and the 'WHY' explanation facility.

---

### **Theory**

#### **1. Backward Chaining & Goal-Driven Reasoning**
**Backward chaining** is a goal-driven inference technique. Unlike forward chaining (which starts with known facts and derives everything possible), backward chaining starts from a **target hypothesis/goal** (e.g., `starter_motor_fault`) and works backward:
1. It identifies production rules whose **THEN-conclusions** match the target goal.
2. It evaluates the **IF-conditions** of those rules as sub-goals.
3. If an IF-condition is unknown, it recursively checks if another rule can derive it or if it is an **askable fact**.

```
Target Goal (Hypothesis: starter_motor_fault)
                      |
           Rule R1: IF clicking_sound AND NOT engine_cranks
                      |
         +------------+------------+
         |                         |
Sub-Goal 1: clicking_sound   Sub-Goal 2: NOT engine_cranks
  (Askable Fact -> Ask User)   (Askable Fact -> Ask User)
```

#### **2. Askable Facts**
In diagnostic expert systems, many primitive observations cannot be derived by rules (e.g., whether headlights are dim or if a clicking sound occurs). These are designated as **askable facts**. The engine interactively prompts the user for information only when required to prove an active goal.

#### **3. The 'WHY' Explanation Facility**
A critical component of expert systems is transparency. When the engine prompts the user for an askable fact, the user may enter **"WHY"**. The system responds by displaying:
- The current target hypothesis being investigated.
- The active rule being evaluated.
- The exact reason why the asked fact is required to satisfy the rule.

#### **4. Goal Ordering Impact**
Because reasoning is goal-driven, the order in which candidate hypotheses are evaluated directly dictates the sequence of questions asked to the user. Evaluated goals cache facts in Working Memory (WM), eliminating redundant questions for subsequent hypotheses.

---

### **Algorithm**

#### **Goal-Driven Backward Chaining Algorithm**
```
FUNCTION EvaluateGoal(Goal, RuleBase, AskableFacts, WM, ReasoningStack):
  1. IF Goal is in WM THEN RETURN WM[Goal]
  2. MatchingRules <- Find rules in RuleBase where Rule.conclusion == Goal
  3. FOR EACH Rule in MatchingRules:
       Push (Rule, Goal) to ReasoningStack
       RuleSatisfied <- TRUE
       FOR EACH Condition in Rule.conditions:
         IF NOT EvaluateGoal(Condition, RuleBase, AskableFacts, WM, ReasoningStack) THEN
           RuleSatisfied <- FALSE
           BREAK
       Pop ReasoningStack
       IF RuleSatisfied THEN
         WM[Goal] <- TRUE
         RETURN TRUE
  4. IF Goal is in AskableFacts AND Goal not in WM THEN
       Response <- PromptUser(AskableFacts[Goal])
       IF Response == "WHY" THEN
         DisplayExplanation(ReasoningStack)
         Re-prompt User
       WM[Goal] <- (Response == "YES")
       RETURN WM[Goal]
  5. WM[Goal] <- FALSE
  6. RETURN FALSE
```

---

### **Knowledge Base Specification (Car Fault Diagnosis)**

| Rule ID | IF Conditions | THEN Conclusion | Description |
| :--- | :--- | :--- | :--- |
| **R1** | `clicking_sound`, `NOT engine_cranks` | `starter_motor_fault` | Clicking sound without engine cranking indicates starter motor failure. |
| **R2** | `NOT lights_working`, `NOT engine_cranks` | `dead_battery` | No lights and no engine cranking indicates a dead battery. |
| **R3** | `engine_cranks`, `NOT engine_starts`, `fuel_gauge_empty` | `empty_fuel_tank` | Engine cranks but won't start and fuel gauge is empty. |
| **R4** | `engine_cranks`, `NOT engine_starts`, `spark_plug_dirty` | `bad_spark_plug` | Engine cranks but won't start and spark plug is dirty. |
| **R5** | `battery_drains_frequently`, `dim_headlights` | `alternator_failure` | Battery drains frequently and headlights are dim. |

#### **Askable Facts Table**:
- `clicking_sound`: "Is there a clicking sound when turning the ignition key?"
- `engine_cranks`: "Does the engine crank over when turning the key?"
- `lights_working`: "Are the headlights and dashboard lights working normally?"
- `engine_starts`: "Does the engine start up successfully?"
- `fuel_gauge_empty`: "Is the fuel gauge pointing to empty (E)?"
- `spark_plug_dirty`: "Are the spark plugs dirty, oily, or fouled?"
- `battery_drains_frequently`: "Does the car battery drain frequently overnight?"
- `dim_headlights`: "Are the headlights dim or flickering while driving?"

---

### **Experimental Implementation & Results**

#### **Exercise 1: Starter Motor Fault Diagnosis**
- **Test Objective**: Verify diagnosis of starter motor fault using `clicking_sound` and `engine_cranks`.
- **Target Hypothesis Evaluated**: `starter_motor_fault` (Rule R1)
- **Execution Log**:
  - `[ASK]` Is there a clicking sound when turning the ignition key? $\rightarrow$ User: **`yes`**
  - `[ASK]` Does the engine crank over when turning the key? $\rightarrow$ User: **`no`**
- **Inference Chain**:
  1. $R_1$ condition `clicking_sound` = `True` (User input).
  2. $R_1$ condition `NOT engine_cranks` = `True` (`engine_cranks` = `False` from user input).
  3. $R_1$ fires $\rightarrow$ `starter_motor_fault` = `True`.
- **Outcome**: **`starter_motor_fault` successfully confirmed**.

---

#### **Exercise 2: Impact of Hypothesis Ordering**

##### **Order A: `[starter_motor_fault, empty_fuel_tank, dead_battery]`**
- Evaluates `starter_motor_fault` first.
- **Questions Asked**:
  1. `clicking_sound`? $\rightarrow$ `yes`
  2. `engine_cranks`? $\rightarrow$ `no`
- **Result**: `starter_motor_fault` confirmed immediately after **2 questions**.

##### **Order B: `[empty_fuel_tank, starter_motor_fault, dead_battery]`**
- Evaluates `empty_fuel_tank` first (Rule R3).
- **Questions Asked**:
  1. `engine_cranks`? $\rightarrow$ `no` (Fails R3 condition `engine_cranks` $\rightarrow$ Hypothesis `empty_fuel_tank` rejected!).
  2. Evaluates `starter_motor_fault` (Rule R1):
     - `clicking_sound`? $\rightarrow$ `yes`
     - `engine_cranks`? $\rightarrow$ Cached from WM (`False`), so `NOT engine_cranks` holds!
- **Observation**: Hypothesis ordering changes question sequence. Evaluated facts are cached in Working Memory, preventing duplicate questions.

---

#### **Exercise 3: 'WHY' Explanation Facility**

- **Scenario**: User inputs `'why'` when asked about `clicking_sound`.
- **System Response**:
  ```text
  ============================================================
    [EXPLANATION FACILITY — 'WHY' RESPONSE]
  ============================================================
    Target Hypothesis Being Evaluated : 'starter_motor_fault'
    Current Rule Evaluated            : [R1] IF clicking_sound AND NOT engine_cranks THEN starter_motor_fault
    Rule Description                  : Starter Motor Rule: Clicking sound without engine cranking indicates starter motor failure.
    Reason For Question               : To determine if condition 'clicking_sound' is satisfied.
  ============================================================
  ```
- **Observation**: The engine clearly articulates the goal hierarchy and rule context behind every question asked.

---

### **Key Observations & Conclusion**

1. **Goal Efficiency**: Backward chaining asks *only* relevant questions required to verify active hypotheses, unlike forward chaining which requires all facts up front.
2. **Fact Caching**: Working Memory caches user responses so no question is ever asked twice.
3. **Explanation Transparency**: The 'WHY' facility increases trust by detailing active rules and target hypotheses during execution.
4. **Conclusion**: The Backward Chaining Expert System for car fault diagnosis was successfully built, verified, and benchmarked across all three exercises.
