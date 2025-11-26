"""
WIP Visualizer
==============
Creates visualizations for Work In Progress and process metrics.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, Any
import os

from .operations import OPERATIONS, OPERATION_SEQUENCE, get_operation_by_id

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


def plot_wip_by_step(wip_data: pd.DataFrame, output_path: str = None) -> plt.Figure:
    """
    Visualize WIP by step over time.
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Stacked area chart of WIP by operation
    ax1 = axes[0]
    wip_cols = [f"{op_id}_in_progress" for op_id in OPERATION_SEQUENCE]
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(OPERATION_SEQUENCE)))
    
    wip_data_plot = wip_data.set_index("timestamp")[wip_cols]
    wip_data_plot.columns = [get_operation_by_id(op_id).name for op_id in OPERATION_SEQUENCE]
    
    wip_data_plot.plot(kind="area", stacked=True, ax=ax1, alpha=0.7, color=colors)
    ax1.set_xlabel("Time", fontsize=12)
    ax1.set_ylabel("Work In Progress (Units)", fontsize=12)
    ax1.set_title("WIP by Operation Over Time", fontsize=14, fontweight="bold")
    ax1.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=10)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Plot 2: Total WIP over time
    ax2 = axes[1]
    ax2.plot(wip_data["timestamp"], wip_data["total_wip"], 
             color="steelblue", linewidth=2, label="Total WIP")
    ax2.fill_between(wip_data["timestamp"], wip_data["total_wip"], 
                     alpha=0.3, color="steelblue")
    ax2.axhline(y=wip_data["total_wip"].mean(), color="red", 
                linestyle="--", label=f"Average: {wip_data['total_wip'].mean():.1f}")
    ax2.set_xlabel("Time", fontsize=12)
    ax2.set_ylabel("Total WIP (Units)", fontsize=12)
    ax2.set_title("Total Work In Progress Over Time", fontsize=14, fontweight="bold")
    ax2.legend(loc="upper right")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"WIP chart saved to {output_path}")
    
    return fig


def plot_bottleneck_analysis(bottleneck_df: pd.DataFrame, output_path: str = None) -> plt.Figure:
    """
    Visualize bottleneck analysis results.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # Define color mapping for severity
    severity_colors = {
        "Critical": "#d62728",  # Red
        "High": "#ff7f0e",      # Orange
        "Medium": "#ffbb78",    # Light orange
        "None": "#2ca02c"       # Green
    }
    colors = [severity_colors.get(s, "#1f77b4") for s in bottleneck_df["severity"]]
    
    # Plot 1: Wait Time vs Cycle Time
    ax1 = axes[0, 0]
    x_pos = range(len(bottleneck_df))
    width = 0.35
    
    bars1 = ax1.bar([x - width/2 for x in x_pos], bottleneck_df["avg_cycle_time"], 
                    width, label="Avg Cycle Time", color="steelblue")
    bars2 = ax1.bar([x + width/2 for x in x_pos], bottleneck_df["avg_wait_time"], 
                    width, label="Avg Wait Time", color="coral")
    
    ax1.set_xlabel("Operation", fontsize=11)
    ax1.set_ylabel("Time (minutes)", fontsize=11)
    ax1.set_title("Cycle Time vs Wait Time by Operation", fontsize=12, fontweight="bold")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(bottleneck_df["operation_id"], rotation=45, ha="right")
    ax1.legend()
    
    # Add reference marker for bottlenecks
    for i, (_, row) in enumerate(bottleneck_df.iterrows()):
        if row["is_bottleneck"]:
            ax1.annotate("*", (i, max(row["avg_cycle_time"], row["avg_wait_time"]) + 2),
                        ha="center", fontsize=14, fontweight="bold", color="red")
    
    # Plot 2: Wait-to-Cycle Ratio
    ax2 = axes[0, 1]
    x_pos2 = range(len(bottleneck_df))
    bars = ax2.bar(x_pos2, bottleneck_df["wait_cycle_ratio"], 
                   color=colors, edgecolor="black", linewidth=0.5)
    ax2.axhline(y=1.0, color="red", linestyle="--", linewidth=2, 
                label="Critical Threshold (ratio=1)")
    ax2.set_xlabel("Operation", fontsize=11)
    ax2.set_ylabel("Wait/Cycle Ratio", fontsize=11)
    ax2.set_title("Wait-to-Cycle Time Ratio (Bottleneck Indicator)", fontsize=12, fontweight="bold")
    ax2.set_xticks(x_pos2)
    ax2.set_xticklabels(bottleneck_df["operation_id"], rotation=45, ha="right")
    ax2.legend()
    
    # Plot 3: Utilization
    ax3 = axes[1, 0]
    x_pos3 = range(len(bottleneck_df))
    bars = ax3.bar(x_pos3, bottleneck_df["utilization_pct"], 
                   color=colors, edgecolor="black", linewidth=0.5)
    ax3.axhline(y=85, color="orange", linestyle="--", linewidth=2, 
                label="High Utilization (85%)")
    ax3.axhline(y=95, color="red", linestyle="--", linewidth=2, 
                label="Critical Utilization (95%)")
    ax3.set_xlabel("Operation", fontsize=11)
    ax3.set_ylabel("Utilization (%)", fontsize=11)
    ax3.set_title("Workstation Utilization by Operation", fontsize=12, fontweight="bold")
    ax3.set_xticks(x_pos3)
    ax3.set_xticklabels(bottleneck_df["operation_id"], rotation=45, ha="right")
    ax3.set_ylim(0, 110)
    ax3.legend()
    
    # Plot 4: Severity Summary
    ax4 = axes[1, 1]
    severity_counts = bottleneck_df["severity"].value_counts()
    severity_order = ["Critical", "High", "Medium", "None"]
    severity_counts = severity_counts.reindex(severity_order).fillna(0)
    
    wedges, texts, autotexts = ax4.pie(
        severity_counts.values,
        labels=severity_counts.index,
        autopct=lambda pct: f'{int(pct/100*sum(severity_counts.values))}\n({pct:.0f}%)',
        colors=[severity_colors[s] for s in severity_counts.index],
        explode=[0.05 if s in ["Critical", "High"] else 0 for s in severity_counts.index],
        startangle=90
    )
    ax4.set_title("Bottleneck Severity Distribution", fontsize=12, fontweight="bold")
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Bottleneck analysis chart saved to {output_path}")
    
    return fig


def plot_rework_analysis(rework_df: pd.DataFrame, output_path: str = None) -> plt.Figure:
    """
    Visualize rework sources.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Expected vs Actual Rework Rate
    ax1 = axes[0]
    x_pos = range(len(rework_df))
    width = 0.35
    
    bars1 = ax1.bar([x - width/2 for x in x_pos], rework_df["expected_defect_rate_pct"], 
                    width, label="Expected Defect Rate", color="lightblue", edgecolor="steelblue")
    bars2 = ax1.bar([x + width/2 for x in x_pos], rework_df["actual_rework_rate_pct"], 
                    width, label="Actual Rework Rate", color="salmon", edgecolor="darkred")
    
    ax1.set_xlabel("Operation", fontsize=11)
    ax1.set_ylabel("Rate (%)", fontsize=11)
    ax1.set_title("Expected Defect Rate vs Actual Rework Rate", fontsize=12, fontweight="bold")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(rework_df["operation_id"], rotation=45, ha="right")
    ax1.legend()
    
    # Plot 2: Rework Time Cost
    ax2 = axes[1]
    colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(rework_df)))
    bars = ax2.barh(rework_df["operation_name"], rework_df["rework_time_hours"], 
                    color=colors, edgecolor="darkred", linewidth=0.5)
    
    ax2.set_xlabel("Rework Time (hours)", fontsize=11)
    ax2.set_ylabel("Operation", fontsize=11)
    ax2.set_title("Rework Time Cost by Operation", fontsize=12, fontweight="bold")
    
    # Add value labels
    for bar, value in zip(bars, rework_df["rework_time_hours"]):
        ax2.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{value:.1f}h', va='center', fontsize=10)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Rework analysis chart saved to {output_path}")
    
    return fig


def plot_flow_statistics(flow_stats: Dict[str, Any], output_path: str = None) -> plt.Figure:
    """
    Visualize flow statistics.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # Plot 1: Volume per Operation
    ax1 = axes[0, 0]
    volume_df = flow_stats["volume_per_operation"]
    colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(volume_df)))
    
    bars = ax1.bar(volume_df["operation_id"], volume_df["total_events"], 
                   color=colors, edgecolor="navy", linewidth=0.5)
    ax1.set_xlabel("Operation", fontsize=11)
    ax1.set_ylabel("Number of Events", fontsize=11)
    ax1.set_title("Volume (Total Events) per Operation", fontsize=12, fontweight="bold")
    
    # Plot 2: Time Statistics
    ax2 = axes[0, 1]
    time_df = flow_stats["time_statistics"]
    
    ax2.errorbar(time_df["operation_id"], time_df["avg_cycle_time"],
                yerr=time_df["std_cycle_time"], fmt='o-', capsize=5,
                label="Avg Cycle Time ± Std", color="steelblue", markersize=8)
    ax2.scatter(time_df["operation_id"], time_df["median_cycle_time"],
               marker='s', s=60, color="orange", label="Median Cycle Time", zorder=5)
    
    ax2.set_xlabel("Operation", fontsize=11)
    ax2.set_ylabel("Time (minutes)", fontsize=11)
    ax2.set_title("Cycle Time Statistics by Operation", fontsize=12, fontweight="bold")
    ax2.legend()
    ax2.set_xticks(range(len(time_df)))
    ax2.set_xticklabels(time_df["operation_id"], rotation=45, ha="right")
    
    # Plot 3: Process Variants
    ax3 = axes[1, 0]
    variants_df = flow_stats["process_variants"].head(5)  # Top 5 variants
    
    bars = ax3.barh(range(len(variants_df)), variants_df["percentage"], color="teal")
    ax3.set_yticks(range(len(variants_df)))
    
    # Truncate long trace names
    trace_labels = [trace[:40] + "..." if len(trace) > 40 else trace 
                   for trace in variants_df["trace"]]
    ax3.set_yticklabels(trace_labels, fontsize=9)
    
    ax3.set_xlabel("Percentage of Cases (%)", fontsize=11)
    ax3.set_ylabel("Process Variant", fontsize=11)
    ax3.set_title("Top 5 Process Variants", fontsize=12, fontweight="bold")
    
    for bar, pct, count in zip(bars, variants_df["percentage"], variants_df["count"]):
        ax3.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{pct:.1f}% (n={count})', va='center', fontsize=9)
    
    # Plot 4: Standard vs Non-Standard Flow
    ax4 = axes[1, 1]
    standard_pct = flow_stats["standard_flow_percentage"]
    non_standard_pct = 100 - standard_pct
    
    wedges, texts, autotexts = ax4.pie(
        [standard_pct, non_standard_pct],
        labels=["Standard Flow", "Non-Standard Flow\n(includes rework)"],
        autopct='%1.1f%%',
        colors=["#2ca02c", "#d62728"],
        explode=[0, 0.05],
        startangle=90
    )
    ax4.set_title("Process Flow Conformance", fontsize=12, fontweight="bold")
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Flow statistics chart saved to {output_path}")
    
    return fig


def plot_lead_time_distribution(lead_times: pd.DataFrame, output_path: str = None) -> plt.Figure:
    """
    Visualize lead time distribution.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Histogram
    ax1 = axes[0]
    ax1.hist(lead_times["lead_time_hours"], bins=30, color="steelblue", 
             edgecolor="navy", alpha=0.7)
    ax1.axvline(lead_times["lead_time_hours"].mean(), color="red", linestyle="--",
               linewidth=2, label=f'Mean: {lead_times["lead_time_hours"].mean():.2f}h')
    ax1.axvline(lead_times["lead_time_hours"].median(), color="orange", linestyle="--",
               linewidth=2, label=f'Median: {lead_times["lead_time_hours"].median():.2f}h')
    ax1.set_xlabel("Lead Time (hours)", fontsize=11)
    ax1.set_ylabel("Frequency", fontsize=11)
    ax1.set_title("Lead Time Distribution", fontsize=12, fontweight="bold")
    ax1.legend()
    
    # Plot 2: Box plot with components
    ax2 = axes[1]
    components = ["total_wait_time", "total_cycle_time"]
    component_names = ["Wait Time", "Cycle Time"]
    
    data = [lead_times[col] for col in components]
    bp = ax2.boxplot(data, labels=component_names, patch_artist=True)
    
    colors = ["coral", "steelblue"]
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax2.set_ylabel("Time (minutes)", fontsize=11)
    ax2.set_title("Wait Time vs Cycle Time Components", fontsize=12, fontweight="bold")
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Lead time distribution chart saved to {output_path}")
    
    return fig


def create_all_visualizations(
    event_log: pd.DataFrame,
    lead_times: pd.DataFrame,
    wip_data: pd.DataFrame,
    bottleneck_analysis: Dict[str, Any],
    rework_df: pd.DataFrame,
    flow_stats: Dict[str, Any],
    output_dir: str = "reports"
) -> None:
    """
    Create all visualizations and save to output directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate all plots
    plot_wip_by_step(wip_data, os.path.join(output_dir, "wip_analysis.png"))
    plot_bottleneck_analysis(bottleneck_analysis["bottleneck_analysis"], 
                            os.path.join(output_dir, "bottleneck_analysis.png"))
    plot_rework_analysis(rework_df, os.path.join(output_dir, "rework_analysis.png"))
    plot_flow_statistics(flow_stats, os.path.join(output_dir, "flow_statistics.png"))
    plot_lead_time_distribution(lead_times, os.path.join(output_dir, "lead_time_distribution.png"))
    
    print(f"\nAll visualizations saved to {output_dir}/")
    
    # Close all figures to free memory
    plt.close("all")
