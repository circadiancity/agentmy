#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch update all clinical domain task files with new medical format

This script updates all clinical domain task files to include:
- medical_persona: Structured medical persona data
- medical_criteria: Evaluation criteria with tool categories, reasoning steps, safety checks
- set_medical_persona initialization action

Usage:
    python update_all_clinical_tasks.py
"""

import sys
import io
import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')


def extract_age_from_persona(persona: str) -> Optional[int]:
    """Extract age from persona string"""
    if not persona:
        return None

    # Match patterns like "54-year-old", "32岁", "32 year old"
    patterns = [
        r'(\d+)-year-old',
        r'(\d+)\s*year\s*old',
        r'(\d+)岁',
    ]

    for pattern in patterns:
        match = re.search(pattern, persona, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue

    return None


def extract_gender_from_persona(persona: str) -> Optional[str]:
    """Extract gender from persona string"""
    if not persona:
        return None

    # Check for male/female indicators
    male_indicators = ['male', 'man', '男', '先生']
    female_indicators = ['female', 'woman', '女', '女士']

    persona_lower = persona.lower()

    for indicator in male_indicators:
        if indicator.lower() in persona_lower:
            return 'male'

    for indicator in female_indicators:
        if indicator.lower() in persona_lower:
            return 'female'

    return None


def extract_chief_complaint(ticket: str, instructions: Dict) -> str:
    """Extract chief complaint from ticket or instructions"""
    if ticket:
        return ticket

    if instructions and 'reason_for_call' in instructions:
        return instructions['reason_for_call']

    return "Unknown"


def extract_symptoms(ticket: str, instructions: Dict, known_info: str = None) -> List[str]:
    """Extract symptoms from ticket and known_info"""
    symptoms = []

    # Add ticket/chief complaint as main symptom
    if ticket:
        # Remove common prefixes
        ticket_clean = re.sub(r'^(我的|我有|i have|i\'ve|patient has)\s*', '', ticket, flags=re.IGNORECASE)
        ticket_clean = ticket_clean.strip('？?！!。.')
        if ticket_clean:
            symptoms.append(ticket_clean)

    # Extract from known_info
    if known_info:
        # Look for symptom patterns
        symptom_patterns = [
            r'(?:症状|症状是|symptoms?:)\s*([^。，.?\n]+)',
            r'(?:表现为|presenting with)\s*([^。，.?\n]+)',
            r'(?:主要症状|chief complaint:?)\s*([^。，.?\n]+)',
        ]

        for pattern in symptom_patterns:
            matches = re.findall(pattern, known_info, re.IGNORECASE)
            for match in matches:
                symptom = match.strip()
                if symptom and symptom not in symptoms:
                    symptoms.append(symptom)

    return symptoms if symptoms else [extract_chief_complaint(ticket, instructions)]


def create_medical_persona_from_task(task: Dict) -> Dict[str, Any]:
    """Create medical_persona from existing task data"""
    user_scenario = task.get('user_scenario', {})
    instructions = user_scenario.get('instructions', {})
    persona_str = user_scenario.get('persona', '')
    ticket = task.get('ticket', '')
    known_info = instructions.get('known_info', '')

    # Extract basic info
    age = extract_age_from_persona(persona_str)
    gender = extract_gender_from_persona(persona_str)

    # Extract symptoms
    chief_complaint = extract_chief_complaint(ticket, instructions)
    symptoms = extract_symptoms(ticket, instructions, known_info)

    # Extract duration and severity from known_info if available
    duration = None
    severity = None

    if known_info:
        # Look for duration patterns
        duration_match = re.search(r'(\d+)\s*(天|days?|周|weeks?|月|months?)', known_info, re.IGNORECASE)
        if duration_match:
            duration = duration_match.group(0)

        # Look for severity patterns
        severity_indicators = ['严重', 'severe', 'mild', '轻微', 'moderate', '中等']
        for indicator in severity_indicators:
            if indicator.lower() in known_info.lower():
                severity = indicator if '严重' in known_info or 'severe' in known_info.lower() else (
                    'mild' if '轻微' in known_info or 'mild' in known_info.lower() else 'moderate'
                )
                break

    # Build medical persona
    medical_persona = {
        "age": age,
        "gender": gender,
        "symptoms": symptoms,
        "duration": duration,
        "severity": severity,
        "past_medical_history": [],
        "current_medications": [],
        "allergies": [],
        "lab_results": {},
        "vital_signs": {},
        "smoking_status": None,
        "alcohol_use": None
    }

    return medical_persona


def determine_tool_category(domain: str, symptoms: List[str]) -> str:
    """Determine tool category based on domain and symptoms"""
    # Domain-based mapping
    domain_category_map = {
        'cardiology': 'diagnosis',
        'nephrology': 'diagnosis',
        'gastroenterology': 'diagnosis',
        'neurology': 'diagnosis',
        'endocrinology': 'diagnosis',
        'internal_medicine': 'suggestion',
        'primekg': 'diagnosis',
        'chinese_internal_medicine': 'suggestion',
    }

    # Get base domain
    base_domain = domain.replace('chinese_', '').replace('_medicine', '')

    if base_domain in domain_category_map:
        return domain_category_map[base_domain]

    # Check symptoms for clues
    symptoms_text = ' '.join(symptoms).lower()

    if any(word in symptoms_text for word in ['pain', 'chest', 'headache', '痛']):
        return 'diagnosis'

    if any(word in symptoms_text for word in ['can', 'could', 'should', '建议', '能']):
        return 'suggestion'

    return 'diagnosis'


def create_medical_criteria_for_task(task: Dict) -> Dict[str, Any]:
    """Create medical_criteria from existing task data"""
    user_scenario = task.get('user_scenario', {})
    instructions = user_scenario.get('instructions', {})
    domain = instructions.get('domain', task.get('domain', 'internal_medicine'))

    # Get symptoms
    ticket = task.get('ticket', '')
    chief_complaint = extract_chief_complaint(ticket, instructions)
    symptoms = extract_symptoms(ticket, instructions, instructions.get('known_info'))

    # Determine tool category
    tool_category = determine_tool_category(domain, symptoms)

    # Determine required tools based on domain and category
    required_tools = []
    if tool_category == 'diagnosis':
        required_tools = ['get_patient_by_mrn']
        # Add domain-specific tools
        if domain in ['cardiology', 'nephrology', 'internal_medicine']:
            required_tools.append('assess_blood_pressure')

    # Build reasoning steps
    reasoning_steps = [
        f"了解患者症状: {chief_complaint}",
        "评估症状持续时间和严重程度",
        "询问相关病史和用药情况",
        "提供医学建议或建议进一步检查"
    ]

    # Safety checks
    safety_checks = [
        "check_allergies",
        "check_current_medications"
    ]

    # Red flags
    red_flags = [
        "never_tell_patient_to_stop_medication",
        "never_give_definitive_diagnosis_without_examination",
        "always_suggest_consulting_doctor_for_serious_symptoms"
    ]

    medical_criteria = {
        "expected_tool_category": tool_category,
        "required_tools": required_tools,
        "optional_tools": [],
        "required_parameters": {},
        "reasoning_steps": reasoning_steps,
        "safety_checks": safety_checks,
        "red_flags": red_flags,
        "min_turns": 5,
        "max_turns": 10,
        "information_level": "partial"
    }

    return medical_criteria


def update_task_with_new_format(task: Dict) -> Dict:
    """Update a single task with new medical format"""
    # Create medical_persona
    medical_persona = create_medical_persona_from_task(task)

    # Create medical_criteria
    medical_criteria = create_medical_criteria_for_task(task)

    # Add medical_persona field
    task['medical_persona'] = medical_persona

    # Add medical_criteria to evaluation_criteria
    if 'evaluation_criteria' not in task:
        task['evaluation_criteria'] = {}

    task['evaluation_criteria']['medical_criteria'] = medical_criteria

    # Add set_medical_persona to initialization_actions
    if 'initial_state' not in task:
        task['initial_state'] = {}

    if 'initialization_actions' not in task['initial_state']:
        task['initial_state']['initialization_actions'] = []

    # Check if set_medical_persona already exists
    init_actions = task['initial_state']['initialization_actions']
    has_set_medical_persona = any(
        action.get('func_name') == 'set_medical_persona'
        for action in init_actions
    )

    if not has_set_medical_persona:
        # Insert set_medical_persona after set_user_info
        set_medical_persona_action = {
            "env_type": "user",
            "func_name": "set_medical_persona",
            "arguments": medical_persona
        }

        # Find position after set_user_info or append to end
        insert_pos = len(init_actions)
        for i, action in enumerate(init_actions):
            if action.get('func_name') == 'set_user_info':
                insert_pos = i + 1
                break

        init_actions.insert(insert_pos, set_medical_persona_action)

    return task


def update_tasks_file(input_file: Path, output_file: Path = None, backup: bool = True) -> Dict:
    """
    Update a tasks file with new medical format

    Returns:
        Dict with update statistics
    """
    if output_file is None:
        output_file = input_file

    print(f"\nProcessing: {input_file.relative_to(input_file.parent.parent.parent)}")

    # Backup original file
    if backup:
        backup_file = input_file.with_suffix('.json.backup')
        shutil.copy2(input_file, backup_file)
        print(f"  [BACKUP] {backup_file.name}")

    # Load tasks
    with open(input_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    if not isinstance(tasks, list):
        print(f"  [SKIP] Not a task list")
        return {'skipped': True, 'total': 0}

    # Update statistics
    stats = {
        'total': len(tasks),
        'updated': 0,
        'had_medical_persona': 0,
        'had_medical_criteria': 0,
    }

    # Update each task
    for i, task in enumerate(tasks):
        # Check existing format
        if 'medical_persona' in task:
            stats['had_medical_persona'] += 1

        if 'medical_criteria' in task.get('evaluation_criteria', {}):
            stats['had_medical_criteria'] += 1

        # Update task
        updated_task = update_task_with_new_format(task)
        tasks[i] = updated_task
        stats['updated'] += 1

    # Save updated tasks
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    print(f"  [OK] Updated {stats['updated']}/{stats['total']} tasks")
    print(f"       - Had medical_persona: {stats['had_medical_persona']}")
    print(f"       - Had medical_criteria: {stats['had_medical_criteria']}")

    return stats


def find_all_task_files(base_dir: Path) -> List[Path]:
    """Find all task files in clinical domains"""
    task_files = []

    clinical_dir = base_dir / 'data' / 'tau2' / 'domains' / 'clinical'

    if not clinical_dir.exists():
        print(f"Error: Clinical directory not found: {clinical_dir}")
        return task_files

    # Find all tasks*.json files (excluding split, db, test, train, val files)
    for json_file in clinical_dir.rglob('tasks*.json'):
        # Skip certain files
        if any(pattern in json_file.name for pattern in [
            'split_tasks', 'db', '_test', '_train', '_val', 'failed', 'improved',
            'high_quality', 'low_quality'
        ]):
            continue

        task_files.append(json_file)

    return sorted(task_files)


def main():
    """Main function"""
    print("\n" + "="*70)
    print(" Batch Update All Clinical Domain Tasks with New Medical Format")
    print("="*70)

    base_dir = Path.cwd()

    # Find all task files
    print("\n[1/2] Finding all task files...")
    task_files = find_all_task_files(base_dir)

    if not task_files:
        print("  No task files found!")
        return 1

    print(f"  Found {len(task_files)} task files")

    # Update each file
    print("\n[2/2] Updating task files...")
    print("="*70)

    all_stats = {
        'files_processed': 0,
        'total_tasks': 0,
        'total_updated': 0,
        'files_with_old_format': 0,
    }

    for task_file in task_files:
        try:
            stats = update_tasks_file(task_file, backup=True)

            if not stats.get('skipped'):
                all_stats['files_processed'] += 1
                all_stats['total_tasks'] += stats['total']
                all_stats['total_updated'] += stats['updated']

                if stats['had_medical_persona'] < stats['total'] or stats['had_medical_criteria'] < stats['total']:
                    all_stats['files_with_old_format'] += 1

        except Exception as e:
            print(f"  [ERROR] {task_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Summary
    print("\n" + "="*70)
    print(" Summary")
    print("="*70)
    print(f"\nFiles processed: {all_stats['files_processed']}")
    print(f"Total tasks: {all_stats['total_tasks']}")
    print(f"Tasks updated: {all_stats['total_updated']}")
    print(f"Files with old format: {all_stats['files_with_old_format']}")

    print("\nBackup files created with .json.backup extension")
    print("To restore: for f in *.backup; do mv \"$f\" \"${f%.backup}\"; done")

    print("\n[OK] Batch update complete!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
