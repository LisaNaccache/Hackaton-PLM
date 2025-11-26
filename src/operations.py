"""
Digital Twin Operations Configuration
======================================
Defines the 6 workshop operations from a digital twin manufacturing process.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Operation:
    """Represents a workshop operation with its characteristics."""
    id: str
    name: str
    name_fr: str
    avg_duration_minutes: float
    std_deviation_minutes: float
    setup_time_minutes: float
    defect_rate: float  # Probability of defect (causing rework)
    workstation_count: int


# Define 6 workshop operations (chain from digital twin)
OPERATIONS: List[Operation] = [
    Operation(
        id="OP1",
        name="Raw Material Preparation",
        name_fr="Préparation Matière Première",
        avg_duration_minutes=15.0,
        std_deviation_minutes=3.0,
        setup_time_minutes=5.0,
        defect_rate=0.02,
        workstation_count=2
    ),
    Operation(
        id="OP2",
        name="CNC Machining",
        name_fr="Usinage CNC",
        avg_duration_minutes=45.0,
        std_deviation_minutes=8.0,
        setup_time_minutes=10.0,
        defect_rate=0.05,
        workstation_count=3
    ),
    Operation(
        id="OP3",
        name="Heat Treatment",
        name_fr="Traitement Thermique",
        avg_duration_minutes=90.0,
        std_deviation_minutes=10.0,
        setup_time_minutes=15.0,
        defect_rate=0.03,
        workstation_count=1
    ),
    Operation(
        id="OP4",
        name="Surface Finishing",
        name_fr="Finition de Surface",
        avg_duration_minutes=30.0,
        std_deviation_minutes=5.0,
        setup_time_minutes=8.0,
        defect_rate=0.04,
        workstation_count=2
    ),
    Operation(
        id="OP5",
        name="Quality Control",
        name_fr="Contrôle Qualité",
        avg_duration_minutes=20.0,
        std_deviation_minutes=4.0,
        setup_time_minutes=3.0,
        defect_rate=0.0,  # QC doesn't produce defects, it detects them
        workstation_count=2
    ),
    Operation(
        id="OP6",
        name="Assembly & Packaging",
        name_fr="Assemblage et Conditionnement",
        avg_duration_minutes=25.0,
        std_deviation_minutes=5.0,
        setup_time_minutes=5.0,
        defect_rate=0.02,
        workstation_count=2
    ),
]


# Operation sequence (standard flow)
OPERATION_SEQUENCE = ["OP1", "OP2", "OP3", "OP4", "OP5", "OP6"]

# Rework routing: if defect detected at QC, which operation to return to
REWORK_ROUTES = {
    "OP2": "OP2",  # CNC defects -> redo CNC
    "OP3": "OP3",  # Heat treatment defects -> redo heat treatment
    "OP4": "OP4",  # Surface defects -> redo surface finishing
}


def get_operation_by_id(op_id: str) -> Operation:
    """Get an operation by its ID."""
    for op in OPERATIONS:
        if op.id == op_id:
            return op
    raise ValueError(f"Operation not found: {op_id}")


def get_operation_index(op_id: str) -> int:
    """Get the index of an operation in the sequence."""
    return OPERATION_SEQUENCE.index(op_id)


def get_next_operation(current_op_id: str) -> str:
    """Get the next operation in the sequence."""
    idx = get_operation_index(current_op_id)
    if idx < len(OPERATION_SEQUENCE) - 1:
        return OPERATION_SEQUENCE[idx + 1]
    return None


def get_theoretical_lead_time() -> Tuple[float, str]:
    """Calculate theoretical minimum lead time (without queues/rework)."""
    total_time = sum(op.avg_duration_minutes + op.setup_time_minutes for op in OPERATIONS)
    return total_time, f"{total_time:.1f} minutes ({total_time/60:.2f} hours)"
