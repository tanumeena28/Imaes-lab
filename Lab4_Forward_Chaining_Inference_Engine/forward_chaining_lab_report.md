# AI401 — Expert Systems Lab
## Experiment 3 / Lab 4: Forward Chaining Inference Engine (Data-Driven Reasoning)

---

### **Aim**
To implement a forward chaining inference engine and use it to identify an animal from observed features, in the manner of the classic **ZOOKEEPER** system, and to evaluate conflict resolution strategies and fallback mechanisms for incomplete knowledge.

---

### **Theory**

#### **1. Forward Chaining & Data-Driven Reasoning**
**Forward chaining** is a data-driven inference technique that begins with a collection of known facts in **Working Memory (WM)** and iteratively applies production rules (**IF condition THEN conclusion**) to derive new facts. 

Reasoning moves forward from evidence (percepts/observations) toward abstraction levels and final conclusions (goals). This approach is particularly suitable for monitoring, diagnostic interpretation, and classification tasks (such as the classic ZOOKEEPER expert system) where multiple conclusions may naturally follow from initial observations.

```
+------------------+      Matches Rules      +-------------------+
|  Working Memory  | ----------------------> |   Conflict Set    |
| (Observed Facts) |                         | (Eligible Rules)  |
+------------------+                         +-------------------+
         ^                                             |
         |                                             | Selects & Fires
         |           Adds New Fact(s)                  v
         +------------------------------------- +--------------+
                                                | Fired Rule   |
                                                +--------------+
```

#### **2. The Recognize-Act Cycle & Refractoriness**
The core control loop of a production system operates via the **Recognize-Act Cycle**:
1. **Match Phase**: Evaluate rule conditions against current facts in WM to construct the **Conflict Set**.
2. **Conflict Resolution Phase**: Select one or more rules from the conflict set according to a chosen strategy.
3. **Act (Fire) Phase**: Execute the selected rule(s), adding their conclusion(s) to WM and recording rule identifiers.

To prevent infinite loops, the engine enforces **refractoriness**: a rule whose conclusion is already present in Working Memory will not fire again.

#### **3. Conflict Resolution Strategies**
Two primary strategies govern rule selection during forward chaining:
- **First-Match Strategy (`FIRST_MATCH`)**: Sequential / Depth-First approach. In each cycle, only the *first* eligible rule in the conflict set fires. Working memory is immediately updated, altering the conflict set for subsequent cycles.
- **Fire-All Strategy (`FIRE_ALL`)**: Parallel / Breadth-First approach. In each cycle, *all* eligible rules in the conflict set fire simultaneously. This minimizes cycle count and expands working memory rapidly.

#### **4. Taxonomic Abstraction & Fallback Reasoning**
Knowledge in domain systems like ZOOKEEPER forms an **abstraction hierarchy**:
- **Level 0 (Perceptual Features)**: `has_hair`, `eats_meat`, `tawny_color`, `black_stripes`
- **Level 1 (Class Abstraction)**: `is_mammal`, `is_bird`
- **Level 2 (Order / Sub-Class Abstraction)**: `is_carnivore`, `is_ungulate`
- **Level 3 (Final Species Identification)**: `tiger`, `cheetah`, `giraffe`, `zebra`, `ostrich`, `penguin`, `albatross`

When observed facts are insufficient to reach Level 3 (a specific animal species), a robust engine falls back to reporting the **most specific class established** (e.g., Level 2 `is_carnivore`), indicating how far reasoning progressed before halting.

---

### **Algorithm**

#### **Forward Chaining Inference Algorithm**
```
INPUT  : Initial Fact Set F_0, Rule Base KB, Strategy S
OUTPUT : Final Working Memory WM, Firing Sequence R_seq, Identified Animal / Most Specific Class

1. Initialize Working Memory: WM <- F_0
2. Initialize Firing Sequence: R_seq <- []
3. Loop Cycle c = 1, 2, ...:
   a. ConflictSet <- { r in KB | r.conditions satisfied by WM AND r.conclusion not in WM }
   b. IF ConflictSet is empty THEN Exit Loop
   c. IF S == FIRST_MATCH THEN
         FireRules <- [ ConflictSet[0] ]
      ELSE IF S == FIRE_ALL THEN
         FireRules <- ConflictSet
   d. FOR EACH rule r in FireRules:
         WM <- WM U { r.conclusion }
         R_seq <- R_seq + [ r.id ]
4. Check WM for identified species (Taxonomy Level 3).
5. IF species found:
      Report Identified Animal
   ELSE:
      Find highest taxonomy level L present in WM
      Report Most Specific Established Class at Level L
```

---

### **Knowledge Base Specification (ZOOKEEPER)**

| Rule ID | IF Conditions | THEN Conclusion | Taxonomy Level |
| :--- | :--- | :--- | :--- |
| **R1** | `has_hair` | `is_mammal` | Level 1 (Class) |
| **R2** | `gives_milk` | `is_mammal` | Level 1 (Class) |
| **R3** | `has_feathers` | `is_bird` | Level 1 (Class) |
| **R4** | `flies`, `lays_eggs` | `is_bird` | Level 1 (Class) |
| **R5** | `eats_meat` | `is_carnivore` | Level 2 (Order) |
| **R6** | `has_pointed_teeth`, `has_claws`, `has_forward_eyes` | `is_carnivore` | Level 2 (Order) |
| **R7** | `is_mammal`, `has_hoofs` | `is_ungulate` | Level 2 (Order) |
| **R8** | `is_mammal`, `chews_cud` | `is_ungulate` | Level 2 (Order) |
| **R9** | `is_mammal`, `is_carnivore`, `tawny_color`, `dark_spots` | `cheetah` | Level 3 (Species) |
| **R10** | `is_mammal`, `is_carnivore`, `tawny_color`, `black_stripes` | `tiger` | Level 3 (Species) |
| **R11** | `is_ungulate`, `long_neck`, `long_legs`, `dark_spots` | `giraffe` | Level 3 (Species) |
| **R12** | `is_ungulate`, `black_stripes`, `NOT is_carnivore` | `zebra` | Level 3 (Species) |
| **R13** | `is_bird`, `does_not_fly`, `long_neck`, `long_legs`, `black_and_white_color` | `ostrich` | Level 3 (Species) |
| **R14** | `is_bird`, `does_not_fly`, `swims`, `black_and_white_color` | `penguin` | Level 3 (Species) |
| **R15** | `is_bird`, `good_flyer` | `albatross` | Level 3 (Species) |

---

### **Experimental Implementation & Results**

#### **Exercise 1: Animal Identification (Tiger, Giraffe, Zebra)**

##### **1. Tiger Identification Test**
- **Initial Working Memory (WM)**: `{"has_hair", "eats_meat", "tawny_color", "black_stripes"}`
- **Execution Log**:
  - **Cycle 1**: Conflict Set = `[R1, R5]`. Fired `R1` -> Added `is_mammal`.
  - **Cycle 2**: Conflict Set = `[R5]`. Fired `R5` -> Added `is_carnivore`.
  - **Cycle 3**: Conflict Set = `[R10]`. Fired `R10` -> Added `tiger`.
- **Firing Sequence**: `R1 -> R5 -> R10`
- **Result**: Identified **tiger**.

##### **2. Giraffe Identification Test**
- **Initial Working Memory (WM)**: `{"gives_milk", "has_hoofs", "long_neck", "long_legs", "dark_spots"}`
- **Execution Log**:
  - **Cycle 1**: Conflict Set = `[R2]`. Fired `R2` -> Added `is_mammal`.
  - **Cycle 2**: Conflict Set = `[R7]`. Fired `R7` -> Added `is_ungulate`.
  - **Cycle 3**: Conflict Set = `[R11]`. Fired `R11` -> Added `giraffe`.
- **Firing Sequence**: `R2 -> R7 -> R11`
- **Result**: Identified **giraffe**.

##### **3. Zebra Identification Test**
- **Initial Working Memory (WM)**: `{"has_hair", "chews_cud", "black_stripes", "NOT is_carnivore"}`
- **Execution Log**:
  - **Cycle 1**: Conflict Set = `[R1]`. Fired `R1` -> Added `is_mammal`.
  - **Cycle 2**: Conflict Set = `[R8]`. Fired `R8` -> Added `is_ungulate`.
  - **Cycle 3**: Conflict Set = `[R12]`. Fired `R12` -> Added `zebra`.
- **Firing Sequence**: `R1 -> R8 -> R12`
- **Result**: Identified **zebra**.

---

#### **Exercise 2: Fallback to Most Specific Class (Incomplete Facts)**

When provided with facts that satisfy no species-level rule (Level 3), the engine halts gracefully and reports the **most specific taxonomic class** established from intermediate conclusions.

```
Initial WM: {"has_hair", "eats_meat"}
  |
  +---> [R1 Fired] ---> WM: +{"is_mammal"}      (Level 1 Class)
  |
  +---> [R5 Fired] ---> WM: +{"is_carnivore"}   (Level 2 Order)
  |
  +---> No species rules match (No tawny_color/black_stripes)
  |
  +---> Output: Species = NONE, Most Specific Class = "is_carnivore" (Level 2 Order)
```

##### **Test Case Summaries**:

1. **Test Case: `{"has_hair", "eats_meat"}`**
   - **Firing Sequence**: `R1 -> R5`
   - **Final Working Memory**: `{"has_hair", "eats_meat", "is_mammal", "is_carnivore"}`
   - **Identified Animal**: `NONE`
   - **Most Specific Class**: **`is_carnivore`** (Order Level 2)

2. **Test Case: `{"gives_milk"}`**
   - **Firing Sequence**: `R2`
   - **Final Working Memory**: `{"gives_milk", "is_mammal"}`
   - **Identified Animal**: `NONE`
   - **Most Specific Class**: **`is_mammal`** (Class Level 1)

3. **Test Case: `{"green_skin", "small_tail"}`**
   - **Firing Sequence**: `None`
   - **Final Working Memory**: `{"green_skin", "small_tail"}`
   - **Identified Animal**: `NONE`
   - **Most Specific Class**: `NONE` (Unrecognized features, no rules triggered)

---

#### **Exercise 3: Conflict Resolution Strategy Comparison (`FIRST_MATCH` vs `FIRE_ALL`)**

To evaluate the impact of rule execution granularity, the engine was tested on identical inputs (`{"has_hair", "has_pointed_teeth", "has_claws", "has_forward_eyes", "tawny_color", "black_stripes"}`) under both strategies.

##### **Detailed Cycle Comparison**:

- **Strategy 1: `FIRST_MATCH` (Sequential / Depth-First)**
  - **Cycle 1**: Conflict Set = `[R1, R6]`. Fired `R1` -> WM: `+is_mammal`.
  - **Cycle 2**: Conflict Set = `[R6]`. Fired `R6` -> WM: `+is_carnivore`.
  - **Cycle 3**: Conflict Set = `[R10]`. Fired `R10` -> WM: `+tiger`.
  - **Total Cycles**: **3** | **Firing Sequence**: `R1 -> R6 -> R10`

- **Strategy 2: `FIRE_ALL` (Parallel / Breadth-First)**
  - **Cycle 1**: Conflict Set = `[R1, R6]`. Fired `[R1, R6]` simultaneously -> WM: `+is_mammal, +is_carnivore`.
  - **Cycle 2**: Conflict Set = `[R10]`. Fired `R10` -> WM: `+tiger`.
  - **Total Cycles**: **2** | **Firing Sequence**: `[R1, R6, R10]`

##### **Quantitative Comparison Summary**:

| Performance Metric | `FIRST_MATCH` (Sequential) | `FIRE_ALL` (Parallel) | Impact / Observations |
| :--- | :--- | :--- | :--- |
| **Total Reasoning Cycles** | `3 cycles` | `2 cycles` | **33.3% reduction in cycles** using `FIRE_ALL` |
| **Total Rules Fired** | `3 rules` | `3 rules` | Same total deduction work |
| **Cycle 1 Fired Rules** | `[R1]` | `[R1, R6]` | `FIRE_ALL` fires independent rules together |
| **Firing Sequence Format** | `R1 -> R6 -> R10` | `[R1, R6, R10]` | Sequential chain vs. Layered stages |
| **Final Working Memory Size** | `9 facts` | `9 facts` | Identical final logical state |
| **Identified Animal** | `tiger` | `tiger` | Sound and identical identification |

---

### **Key Observations & Discussion**

1. **Incremental Abstraction**: Forward chaining elegantly demonstrates how high-level concepts (`is_mammal`, `is_carnivore`, `is_ungulate`) emerge step-by-step from raw perceptual observations before reaching concrete conclusions (`tiger`, `giraffe`, `zebra`).
2. **Explanation Trace**: The recorded firing sequence (`R1 -> R5 -> R10`) serves as a direct, auditable justification chain showing *why* a conclusion was reached.
3. **Robustness via Fallback**: In real-world diagnostic systems, complete feature sets are rarely available. Returning the most specific derived class prevents system failure when exact matching is impossible.
4. **Strategy Trade-offs**:
   - `FIRST_MATCH` allows fine-grained control and predictable single-step debugging, but requires more reasoning cycles.
   - `FIRE_ALL` maximizes throughput and reduces total cycles, making it suitable for high-performance inference engines.

---

### **Conclusion**
The Forward Chaining Inference Engine for animal identification was successfully designed, implemented, and benchmarked. The system demonstrated data-driven reasoning by progressively deriving intermediate taxonomic abstractions and identifying target animals (`tiger`, `giraffe`, `zebra`). When presented with incomplete facts, the engine accurately reported the most specific established class. Comparison between `FIRST_MATCH` and `FIRE_ALL` conflict resolution strategies highlighted how parallel rule firing optimizes deduction efficiency while maintaining logical correctness.
