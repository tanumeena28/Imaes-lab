import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import accuracy_score, classification_report, ConfusionMatrixDisplay

SEED = 42
rng = np.random.default_rng(SEED)

ACTIONS = ["Self-study plan", "Peer tutoring", "Academic advisor"]

def human_label(attendance, assignment_avg, quiz_avg, study_hours, group, biased=True):
    """Simulate a human advisor's example decision.

    The baseline rule uses academic indicators. For demonstration only, when
    biased=True, Group B receives a slightly more severe decision in borderline
    cases. This is intentionally included to demonstrate how unfair patterns
    can enter example labels. Do not use group membership for real decisions.
    """
    academic_score = 0.30 * attendance + 0.35 * assignment_avg + 0.35 * quiz_avg
    low_support_signal = (
        attendance < 65 or assignment_avg < 50 or quiz_avg < 50
    )
    borderline = academic_score < 62 or study_hours < 4

    if low_support_signal:
        decision = "Academic advisor"
    elif borderline:
        decision = "Peer tutoring"
    else:
        decision = "Self-study plan"

    # Deliberate synthetic bias: only used in the baseline human examples.
    if biased and group == "Group B" and decision == "Self-study plan" and academic_score < 72:
        decision = "Peer tutoring"

    return decision

n = 600
df = pd.DataFrame({
    "attendance": rng.integers(40, 101, size=n),
    "assignment_avg": np.clip(rng.normal(68, 17, size=n), 15, 100).round(1),
    "quiz_avg": np.clip(rng.normal(65, 18, size=n), 10, 100).round(1),
    "study_hours": np.clip(rng.normal(7, 3, size=n), 0, 20).round(1),
    "group": rng.choice(["Group A", "Group B"], size=n, p=[0.5, 0.5])
})

df["human_decision"] = df.apply(
    lambda r: human_label(
        r.attendance, r.assignment_avg, r.quiz_avg, r.study_hours, r.group, biased=True
    ),
    axis=1
)

display(df.head(10))
print("\nNumber of examples:", len(df))
print("\nHuman decision counts:")
display(df["human_decision"].value_counts().rename_axis("decision").to_frame("count"))


# Knowledge base: ordered rules. Earlier rules have higher priority.
RULES_V1 = [
    {
        "id": "R1",
        "condition": "Attendance < 65 OR assignment average < 50 OR quiz average < 50",
        "action": "Academic advisor",
        "why": "At least one academic indicator is low, so a human review is recommended."
    },
    {
        "id": "R2",
        "condition": "Weighted academic score < 62 OR study hours < 4",
        "action": "Peer tutoring",
        "why": "The indicators suggest that extra structured practice may help."
    },
    {
        "id": "R3",
        "condition": "No earlier rule matched",
        "action": "Self-study plan",
        "why": "The indicators do not trigger the higher-support rules."
    }
]

def expert_system(row, rules=RULES_V1):
    """Rule-based inference engine. Returns both action and explanation."""
    attendance = float(row["attendance"])
    assignment_avg = float(row["assignment_avg"])
    quiz_avg = float(row["quiz_avg"])
    study_hours = float(row["study_hours"])
    score = 0.30 * attendance + 0.35 * assignment_avg + 0.35 * quiz_avg

    # Rule R1
    if attendance < 65 or assignment_avg < 50 or quiz_avg < 50:
        return {
            "recommendation": "Academic advisor",
            "rule_id": "R1",
            "explanation": (
                f"R1 fired: attendance={attendance:.1f}%, "
                f"assignment average={assignment_avg:.1f}, quiz average={quiz_avg:.1f}. "
                "At least one is below its threshold."
            ),
            "weighted_score": round(score, 2)
        }

    # Rule R2
    if score < 62 or study_hours < 4:
        reasons = []
        if score < 62:
            reasons.append(f"weighted academic score {score:.1f} < 62")
        if study_hours < 4:
            reasons.append(f"study hours {study_hours:.1f} < 4")
        return {
            "recommendation": "Peer tutoring",
            "rule_id": "R2",
            "explanation": "R2 fired: " + " and ".join(reasons) + ".",
            "weighted_score": round(score, 2)
        }

    # Rule R3
    return {
        "recommendation": "Self-study plan",
        "rule_id": "R3",
        "explanation": (
            f"R3 fired: no higher-priority rule matched; weighted academic score={score:.1f}, "
            f"study hours={study_hours:.1f}."
        ),
        "weighted_score": round(score, 2)
    }

# Run the expert system on a few illustrative cases.
examples = pd.DataFrame([
    {"case": "Low attendance", "attendance": 55, "assignment_avg": 72, "quiz_avg": 70, "study_hours": 6},
    {"case": "Borderline performance", "attendance": 82, "assignment_avg": 60, "quiz_avg": 58, "study_hours": 5},
    {"case": "Doing well", "attendance": 92, "assignment_avg": 85, "quiz_avg": 88, "study_hours": 8},
])

example_results = []
for _, row in examples.iterrows():
    result = expert_system(row)
    example_results.append({
        "case": row["case"],
        "recommendation": result["recommendation"],
        "rule": result["rule_id"],
        "explanation": result["explanation"]
    })

display(pd.DataFrame(example_results))


FEATURES = ["attendance", "assignment_avg", "quiz_avg", "study_hours"]
TARGET = "human_decision"

X = df[FEATURES]
y = df[TARGET]
groups = df["group"]

X_train, X_test, y_train, y_test, group_train, group_test = train_test_split(
    X, y, groups, test_size=0.25, random_state=SEED, stratify=y
)

# A shallow decision tree is chosen because it is relatively interpretable.
imitation_model = Pipeline([
    ("scale", StandardScaler()),
    ("tree", DecisionTreeClassifier(max_depth=4, min_samples_leaf=8, random_state=SEED))
])
imitation_model.fit(X_train, y_train)

y_pred = imitation_model.predict(X_test)
print(f"Imitation model accuracy vs. held-out human labels: {accuracy_score(y_test, y_pred):.3f}")
print("\nClassification report:")
print(classification_report(y_test, y_pred, zero_division=0))

ConfusionMatrixDisplay.from_predictions(
    y_test, y_pred, labels=ACTIONS, xticks_rotation=25
)
plt.title("Imitation model: predictions vs. human example decisions")
plt.tight_layout()
plt.show()


# Example: explain one rule-based recommendation.
student = {
    "attendance": 78,
    "assignment_avg": 56,
    "quiz_avg": 61,
    "study_hours": 3
}
rule_result = expert_system(student)
print("Rule-based recommendation:", rule_result["recommendation"])
print("Rule fired:", rule_result["rule_id"])
print("Explanation:", rule_result["explanation"])

# Explain a learned-model prediction by following its decision-tree path.
tree = imitation_model.named_steps["tree"]
scaler = imitation_model.named_steps["scale"]
student_df = pd.DataFrame([student])[FEATURES]
student_scaled = scaler.transform(student_df)
leaf_id = tree.apply(student_scaled)[0]
node_indicator = tree.decision_path(student_scaled)
feature_names = FEATURES
tree_classes = tree.classes_

print("\nImitation model recommendation:", imitation_model.predict(student_df)[0])
print("Decision-tree path:")
for node_id in node_indicator.indices:
    if node_id == leaf_id:
        counts = tree.tree_.value[node_id][0]
        predicted_class = tree_classes[np.argmax(counts)]
        print(f"  Leaf node {node_id}: class proportions={np.round(counts, 3).tolist()}, predicted={predicted_class}")
    else:
        feature_index = tree.tree_.feature[node_id]
        if feature_index >= 0:
            threshold = tree.tree_.threshold[node_id]
            value = student_scaled[0, feature_index]
            direction = "<=" if value <= threshold else ">"
            print(
                f"  Node {node_id}: scaled {feature_names[feature_index]} "
                f"({value:.2f}) {direction} threshold {threshold:.2f}"
            )

# Global feature importance from the trained decision tree.
importance = pd.Series(
    tree.feature_importances_, index=FEATURES
).sort_values(ascending=True)
importance.plot(kind="barh")
plt.title("Imitation model: decision-tree feature importance")
plt.xlabel("Importance")
plt.tight_layout()
plt.show()


SUPPORT_LEVEL = {
    "Self-study plan": 0,
    "Peer tutoring": 1,
    "Academic advisor": 2
}

audit = X_test.copy()
audit["group"] = group_test.to_numpy()
audit["human_decision"] = y_test.to_numpy()
audit["model_decision"] = y_pred

def fairness_summary(data, decision_col):
    """Summarize group-level decision rates and mean support intensity."""
    counts = data.groupby("group").size().rename("n")
    rates = pd.crosstab(data["group"], data[decision_col], normalize="index")
    rates = rates.reindex(columns=ACTIONS, fill_value=0)
    rates.columns = [f"rate: {c}" for c in rates.columns]
    support = data.assign(
        support_level=data[decision_col].map(SUPPORT_LEVEL)
    ).groupby("group")["support_level"].mean().rename("mean_support_level")
    return pd.concat([counts, rates, support], axis=1).round(3)

print("Fairness audit for human-provided decisions:")
display(fairness_summary(audit, "human_decision"))

print("Fairness audit for imitation model predictions:")
display(fairness_summary(audit, "model_decision"))

# Visual comparison of model action rates by group.
rates = pd.crosstab(audit["group"], audit["model_decision"], normalize="index")
rates = rates.reindex(columns=ACTIONS, fill_value=0)
rates.plot(kind="bar")
plt.title("Imitation model recommendation rates by group")
plt.ylabel("Share within group")
plt.xlabel("Synthetic group")
plt.xticks(rotation=0)
plt.legend(title="Recommendation", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.show()


# Make a modified rule-based engine. Keep the same inference structure,
# but change R1 attendance threshold from 65 to 60.
def expert_system_v2(row):
    attendance = float(row["attendance"])
    assignment_avg = float(row["assignment_avg"])
    quiz_avg = float(row["quiz_avg"])
    study_hours = float(row["study_hours"])
    score = 0.30 * attendance + 0.35 * assignment_avg + 0.35 * quiz_avg

    if attendance < 60 or assignment_avg < 50 or quiz_avg < 50:
        return {"recommendation": "Academic advisor", "rule_id": "R1-v2"}
    if score < 62 or study_hours < 4:
        return {"recommendation": "Peer tutoring", "rule_id": "R2"}
    return {"recommendation": "Self-study plan", "rule_id": "R3"}

# Apply both expert-system versions to the same test cases.
comparison = X_test.copy().reset_index(drop=True)
comparison["old_rule"] = comparison.apply(
    lambda r: expert_system(r)["recommendation"], axis=1
)
comparison["new_rule"] = comparison.apply(
    lambda r: expert_system_v2(r)["recommendation"], axis=1
)
comparison["rule_changed"] = comparison["old_rule"] != comparison["new_rule"]

print("Rule-based change count:")
print(comparison["rule_changed"].value_counts().rename(index={True: "Changed", False: "Unchanged"}))
display(comparison.loc[comparison["rule_changed"]].head(10))

# Generate a less biased example set. The revised labels use academic indicators only.
df_revised = df.copy()
df_revised["human_decision_revised"] = df_revised.apply(
    lambda r: human_label(
        r.attendance, r.assignment_avg, r.quiz_avg, r.study_hours, r.group, biased=False
    ),
    axis=1
)

# Train a second model on revised human labels using the same split indices.
X_train2 = df_revised.loc[X_train.index, FEATURES]
y_train2 = df_revised.loc[X_train.index, "human_decision_revised"]
X_test2 = df_revised.loc[X_test.index, FEATURES]
y_test2 = df_revised.loc[X_test.index, "human_decision_revised"]

revised_model = Pipeline([
    ("scale", StandardScaler()),
    ("tree", DecisionTreeClassifier(max_depth=4, min_samples_leaf=8, random_state=SEED))
])
revised_model.fit(X_train2, y_train2)
revised_pred = revised_model.predict(X_test2)

print(f"Original model agreement with original labels: {accuracy_score(y_test, y_pred):.3f}")
print(f"Revised model agreement with revised labels:   {accuracy_score(y_test2, revised_pred):.3f}")

# Compare fairness summaries on the same test cases.
fairness_compare = pd.DataFrame({
    "group": group_test.to_numpy(),
    "original_label": y_test.to_numpy(),
    "revised_label": y_test2.to_numpy(),
    "original_model": y_pred,
    "revised_model": revised_pred
})

print("\nOriginal model recommendation rates:")
display(fairness_summary(
    fairness_compare.rename(columns={"original_model": "decision"}), "decision"
))
print("Revised model recommendation rates:")
display(fairness_summary(
    fairness_compare.rename(columns={"revised_model": "decision"}), "decision"
))


changed = comparison[comparison["rule_changed"]]
if len(changed) > 0:
    case = changed.iloc[0]
    print("Example where the rule change matters:")
    print(case[FEATURES].to_dict())
    print("Before:", case["old_rule"])
    print("After: ", case["new_rule"])
    print("Reason: the attendance threshold in R1 changed from <65 to <60.")
else:
    print("No changed test example in this split. Trying a targeted case:")
    targeted = {
        "attendance": 62,
        "assignment_avg": 70,
        "quiz_avg": 68,
        "study_hours": 6
    }
    print("Inputs:", targeted)
    print("Before:", expert_system(targeted)["recommendation"])
    print("After: ", expert_system_v2(targeted)["recommendation"])


