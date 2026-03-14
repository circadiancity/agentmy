#!/usr/bin/env python3
"""
Test the Medical Dialogue Data Validator with example datasets.

This script demonstrates the validator's capabilities by testing it
against both valid and invalid medical dialogue datasets.
"""

import json
from pathlib import Path
from data_validator import MedicalDialogueValidator, ValidationLevel, ValidationResult


def create_valid_medical_task(task_id: str) -> dict:
    """Create a valid medical consultation task."""
    return {
        "id": task_id,
        "description": {
            "purpose": "Clinical consultation - patient with chest pain",
            "relevant_policies": None,
            "notes": "Multi-turn cardiac consultation"
        },
        "user_scenario": {
            "persona": "45-year-old patient with chest pain",
            "instructions": {
                "domain": "cardiology",
                "reason_for_call": "chest pain",
                "known_info": "Patient experiences chest pain during exercise",
                "unknown_info": None,
                "task_instructions": """You are a patient seeking medical advice.

Patient: I've been having chest pain when I exercise for the past week.
Physician: Can you describe the pain? Is it sharp or dull?
Patient: It's more like a pressure, right in the center of my chest.
Physician: Does the pain radiate to your arm or jaw?
Patient: Sometimes I feel it in my left shoulder.
Physician: Any shortness of breath or sweating?
Patient: A little bit of shortness when I climb stairs."""
            }
        },
        "ticket": "I've been having chest pain when I exercise for the past week. It's a pressure in the center of my chest and sometimes radiates to my left shoulder.",
        "initial_state": {
            "initialization_actions": [
                {
                    "env_type": "user",
                    "func_name": "set_user_info",
                    "arguments": {
                        "name": "Jane Smith",
                        "age": 45,
                        "gender": "female"
                    }
                }
            ]
        },
        "evaluation_criteria": {
            "actions": [
                {
                    "action_id": "assess_cardiovascular_risk",
                    "requestor": "assistant",
                    "name": "assess_cardiovascular_risk",
                    "arguments": {}
                }
            ],
            "communication_checks": [
                {
                    "check_id": "empathetic_response",
                    "criteria": "Response should show empathy and professionalism"
                }
            ]
        }
    }


def create_invalid_task_missing_fields(task_id: str) -> dict:
    """Create a task with missing required fields."""
    return {
        "id": task_id,
        "description": {
            "purpose": "Incomplete task"
        }
        # Missing: user_scenario, ticket, evaluation_criteria
    }


def create_non_medical_task(task_id: str) -> dict:
    """Create a task that's not medical-related."""
    return {
        "id": task_id,
        "description": {
            "purpose": "Technical support consultation"
        },
        "user_scenario": {
            "persona": "Computer user",
            "instructions": {
                "domain": "technical_support",
                "reason_for_call": "computer not working",
                "known_info": "Computer won't turn on",
                "unknown_info": None,
                "task_instructions": "User: My computer won't turn on"
            }
        },
        "ticket": "My computer is broken and I need help fixing it",
        "initial_state": {
            "initialization_actions": []
        },
        "evaluation_criteria": {
            "actions": []
        }
    }


def create_single_turn_task(task_id: str) -> dict:
    """Create a single-turn task (lacks multi-turn structure)."""
    return {
        "id": task_id,
        "description": {
            "purpose": "Simple medical question"
        },
        "user_scenario": {
            "persona": "Patient with a question",
            "instructions": {
                "domain": "general",
                "reason_for_call": "medication question",
                "known_info": "Patient wants to know about medication",
                "unknown_info": None,
                "task_instructions": "Single question only"
            }
        },
        "ticket": "Can I take ibuprofen with food?",
        "initial_state": {
            "initialization_actions": []
        },
        "evaluation_criteria": {
            "actions": [
                {
                    "action_id": "provide_medical_advice",
                    "requestor": "assistant",
                    "name": "provide_medical_advice",
                    "arguments": {}
                }
            ]
        }
    }


def run_validation_tests():
    """Run validation tests on various datasets."""
    print("\n" + "=" * 80)
    print("  MEDICAL DIALOGUE VALIDATOR - TEST SUITE")
    print("=" * 80 + "\n")

    validator = MedicalDialogueValidator(strict_mode=False)

    # Test 1: Valid medical dialogue dataset
    print("Test 1: Valid Multi-turn Medical Dialogue Dataset")
    print("-" * 80)
    valid_dataset = [
        create_valid_medical_task(f"valid_task_{i}")
        for i in range(1, 6)
    ]

    test_file_1 = Path("test_valid_dataset.json")
    with open(test_file_1, "w", encoding="utf-8") as f:
        json.dump(valid_dataset, f, indent=2, ensure_ascii=False)

    result_1 = validator.validate_dataset(test_file_1)
    result_1.print_report()

    # Clean up
    test_file_1.unlink()

    # Test 2: Dataset with missing fields
    print("\nTest 2: Dataset with Missing Required Fields")
    print("-" * 80)
    invalid_dataset = [
        create_invalid_task_missing_fields(f"invalid_task_{i}")
        for i in range(1, 4)
    ]

    test_file_2 = Path("test_invalid_dataset.json")
    with open(test_file_2, "w", encoding="utf-8") as f:
        json.dump(invalid_dataset, f, indent=2, ensure_ascii=False)

    result_2 = validator.validate_dataset(test_file_2)
    result_2.print_report()

    # Clean up
    test_file_2.unlink()

    # Test 3: Non-medical dataset
    print("\nTest 3: Non-Medical Dataset (Should Have Warnings)")
    print("-" * 80)
    non_medical_dataset = [
        create_non_medical_task(f"tech_task_{i}")
        for i in range(1, 4)
    ]

    test_file_3 = Path("test_non_medical_dataset.json")
    with open(test_file_3, "w", encoding="utf-8") as f:
        json.dump(non_medical_dataset, f, indent=2, ensure_ascii=False)

    result_3 = validator.validate_dataset(test_file_3)
    result_3.print_report()

    # Clean up
    test_file_3.unlink()

    # Test 4: Mixed quality dataset
    print("\nTest 4: Mixed Quality Dataset (Valid + Invalid + Single-turn)")
    print("-" * 80)
    mixed_dataset = [
        create_valid_medical_task(f"mixed_valid_{i}") for i in range(1, 4)
    ] + [
        create_single_turn_task(f"mixed_single_{i}") for i in range(1, 4)
    ] + [
        create_invalid_task_missing_fields(f"mixed_invalid_{i}") for i in range(1, 3)
    ]

    test_file_4 = Path("test_mixed_dataset.json")
    with open(test_file_4, "w", encoding="utf-8") as f:
        json.dump(mixed_dataset, f, indent=2, ensure_ascii=False)

    result_4 = validator.validate_dataset(test_file_4)
    result_4.print_report()

    # Clean up
    test_file_4.unlink()

    # Test 5: Validate actual threadmed_qa dataset
    print("\nTest 5: Actual ThReadMed-QA Dataset")
    print("-" * 80)
    threadmed_file = Path("data/tau2/domains/clinical/threadmed_qa/tasks.json")

    if threadmed_file.exists():
        result_5 = validator.validate_dataset(threadmed_file)
        result_5.print_report()
    else:
        print(f"File not found: {threadmed_file}")

    # Test 6: Validate Chinese MedDialog dataset
    print("\nTest 6: Chinese MedDialog Dataset")
    print("-" * 80)
    chinese_file = Path("data/tau2/domains/clinical/chinese_internal_medicine/tasks.json")

    if chinese_file.exists():
        result_6 = validator.validate_dataset(chinese_file)
        result_6.print_report()
    else:
        print(f"File not found: {chinese_file}")

    # Summary
    print("\n" + "=" * 80)
    print("  TEST SUMMARY")
    print("=" * 80)
    print(f"\nTests completed:")
    print(f"  Test 1 (Valid Medical): {'[PASS]' if result_1.is_valid else '[FAIL]'}")
    print(f"  Test 2 (Missing Fields): {'[Expected FAIL]' if not result_2.is_valid else '[Unexpected]'}")
    print(f"  Test 3 (Non-Medical): {'[Has Warnings]' if result_3.warnings else '[No Warnings]'}")
    print(f"  Test 4 (Mixed): {'[Has Issues]' if result_4.errors or result_4.warnings else '[No Issues]'}")

    if threadmed_file.exists():
        print(f"  Test 5 (ThReadMed-QA): {'[Valid]' if result_5.is_valid else '[Has Issues]'} ({result_5.total_tasks} tasks)")
    if chinese_file.exists():
        print(f"  Test 6 (Chinese MedDialog): {'[Valid]' if result_6.is_valid else '[Has Issues]'} ({result_6.total_tasks} tasks)")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    run_validation_tests()
