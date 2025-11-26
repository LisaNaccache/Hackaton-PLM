"""
Process Flow Analyzer
=====================
Discovers real flow, calculates metrics, and identifies bottlenecks.
"""

from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .operations import OPERATIONS, OPERATION_SEQUENCE, get_operation_by_id


def discover_real_flow(event_log: pd.DataFrame) -> Dict[str, Any]:
    """
    Discover the real process flow from the event log.
    
    Returns statistics on:
    - Volume per operation
    - Average/median times
    - Flow variants
    """
    results = {}
    
    # Volume per operation
    volume_per_op = event_log.groupby("operation_id").agg(
        total_events=("case_id", "count"),
        unique_cases=("case_id", "nunique"),
        rework_events=("is_rework", "sum")
    ).reset_index()
    
    results["volume_per_operation"] = volume_per_op
    
    # Time statistics per operation
    time_stats = event_log.groupby("operation_id").agg(
        avg_cycle_time=("cycle_time_minutes", "mean"),
        median_cycle_time=("cycle_time_minutes", "median"),
        std_cycle_time=("cycle_time_minutes", "std"),
        avg_wait_time=("wait_time_minutes", "mean"),
        median_wait_time=("wait_time_minutes", "median"),
        max_wait_time=("wait_time_minutes", "max"),
        avg_total_time=("total_time_minutes", "mean")
    ).reset_index()
    
    results["time_statistics"] = time_stats
    
    # Process variants (unique traces)
    traces = event_log.groupby("case_id")["operation_id"].apply(
        lambda x: " -> ".join(x.tolist())
    ).reset_index()
    traces.columns = ["case_id", "trace"]
    
    variant_counts = traces.groupby("trace").size().reset_index(name="count")
    variant_counts = variant_counts.sort_values("count", ascending=False)
    variant_counts["percentage"] = (variant_counts["count"] / len(traces) * 100).round(2)
    
    results["process_variants"] = variant_counts
    
    # Standard vs non-standard flow
    standard_trace = " -> ".join(OPERATION_SEQUENCE)
    standard_cases = traces[traces["trace"] == standard_trace]["case_id"].nunique()
    results["standard_flow_percentage"] = round(standard_cases / len(traces) * 100, 2)
    
    return results


def calculate_wip_by_step(event_log: pd.DataFrame, time_interval_minutes: int = 60) -> pd.DataFrame:
    """
    Calculate Work In Progress (WIP) by step over time.
    
    Creates snapshots at regular intervals showing how many cases
    are at each operation stage.
    """
    start_time = event_log["timestamp_start"].min()
    end_time = event_log["timestamp_end"].max()
    
    # Generate time points
    time_points = []
    current_time = start_time
    while current_time <= end_time:
        time_points.append(current_time)
        current_time += timedelta(minutes=time_interval_minutes)
    
    wip_data = []
    
    for time_point in time_points:
        # For each time point, count cases currently at each operation
        wip_at_time = {"timestamp": time_point}
        
        for op_id in OPERATION_SEQUENCE:
            # Cases currently being processed at this operation
            in_progress = len(event_log[
                (event_log["operation_id"] == op_id) &
                (event_log["timestamp_start"] <= time_point) &
                (event_log["timestamp_end"] > time_point)
            ])
            wip_at_time[f"{op_id}_in_progress"] = in_progress
            
            # Cases waiting (completed previous op, not yet started this op)
            # This is more complex - we need to track case state
        
        # Total WIP
        wip_at_time["total_wip"] = sum(
            wip_at_time[f"{op_id}_in_progress"] for op_id in OPERATION_SEQUENCE
        )
        
        wip_data.append(wip_at_time)
    
    return pd.DataFrame(wip_data)


def calculate_queue_lengths(event_log: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate queue lengths before each operation.
    
    Queue length = cases waiting to start an operation
    """
    queue_data = []
    
    for op_id in OPERATION_SEQUENCE:
        op_events = event_log[event_log["operation_id"] == op_id].copy()
        
        # Cases with significant wait time indicate queueing
        avg_queue = (op_events["wait_time_minutes"] > 5).sum()  # Arbitrary threshold
        
        queue_data.append({
            "operation_id": op_id,
            "operation_name": get_operation_by_id(op_id).name,
            "avg_wait_time": op_events["wait_time_minutes"].mean(),
            "max_wait_time": op_events["wait_time_minutes"].max(),
            "cases_with_wait": (op_events["wait_time_minutes"] > 5).sum(),
            "pct_cases_waiting": round((op_events["wait_time_minutes"] > 5).mean() * 100, 2)
        })
    
    return pd.DataFrame(queue_data)


def identify_bottlenecks(event_log: pd.DataFrame) -> Dict[str, Any]:
    """
    Identify bottlenecks in the process.
    
    Bottleneck indicators:
    1. High wait time relative to cycle time (wait > cycle)
    2. Persistent queues (consistently high wait times)
    3. High utilization (close to 100%)
    4. Low throughput relative to capacity
    """
    bottlenecks = []
    
    for op_id in OPERATION_SEQUENCE:
        op = get_operation_by_id(op_id)
        op_events = event_log[event_log["operation_id"] == op_id]
        
        avg_wait = op_events["wait_time_minutes"].mean()
        avg_cycle = op_events["cycle_time_minutes"].mean()
        max_wait = op_events["wait_time_minutes"].max()
        
        # Calculate wait-to-cycle ratio
        wait_cycle_ratio = avg_wait / avg_cycle if avg_cycle > 0 else 0
        
        # Calculate utilization estimate
        total_processing_time = op_events["total_time_minutes"].sum()
        time_span = (op_events["timestamp_end"].max() - op_events["timestamp_start"].min()).total_seconds() / 60
        utilization = (total_processing_time / (time_span * op.workstation_count)) * 100 if time_span > 0 else 0
        
        # Determine bottleneck severity
        is_bottleneck = False
        severity = "None"
        reasons = []
        
        if wait_cycle_ratio > 1.0:
            is_bottleneck = True
            reasons.append(f"Wait time ({avg_wait:.1f}min) exceeds cycle time ({avg_cycle:.1f}min)")
            
        if max_wait > avg_cycle * 3:
            is_bottleneck = True
            reasons.append(f"Max wait ({max_wait:.1f}min) is 3x+ cycle time")
            
        if utilization > 85:
            is_bottleneck = True
            reasons.append(f"High utilization ({utilization:.1f}%)")
        
        if is_bottleneck:
            if wait_cycle_ratio > 2.0 or utilization > 95:
                severity = "Critical"
            elif wait_cycle_ratio > 1.0 or utilization > 85:
                severity = "High"
            else:
                severity = "Medium"
        
        bottlenecks.append({
            "operation_id": op_id,
            "operation_name": op.name,
            "operation_name_fr": op.name_fr,
            "avg_wait_time": round(avg_wait, 2),
            "avg_cycle_time": round(avg_cycle, 2),
            "wait_cycle_ratio": round(wait_cycle_ratio, 3),
            "max_wait_time": round(max_wait, 2),
            "utilization_pct": round(utilization, 2),
            "workstation_count": op.workstation_count,
            "is_bottleneck": is_bottleneck,
            "severity": severity,
            "reasons": "; ".join(reasons) if reasons else "N/A"
        })
    
    bottleneck_df = pd.DataFrame(bottlenecks)
    
    # Sort by severity
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "None": 3}
    bottleneck_df["severity_rank"] = bottleneck_df["severity"].map(severity_order)
    bottleneck_df = bottleneck_df.sort_values("severity_rank").drop(columns=["severity_rank"])
    
    return {
        "bottleneck_analysis": bottleneck_df,
        "critical_bottlenecks": bottleneck_df[bottleneck_df["severity"] == "Critical"]["operation_name"].tolist(),
        "high_bottlenecks": bottleneck_df[bottleneck_df["severity"] == "High"]["operation_name"].tolist()
    }


def identify_rework_sources(event_log: pd.DataFrame) -> pd.DataFrame:
    """
    Identify operations that are sources of rework.
    """
    rework_data = []
    
    for op_id in OPERATION_SEQUENCE:
        op = get_operation_by_id(op_id)
        op_events = event_log[event_log["operation_id"] == op_id]
        
        total_passes = len(op_events)
        first_passes = len(op_events[op_events["rework_count"] == 1])
        rework_passes = len(op_events[op_events["is_rework"] == True])
        
        rework_rate = (rework_passes / first_passes * 100) if first_passes > 0 else 0
        
        # Calculate rework cost (extra time spent)
        rework_time = op_events[op_events["is_rework"] == True]["total_time_minutes"].sum()
        
        rework_data.append({
            "operation_id": op_id,
            "operation_name": op.name,
            "expected_defect_rate_pct": op.defect_rate * 100,
            "total_passes": total_passes,
            "first_passes": first_passes,
            "rework_passes": rework_passes,
            "actual_rework_rate_pct": round(rework_rate, 2),
            "rework_time_minutes": round(rework_time, 2),
            "rework_time_hours": round(rework_time / 60, 2)
        })
    
    return pd.DataFrame(rework_data)


def calculate_overall_metrics(event_log: pd.DataFrame, lead_times: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate overall process metrics.
    """
    metrics = {}
    
    # Lead time metrics
    metrics["avg_lead_time_hours"] = round(lead_times["lead_time_hours"].mean(), 2)
    metrics["median_lead_time_hours"] = round(lead_times["lead_time_hours"].median(), 2)
    metrics["min_lead_time_hours"] = round(lead_times["lead_time_hours"].min(), 2)
    metrics["max_lead_time_hours"] = round(lead_times["lead_time_hours"].max(), 2)
    metrics["std_lead_time_hours"] = round(lead_times["lead_time_hours"].std(), 2)
    
    # WIP metrics
    metrics["total_cases"] = lead_times["case_id"].nunique()
    metrics["total_events"] = len(event_log)
    
    # Rework metrics
    metrics["total_rework_events"] = event_log["is_rework"].sum()
    metrics["rework_rate_pct"] = round(
        event_log["is_rework"].sum() / len(event_log) * 100, 2
    )
    
    # Wait time metrics
    metrics["total_wait_time_hours"] = round(event_log["wait_time_minutes"].sum() / 60, 2)
    metrics["avg_wait_per_case_minutes"] = round(
        lead_times["total_wait_time"].mean(), 2
    )
    
    # Process efficiency
    value_add_time = event_log["cycle_time_minutes"].sum()
    total_time = value_add_time + event_log["wait_time_minutes"].sum() + event_log["setup_time_minutes"].sum()
    metrics["process_efficiency_pct"] = round(value_add_time / total_time * 100, 2) if total_time > 0 else 0
    
    return metrics


if __name__ == "__main__":
    from .event_log_generator import generate_event_log, calculate_case_lead_times
    
    # Generate event log
    event_log = generate_event_log(num_cases=500)
    lead_times = calculate_case_lead_times(event_log)
    
    # Analyze
    flow = discover_real_flow(event_log)
    bottlenecks = identify_bottlenecks(event_log)
    rework = identify_rework_sources(event_log)
    metrics = calculate_overall_metrics(event_log, lead_times)
    
    print("=== Flow Discovery ===")
    print(flow["volume_per_operation"])
    
    print("\n=== Bottlenecks ===")
    print(bottlenecks["bottleneck_analysis"])
    
    print("\n=== Rework Sources ===")
    print(rework)
    
    print("\n=== Overall Metrics ===")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
