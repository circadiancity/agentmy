"""
Tool Interfaces Module for Medical Task Suite

This module provides stub interfaces for various medical systems and tools
that medical agents may interact with, including:
- HIS (Hospital Information System)
- Drug Database
- Insurance System
- OCR (Optical Character Recognition)
"""

from .his_interface import HISInterface
from .drug_database_interface import DrugDatabaseInterface
from .insurance_interface import InsuranceInterface
from .ocr_interface import OCRInterface

__all__ = [
    'HISInterface',
    'DrugDatabaseInterface',
    'InsuranceInterface',
    'OCRInterface'
]
