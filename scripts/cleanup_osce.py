#!/usr/bin/env python3
"""Clean up all_generated_tasks.json by applying OSCE criteria."""

import json
import re
from collections import Counter
from pathlib import Path

TASKS_PATH = Path("data/tau2/domains/clinical/primekg/all_generated_tasks.json")

KEEP_ACTIONS = {
    "record_diagnosis",
    "record_differential",
    "prescribe_medication",
    "refer_to_specialist",
    "create_follow_up_plan",
}

# Qualifier phrases to strip from diagnosis strings (order matters: longest first)
QUALIFIER_PHRASES = [
    "in the setting of",
    "secondary to",
    "associated with",
    "suspected/confirmed",
    "suspected/",
    "confirmed/",
    "due to",
    "with",
]


def clean_diagnosis_string(diag: str) -> str:
    """Strip parenthetical content and trailing qualifier phrases from diagnosis."""
    if not diag:
        return diag

    # Strip parenthetical content like (CAD), (CMS), etc.
    cleaned = re.sub(r"\s*\([^)]*\)", "", diag).strip()

    # Strip trailing qualifier phrases
    for phrase in QUALIFIER_PHRASES:
        pattern = re.compile(r"\s+" + re.escape(phrase) + r"\s+.*$", re.IGNORECASE)
        candidate = pattern.sub("", cleaned).strip()
        if len(candidate) >= 5:
            cleaned = candidate

    # Also handle "suspected/" or "confirmed/" at the beginning
    for prefix in ["suspected/confirmed ", "suspected/ ", "confirmed/ "]:
        if cleaned.lower().startswith(prefix.lower()):
            candidate = cleaned[len(prefix):].strip()
            if len(candidate) >= 5:
                cleaned = candidate

    return cleaned.strip()


def extract_disease_name(task: dict) -> str | None:
    """Extract disease name from task using priority chain."""
    # 1. Try record_diagnosis action's diagnosis argument
    for action in task.get("evaluation_criteria", {}).get("actions", []):
        if action["name"] == "record_diagnosis":
            diag = action.get("arguments", {}).get("diagnosis", "")
            if diag and not diag.startswith("<"):
                # Use the cleaned version for communicate_info
                return clean_diagnosis_string(diag)

    # 2. Try description.notes field: "Disease: <name>."
    notes = task.get("description", {}).get("notes", "")
    m = re.search(r"Disease:\s*(.+?)\.", notes)
    if m:
        disease = m.group(1).strip()
        if disease:
            return disease

    # 3. Try task ID pattern
    task_id = task.get("id", "")
    m = re.match(r"primekg_L\d+_(.+?)_\d+$", task_id)
    if m:
        disease = m.group(1).replace("_", " ")
        if disease.lower() != "unknown":
            return disease

    return None


def main():
    with open(TASKS_PATH) as f:
        tasks = json.load(f)

    total = len(tasks)
    tasks_with_actions = 0
    tasks_with_diagnosis = 0
    tasks_with_communicate = 0
    action_type_counts = Counter()

    for task in tasks:
        ec = task.get("evaluation_criteria", {})

        # 2a. Set reward_basis
        ec["reward_basis"] = ["CLINICAL_PROCESS"]

        # 2b. Strip non-OSCE actions
        old_actions = ec.get("actions", [])
        new_actions = [a for a in old_actions if a["name"] in KEEP_ACTIONS]
        ec["actions"] = new_actions

        if new_actions:
            tasks_with_actions += 1
        for a in new_actions:
            action_type_counts[a["name"]] += 1

        # 2d. Clean verbose diagnosis strings in record_diagnosis actions
        has_diagnosis = False
        for action in new_actions:
            if action["name"] == "record_diagnosis":
                has_diagnosis = True
                args = action.get("arguments", {})
                if "diagnosis" in args and args["diagnosis"]:
                    args["diagnosis"] = clean_diagnosis_string(args["diagnosis"])

        if has_diagnosis:
            tasks_with_diagnosis += 1

        # 2c. Set communicate_info to primary disease name
        disease = extract_disease_name(task)
        if disease:
            ec["communicate_info"] = [disease]
            tasks_with_communicate += 1
        elif ec.get("communicate_info"):
            # Keep existing first element
            ec["communicate_info"] = [ec["communicate_info"][0]]
            tasks_with_communicate += 1

    with open(TASKS_PATH, "w") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    print(f"Total tasks: {total}")
    print(f"Tasks with actions: {tasks_with_actions}")
    print(f"Tasks with record_diagnosis: {tasks_with_diagnosis}")
    print(f"Tasks with communicate_info: {tasks_with_communicate}")
    print(f"\nAction type distribution (kept):")
    for name, count in action_type_counts.most_common():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
