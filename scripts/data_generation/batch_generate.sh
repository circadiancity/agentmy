#!/bin/bash
# Batch generate 2000 enriched clinical tasks in batches of 20
# Each batch uses a different seed to ensure diversity
# Accumulates results into a single tasks file

set -e

PROJECT_ROOT="/home/ubuntu/agentmy"
OUTPUT_DIR="$PROJECT_ROOT/data/tau2/domains/clinical/primekg"
BATCH_DIR="$OUTPUT_DIR/batches"
ACCUMULATOR="$OUTPUT_DIR/all_generated_tasks.json"
LOG_FILE="$OUTPUT_DIR/generation_log.txt"
TOTAL_TASKS=40000
BATCH_SIZE=20
MAX_CONCURRENCY=5

mkdir -p "$BATCH_DIR"

# Initialize accumulator if it doesn't exist
if [ ! -f "$ACCUMULATOR" ]; then
    echo "[]" > "$ACCUMULATOR"
fi

# Count existing tasks
EXISTING=$(python3 -c "import json; print(len(json.load(open('$ACCUMULATOR'))))" 2>/dev/null || echo 0)
echo "$(date): Starting batch generation. Existing tasks: $EXISTING, Target: $TOTAL_TASKS" | tee -a "$LOG_FILE"

BATCH_NUM=0
SEED_BASE=1000

while [ "$EXISTING" -lt "$TOTAL_TASKS" ]; do
    BATCH_NUM=$((BATCH_NUM + 1))
    SEED=$((SEED_BASE + BATCH_NUM * 7))  # Different seed per batch
    REMAINING=$((TOTAL_TASKS - EXISTING))

    # Don't generate more than needed
    if [ "$REMAINING" -lt "$BATCH_SIZE" ]; then
        CURRENT_BATCH=$REMAINING
    else
        CURRENT_BATCH=$BATCH_SIZE
    fi

    echo "$(date): Batch $BATCH_NUM — generating $CURRENT_BATCH tasks (seed=$SEED, total so far=$EXISTING)" | tee -a "$LOG_FILE"

    # Generate batch
    BATCH_FILE="$BATCH_DIR/batch_${BATCH_NUM}.json"

    if python3 "$PROJECT_ROOT/scripts/data_generation/generate_enriched_tasks.py" \
        --num-tasks "$CURRENT_BATCH" \
        --max-concurrency "$MAX_CONCURRENCY" \
        --seed "$SEED" \
        2>&1 | tee -a "$LOG_FILE"; then

        # Copy the generated v3 tasks as batch backup
        if [ -f "$OUTPUT_DIR/enriched_tasks_v3.json" ]; then
            cp "$OUTPUT_DIR/enriched_tasks_v3.json" "$BATCH_FILE"
        fi

        # Read newly generated tau2 tasks and accumulate
        python3 << PYEOF
import json

# Load new batch
with open("$OUTPUT_DIR/tasks.json") as f:
    new_tasks = json.load(f)

# Load accumulator
with open("$ACCUMULATOR") as f:
    all_tasks = json.load(f)

# Deduplicate by ID
existing_ids = {t["id"] for t in all_tasks}
added = 0
for t in new_tasks:
    if t["id"] not in existing_ids:
        all_tasks.append(t)
        existing_ids.add(t["id"])
        added += 1

# Save accumulator
with open("$ACCUMULATOR", "w") as f:
    json.dump(all_tasks, f, indent=2, ensure_ascii=False)

print(f"  Added {added} new tasks. Total: {len(all_tasks)}")
PYEOF

        echo "$(date): Batch $BATCH_NUM complete" | tee -a "$LOG_FILE"
    else
        echo "$(date): Batch $BATCH_NUM FAILED (seed=$SEED). Continuing..." | tee -a "$LOG_FILE"
    fi

    # Update count
    EXISTING=$(python3 -c "import json; print(len(json.load(open('$ACCUMULATOR'))))" 2>/dev/null || echo "$EXISTING")

    # Brief pause between batches to avoid rate limiting
    sleep 2
done

echo "$(date): Generation complete! Total tasks: $EXISTING" | tee -a "$LOG_FILE"

# Final step: fix tool names and create final tasks.json + splits
python3 << 'PYEOF'
import json
import random

TOOL_MAP = {
    "ASK": "get_patient_info",
    "CHECK_ALLERGY": "check_allergies",
    "CHECK_INTERACTION": "check_drug_interactions",
    "ORDER_LAB": "order_lab_test",
    "GET_RESULTS": "get_lab_results",
    "DIAGNOSE": "record_diagnosis",
    "PRESCRIBE": "prescribe_medication",
    "EDUCATE": "get_treatment_guidelines",
    "SCHEDULE_FOLLOWUP": "create_follow_up_plan",
    "REFER": "refer_to_specialist",
    "END": None,
}

OUTPUT_DIR = "/home/ubuntu/agentmy/data/tau2/domains/clinical/primekg"

with open(f"{OUTPUT_DIR}/all_generated_tasks.json") as f:
    tasks = json.load(f)

# Fix tool names and reward_basis
fixed = 0
for task in tasks:
    ec = task.get("evaluation_criteria", {})
    new_actions = []
    for action in ec.get("actions", []):
        old_name = action["name"]
        new_name = TOOL_MAP.get(old_name, old_name)
        if new_name is None:
            continue
        if old_name != new_name:
            fixed += 1
        action["name"] = new_name
        if old_name in action.get("action_id", ""):
            action["action_id"] = action["action_id"].replace(old_name, new_name)
        new_actions.append(action)
    ec["actions"] = new_actions
    basis = ec.get("reward_basis", [])
    ec["reward_basis"] = [b for b in basis if b in ("ACTION", "COMMUNICATE", "DB")]
    if not ec["reward_basis"]:
        ec["reward_basis"] = ["ACTION", "COMMUNICATE"]

# Save final tasks.json
with open(f"{OUTPUT_DIR}/tasks.json", "w") as f:
    json.dump(tasks, f, indent=2, ensure_ascii=False)

# Create train/test/base splits (80/20)
random.seed(42)
ids = [t["id"] for t in tasks]
random.shuffle(ids)
split_idx = int(len(ids) * 0.8)
splits = {
    "train": ids[:split_idx],
    "test": ids[split_idx:],
    "base": ids,
}

with open(f"{OUTPUT_DIR}/split_tasks.json", "w") as f:
    json.dump(splits, f, indent=2)

# Stats
from collections import Counter
difficulties = []
for t in tasks:
    desc = t.get("description", {})
    notes = desc.get("notes", "") if desc else ""
    purpose = desc.get("purpose", "") if desc else ""
    import re
    m = re.search(r"L(\d)", purpose or notes or t.get("id", ""))
    difficulties.append(f"L{m.group(1)}" if m else "unknown")

diff_counts = Counter(difficulties)

stats = {
    "total_tasks": len(tasks),
    "train_tasks": len(splits["train"]),
    "test_tasks": len(splits["test"]),
    "difficulty_distribution": dict(diff_counts),
    "tool_names_fixed": fixed,
}

with open(f"{OUTPUT_DIR}/stats.json", "w") as f:
    json.dump(stats, f, indent=2)

print(f"\nFinal dataset:")
print(f"  Total tasks: {len(tasks)}")
print(f"  Train: {len(splits['train'])}, Test: {len(splits['test'])}")
print(f"  Difficulties: {dict(diff_counts)}")
print(f"  Tool names fixed: {fixed}")
PYEOF

echo "$(date): Final tasks.json, splits, and stats written." | tee -a "$LOG_FILE"
