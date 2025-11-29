"""
Event Log Generator
===================
Generates structured event logs simulating a digital twin manufacturing process.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from .operations import (
    OPERATIONS, OPERATION_SEQUENCE, REWORK_ROUTES,
    get_operation_by_id, get_next_operation, get_operation_index
)


def generate_event_log(
    num_cases: int = 500,
    start_date: datetime = datetime(2024, 1, 1, 8, 0, 0),
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a structured event log simulating manufacturing operations.
    
    Event Log Structure (XES-compatible):
    - case_id: Unique identifier for each product/order
    - activity: Operation name
    - operation_id: Operation identifier
    - timestamp_start: Start time of activity
    - timestamp_end: End time of activity
    - resource: Workstation used
    - is_rework: Whether this is a rework iteration
    - rework_count: Number of times this operation was done for this case
    - wait_time_minutes: Time spent waiting before this operation
    - cycle_time_minutes: Actual processing time
    - defect_detected: Whether a defect was detected (for QC)
    
    Args:
        num_cases: Number of product cases to generate
        start_date: Simulation start date
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with structured event log
    """
    random.seed(seed)
    np.random.seed(seed)
    
    events = []
    
    # Track workstation availability (end time for each workstation)
    workstation_availability: Dict[str, List[datetime]] = {}
    for op in OPERATIONS:
        workstation_availability[op.id] = [start_date] * op.workstation_count
    
    # Track current time for case arrivals
    case_arrival_time = start_date
    
    for case_num in range(1, num_cases + 1):
        case_id = f"CASE-{case_num:04d}"
        
        # Cases arrive with some inter-arrival time (Poisson-like)
        inter_arrival_minutes = np.random.exponential(30)  # Average 30 min between cases
        case_arrival_time += timedelta(minutes=inter_arrival_minutes)
        
        # Reset for each case
        current_time = case_arrival_time
        operation_counts = {op_id: 0 for op_id in OPERATION_SEQUENCE}
        defects_by_op = {}  # Track which operations had defects
        
        # Process through operations
        op_idx = 0
        while op_idx < len(OPERATION_SEQUENCE):
            op_id = OPERATION_SEQUENCE[op_idx]
            op = get_operation_by_id(op_id)
            operation_counts[op_id] += 1
            is_rework = operation_counts[op_id] > 1
            
            # Find earliest available workstation
            ws_availability = workstation_availability[op_id]
            earliest_ws_idx = min(range(len(ws_availability)), key=lambda i: ws_availability[i])
            earliest_available = ws_availability[earliest_ws_idx]
            
            # Wait time if workstation is busy
            wait_time = max(0, (earliest_available - current_time).total_seconds() / 60)
            operation_start = max(current_time, earliest_available)
            
            # Generate operation duration with variability
            cycle_time = max(5, np.random.normal(op.avg_duration_minutes, op.std_deviation_minutes))
            
            # Add setup time
            total_time = cycle_time + op.setup_time_minutes
            operation_end = operation_start + timedelta(minutes=total_time)
            
            # Update workstation availability
            workstation_availability[op_id][earliest_ws_idx] = operation_end
            
            # Check for defects (at QC, we detect defects from previous operations)
            defect_detected = False
            if op_id == "OP5":  # Quality Control
                # Check if any previous operation had a defect
                for prev_op_id, had_defect in defects_by_op.items():
                    if had_defect and random.random() < 0.8:  # 80% detection rate
                        defect_detected = True
                        # Route to rework
                        rework_op = REWORK_ROUTES.get(prev_op_id, prev_op_id)
                        op_idx = get_operation_index(rework_op) - 1  # Will increment below
                        defects_by_op[prev_op_id] = False  # Clear the defect
                        break
            else:
                # Generate potential defect
                if random.random() < op.defect_rate:
                    defects_by_op[op_id] = True
            
            # Record event
            events.append({
                "case_id": case_id,
                "activity": op.name,
                "activity_fr": op.name_fr,
                "operation_id": op_id,
                "timestamp_start": operation_start,
                "timestamp_end": operation_end,
                "resource": f"{op_id}_WS{earliest_ws_idx + 1}",
                "is_rework": is_rework,
                "rework_count": operation_counts[op_id],
                "wait_time_minutes": round(wait_time, 2),
                "cycle_time_minutes": round(cycle_time, 2),
                "setup_time_minutes": round(op.setup_time_minutes, 2),
                "total_time_minutes": round(total_time, 2),
                "defect_detected": defect_detected
            })
            
            # Update current time and move to next operation
            current_time = operation_end
            op_idx += 1
    
    # Create DataFrame
    df = pd.DataFrame(events)
    
    # Sort by timestamp
    df = df.sort_values(["timestamp_start", "case_id"]).reset_index(drop=True)
    
    # Add derived columns
    df["duration_minutes"] = (df["timestamp_end"] - df["timestamp_start"]).dt.total_seconds() / 60
    
    return df


def calculate_case_lead_times(event_log: pd.DataFrame) -> pd.DataFrame:
    """Calculate lead time for each case."""
    lead_times = event_log.groupby("case_id").agg(
        start_time=("timestamp_start", "min"),
        end_time=("timestamp_end", "max"),
        total_operations=("activity", "count"),
        total_reworks=("is_rework", "sum"),
        total_wait_time=("wait_time_minutes", "sum"),
        total_cycle_time=("cycle_time_minutes", "sum")
    ).reset_index()
    
    lead_times["lead_time_minutes"] = (
        lead_times["end_time"] - lead_times["start_time"]
    ).dt.total_seconds() / 60
    
    lead_times["lead_time_hours"] = lead_times["lead_time_minutes"] / 60
    
    return lead_times


def export_event_log(df: pd.DataFrame, filepath: str) -> None:
    """Export event log to CSV."""
    df.to_csv(filepath, index=False)
    print(f"Event log exported to {filepath}")


if __name__ == "__main__":
    # Generate sample event log
    event_log = generate_event_log(num_cases=500)
    print(f"Generated {len(event_log)} events for {event_log['case_id'].nunique()} cases")
    print("\nEvent Log Structure:")
    print(event_log.info())
    print("\nSample Events:")
    print(event_log.head(10))
