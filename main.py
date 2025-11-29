#!/usr/bin/env python3
"""
PLM AI Process Mining - Main Entry Point
=========================================
A comprehensive process mining solution for manufacturing workflow analysis.

Features:
1. Define 4-8 workshop operations (digital twin simulation)
2. Structure and generate event logs
3. Discover real flow (volumes, average times) and visualize WIP
4. Identify bottlenecks and rework sources
5. Generate AI-powered optimization report
6. Present success KPIs: ΔWIP, Δlead time, top 3 actions

Usage:
    python main.py [--cases N] [--output-dir DIR]
"""

import argparse
import os
import sys
from datetime import datetime

from src.operations import OPERATIONS, OPERATION_SEQUENCE, get_theoretical_lead_time
from src.event_log_generator import generate_event_log, calculate_case_lead_times, export_event_log
from src.process_analyzer import (
    discover_real_flow,
    calculate_wip_by_step,
    identify_bottlenecks,
    identify_rework_sources,
    calculate_overall_metrics
)
from src.visualizer import create_all_visualizations
from src.report_generator import generate_full_report


def print_banner():
    """Print application banner."""
    print("=" * 70)
    print("  PLM AI Process Mining - Manufacturing Workflow Analyzer")
    print("  Version 1.0.0")
    print("=" * 70)
    print()


def print_operations_chain():
    """Print the defined operations chain."""
    print("📋 CHAÎNE D'OPÉRATIONS / OPERATIONS CHAIN")
    print("-" * 50)
    print(f"Nombre d'opérations: {len(OPERATIONS)}")
    print(f"Séquence standard: {' → '.join(OPERATION_SEQUENCE)}")
    print()
    
    for op in OPERATIONS:
        print(f"  {op.id}: {op.name_fr}")
        print(f"      ({op.name})")
        print(f"      Durée: {op.avg_duration_minutes}min ± {op.std_deviation_minutes}min")
        print(f"      Postes de travail: {op.workstation_count}")
        print(f"      Taux de défaut: {op.defect_rate * 100:.1f}%")
        print()
    
    theoretical_time, theoretical_str = get_theoretical_lead_time()
    print(f"⏱️  Lead time théorique minimum: {theoretical_str}")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PLM AI Process Mining - Manufacturing Workflow Analyzer"
    )
    parser.add_argument(
        "--cases", type=int, default=500,
        help="Number of cases to simulate (default: 500)"
    )
    parser.add_argument(
        "--output-dir", type=str, default="reports",
        help="Output directory for reports and visualizations (default: reports)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    args = parser.parse_args()
    
    print_banner()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # =========================================================================
    # Step 1: Define Operations Chain (from Digital Twin)
    # =========================================================================
    print("=" * 70)
    print("ÉTAPE 1: Définition de la chaîne d'opérations")
    print("=" * 70)
    print_operations_chain()
    
    # =========================================================================
    # Step 2: Generate and Structure Event Log
    # =========================================================================
    print("=" * 70)
    print("ÉTAPE 2: Génération et structuration de l'event log")
    print("=" * 70)
    
    print(f"Génération de {args.cases} cas...")
    event_log = generate_event_log(num_cases=args.cases, seed=args.seed)
    lead_times = calculate_case_lead_times(event_log)
    
    print(f"✓ {len(event_log)} événements générés pour {event_log['case_id'].nunique()} cas")
    print(f"\nStructure de l'event log:")
    print(f"  - Colonnes: {', '.join(event_log.columns[:8])}...")
    print(f"  - Période: {event_log['timestamp_start'].min()} to {event_log['timestamp_end'].max()}")
    
    # Export event log
    event_log_path = os.path.join("data", "event_log.csv")
    export_event_log(event_log, event_log_path)
    print()
    
    # =========================================================================
    # Step 3: Discover Real Flow and Calculate WIP
    # =========================================================================
    print("=" * 70)
    print("ÉTAPE 3: Découverte du flux réel et calcul du WIP")
    print("=" * 70)
    
    flow_stats = discover_real_flow(event_log)
    wip_data = calculate_wip_by_step(event_log)
    
    print("\n📊 Volumes par opération:")
    print(flow_stats["volume_per_operation"].to_string(index=False))
    
    print("\n⏱️ Temps moyens par opération (minutes):")
    time_stats = flow_stats["time_statistics"][["operation_id", "avg_cycle_time", "avg_wait_time"]]
    print(time_stats.to_string(index=False))
    
    print(f"\n📈 Conformité au flux standard: {flow_stats['standard_flow_percentage']:.1f}%")
    print()
    
    # =========================================================================
    # Step 4: Identify Bottlenecks and Rework Sources
    # =========================================================================
    print("=" * 70)
    print("ÉTAPE 4: Identification des goulots et sources de reprise")
    print("=" * 70)
    
    bottleneck_analysis = identify_bottlenecks(event_log)
    rework_analysis = identify_rework_sources(event_log)
    metrics = calculate_overall_metrics(event_log, lead_times)
    
    print("\n🚧 Analyse des goulots d'étranglement:")
    bottleneck_df = bottleneck_analysis["bottleneck_analysis"]
    summary_df = bottleneck_df[["operation_name", "wait_cycle_ratio", "utilization_pct", "severity"]]
    print(summary_df.to_string(index=False))
    
    if bottleneck_analysis["critical_bottlenecks"]:
        print(f"\n⚠️ GOULOTS CRITIQUES: {', '.join(bottleneck_analysis['critical_bottlenecks'])}")
    if bottleneck_analysis["high_bottlenecks"]:
        print(f"⚡ GOULOTS IMPORTANTS: {', '.join(bottleneck_analysis['high_bottlenecks'])}")
    
    print("\n🔄 Analyse des sources de reprise:")
    rework_summary = rework_analysis[["operation_name", "actual_rework_rate_pct", "rework_time_hours"]]
    print(rework_summary.to_string(index=False))
    print()
    
    # =========================================================================
    # Step 5: Generate Visualizations and Report
    # =========================================================================
    print("=" * 70)
    print("ÉTAPE 5: Génération des visualisations et du rapport")
    print("=" * 70)
    
    print("\n📊 Création des visualisations...")
    create_all_visualizations(
        event_log, lead_times, wip_data,
        bottleneck_analysis, rework_analysis, flow_stats,
        output_dir=args.output_dir
    )
    
    print("\n📝 Génération du rapport d'analyse...")
    report_path = os.path.join(args.output_dir, "analysis_report.md")
    report = generate_full_report(
        event_log, lead_times, flow_stats,
        bottleneck_analysis, rework_analysis, metrics,
        output_path=report_path
    )
    print()
    
    # =========================================================================
    # Step 6: Present Success KPIs
    # =========================================================================
    print("=" * 70)
    print("ÉTAPE 6: KPI de succès")
    print("=" * 70)
    
    print("\n" + "=" * 60)
    print("           📊 KPI DE SUCCÈS / SUCCESS KPIs")
    print("=" * 60)
    
    # Import to get gains
    from src.report_generator import (
        generate_optimization_recommendations,
        estimate_potential_gains,
        get_top_3_actions
    )
    
    recommendations = generate_optimization_recommendations(
        bottleneck_analysis, rework_analysis, metrics, flow_stats
    )
    gains = estimate_potential_gains(recommendations, metrics, lead_times)
    top_actions = get_top_3_actions(recommendations)
    
    print(f"""
┌────────────────────────────────────────────────────────────────────┐
│                    INDICATEURS DE PERFORMANCE                      │
├────────────────────────────────────────────────────────────────────┤
│  Lead Time Actuel         : {metrics['avg_lead_time_hours']:>8.2f} heures                       │
│  Lead Time Estimé Après   : {gains['estimated_new_lead_time_hours']:>8.2f} heures                       │
├────────────────────────────────────────────────────────────────────┤
│  ✨ ΔWIP (Work In Progress): -{gains['estimated_wip_reduction_pct']:>5.1f}%                           │
│  ✨ ΔLead Time             : -{gains['delta_lead_time_pct']:>5.1f}% ({gains['delta_lead_time_hours']:.2f}h)                      │
├────────────────────────────────────────────────────────────────────┤
│                      TOP 3 ACTIONS                                 │
├────────────────────────────────────────────────────────────────────┤
""")
    
    for action in top_actions:
        action_text = action['action_fr'][:55]
        if len(action['action_fr']) > 55:
            action_text += "..."
        print(f"│  {action['rank']}. {action_text:<60} │")
    
    print(f"""├────────────────────────────────────────────────────────────────────┤
│  Efficacité Processus     : {metrics['process_efficiency_pct']:>5.1f}%                             │
│  Taux de Reprise          : {metrics['rework_rate_pct']:>5.1f}%                              │
└────────────────────────────────────────────────────────────────────┘
""")
    
    print(f"\n📁 Fichiers générés:")
    print(f"   - Event log: data/event_log.csv")
    print(f"   - Rapport: {report_path}")
    print(f"   - Visualisations: {args.output_dir}/")
    for f in os.listdir(args.output_dir):
        if f.endswith('.png'):
            print(f"      • {f}")
    
    print("\n" + "=" * 70)
    print("  Analyse terminée avec succès!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
