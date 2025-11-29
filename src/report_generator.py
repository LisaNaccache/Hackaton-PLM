"""
AI-Powered Analysis Report Generator
=====================================
Generates comprehensive analysis reports with optimization recommendations.
"""

from datetime import datetime
from typing import Dict, Any, List, Tuple
import pandas as pd

from .operations import OPERATIONS, get_operation_by_id, get_theoretical_lead_time


def generate_optimization_recommendations(
    bottleneck_analysis: Dict[str, Any],
    rework_df: pd.DataFrame,
    metrics: Dict[str, Any],
    flow_stats: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate AI-powered optimization recommendations based on analysis.
    
    Uses rule-based inference to identify improvement opportunities and
    estimate potential gains.
    """
    recommendations = []
    
    bottleneck_df = bottleneck_analysis["bottleneck_analysis"]
    
    # 1. Analyze bottlenecks and recommend capacity increases
    critical_bottlenecks = bottleneck_df[bottleneck_df["severity"] == "Critical"]
    high_bottlenecks = bottleneck_df[bottleneck_df["severity"] == "High"]
    
    for _, row in critical_bottlenecks.iterrows():
        op = get_operation_by_id(row["operation_id"])
        
        # Calculate potential gain from adding workstation
        current_util = row["utilization_pct"]
        new_util = current_util * op.workstation_count / (op.workstation_count + 1)
        wait_reduction = row["avg_wait_time"] * (1 - new_util/current_util)
        
        recommendations.append({
            "priority": 1,
            "category": "Capacity",
            "operation": row["operation_name"],
            "operation_fr": row["operation_name_fr"],
            "issue": f"Critical bottleneck with {current_util:.0f}% utilization",
            "issue_fr": f"Goulot d'étranglement critique avec {current_util:.0f}% d'utilisation",
            "recommendation": f"Add 1 additional workstation to {row['operation_name']}",
            "recommendation_fr": f"Ajouter 1 poste de travail supplémentaire à {row['operation_name_fr']}",
            "estimated_wait_reduction_min": round(wait_reduction, 1),
            "estimated_lead_time_reduction_pct": round(wait_reduction / metrics["avg_lead_time_hours"] / 60 * 100, 1),
            "confidence": "High"
        })
    
    for _, row in high_bottlenecks.iterrows():
        recommendations.append({
            "priority": 2,
            "category": "Process",
            "operation": row["operation_name"],
            "operation_fr": row["operation_name_fr"],
            "issue": f"High wait-to-cycle ratio ({row['wait_cycle_ratio']:.2f})",
            "issue_fr": f"Ratio attente/cycle élevé ({row['wait_cycle_ratio']:.2f})",
            "recommendation": f"Optimize scheduling and reduce setup time at {row['operation_name']}",
            "recommendation_fr": f"Optimiser l'ordonnancement et réduire le temps de réglage à {row['operation_name_fr']}",
            "estimated_wait_reduction_min": round(row["avg_wait_time"] * 0.3, 1),
            "estimated_lead_time_reduction_pct": round(row["avg_wait_time"] * 0.3 / metrics["avg_lead_time_hours"] / 60 * 100, 1),
            "confidence": "Medium"
        })
    
    # 2. Analyze rework and recommend quality improvements
    high_rework_ops = rework_df[rework_df["actual_rework_rate_pct"] > 3.0]
    
    for _, row in high_rework_ops.iterrows():
        if row["rework_time_hours"] > 0:
            recommendations.append({
                "priority": 2,
                "category": "Quality",
                "operation": row["operation_name"],
                "operation_fr": get_operation_by_id(row["operation_id"]).name_fr,
                "issue": f"High rework rate ({row['actual_rework_rate_pct']:.1f}%) causing {row['rework_time_hours']:.1f}h of waste",
                "issue_fr": f"Taux de reprise élevé ({row['actual_rework_rate_pct']:.1f}%) causant {row['rework_time_hours']:.1f}h de gaspillage",
                "recommendation": f"Implement error-proofing (poka-yoke) at {row['operation_name']}",
                "recommendation_fr": f"Mettre en œuvre le détrompeur (poka-yoke) à {get_operation_by_id(row['operation_id']).name_fr}",
                "estimated_wait_reduction_min": round(row["rework_time_hours"] * 60 * 0.5 / metrics["total_cases"], 1),
                "estimated_lead_time_reduction_pct": round(row["rework_time_hours"] * 0.5 / metrics["total_cases"] / metrics["avg_lead_time_hours"] * 100, 1),
                "confidence": "Medium"
            })
    
    # 3. Flow conformance recommendations
    standard_pct = flow_stats["standard_flow_percentage"]
    if standard_pct < 90:
        recommendations.append({
            "priority": 3,
            "category": "Flow",
            "operation": "All",
            "operation_fr": "Toutes",
            "issue": f"Low process conformance ({standard_pct:.1f}% follow standard path)",
            "issue_fr": f"Faible conformité du processus ({standard_pct:.1f}% suivent le chemin standard)",
            "recommendation": "Implement standardized work instructions and training",
            "recommendation_fr": "Mettre en œuvre des instructions de travail standardisées et une formation",
            "estimated_wait_reduction_min": round(metrics["avg_wait_per_case_minutes"] * 0.1, 1),
            "estimated_lead_time_reduction_pct": 2.0,
            "confidence": "Low"
        })
    
    # 4. General efficiency recommendations
    if metrics["process_efficiency_pct"] < 60:
        recommendations.append({
            "priority": 3,
            "category": "Efficiency",
            "operation": "All",
            "operation_fr": "Toutes",
            "issue": f"Low process efficiency ({metrics['process_efficiency_pct']:.1f}%)",
            "issue_fr": f"Faible efficacité du processus ({metrics['process_efficiency_pct']:.1f}%)",
            "recommendation": "Implement lean manufacturing principles (5S, SMED)",
            "recommendation_fr": "Mettre en œuvre les principes de lean manufacturing (5S, SMED)",
            "estimated_wait_reduction_min": round(metrics["avg_wait_per_case_minutes"] * 0.2, 1),
            "estimated_lead_time_reduction_pct": 5.0,
            "confidence": "Medium"
        })
    
    # Sort by priority
    recommendations.sort(key=lambda x: x["priority"])
    
    return recommendations


def estimate_potential_gains(
    recommendations: List[Dict[str, Any]],
    metrics: Dict[str, Any],
    lead_times: pd.DataFrame
) -> Dict[str, Any]:
    """
    Estimate potential gains from implementing recommendations.
    """
    total_lead_time_reduction_pct = sum(r["estimated_lead_time_reduction_pct"] for r in recommendations)
    
    # Calculate new metrics
    current_lead_time = metrics["avg_lead_time_hours"]
    estimated_new_lead_time = current_lead_time * (1 - total_lead_time_reduction_pct / 100)
    
    # Estimate WIP reduction (Little's Law: WIP = throughput * lead time)
    wip_reduction_pct = total_lead_time_reduction_pct
    
    # Theoretical minimum
    theoretical_time, theoretical_str = get_theoretical_lead_time()
    theoretical_hours = theoretical_time / 60
    
    return {
        "current_avg_lead_time_hours": round(current_lead_time, 2),
        "estimated_new_lead_time_hours": round(estimated_new_lead_time, 2),
        "delta_lead_time_hours": round(current_lead_time - estimated_new_lead_time, 2),
        "delta_lead_time_pct": round(total_lead_time_reduction_pct, 1),
        "estimated_wip_reduction_pct": round(wip_reduction_pct, 1),
        "theoretical_minimum_hours": round(theoretical_hours, 2),
        "gap_to_theoretical_current": round((current_lead_time - theoretical_hours) / theoretical_hours * 100, 1),
        "gap_to_theoretical_after": round((estimated_new_lead_time - theoretical_hours) / theoretical_hours * 100, 1)
    }


def get_top_3_actions(recommendations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Extract top 3 priority actions.
    """
    top_3 = recommendations[:3]
    
    actions = []
    for i, rec in enumerate(top_3, 1):
        actions.append({
            "rank": i,
            "action": rec["recommendation"],
            "action_fr": rec["recommendation_fr"],
            "category": rec["category"],
            "target_operation": rec["operation"],
            "expected_impact": f"{rec['estimated_lead_time_reduction_pct']:.1f}% lead time reduction"
        })
    
    return actions


def generate_kpi_summary(
    metrics: Dict[str, Any],
    gains: Dict[str, Any],
    top_actions: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Generate KPI summary for success measurement.
    """
    return {
        "current_state": {
            "avg_lead_time_hours": metrics["avg_lead_time_hours"],
            "total_cases_analyzed": metrics["total_cases"],
            "rework_rate_pct": metrics["rework_rate_pct"],
            "process_efficiency_pct": metrics["process_efficiency_pct"],
            "total_wait_time_hours": metrics["total_wait_time_hours"]
        },
        "projected_improvements": {
            "delta_wip_pct": f"-{gains['estimated_wip_reduction_pct']}%",
            "delta_lead_time_pct": f"-{gains['delta_lead_time_pct']}%",
            "delta_lead_time_hours": f"-{gains['delta_lead_time_hours']}h"
        },
        "top_3_actions": top_actions,
        "success_criteria": {
            "wip_target_reduction": "15-25%",
            "lead_time_target_reduction": "20-30%",
            "efficiency_target": ">70%"
        }
    }


def generate_full_report(
    event_log: pd.DataFrame,
    lead_times: pd.DataFrame,
    flow_stats: Dict[str, Any],
    bottleneck_analysis: Dict[str, Any],
    rework_df: pd.DataFrame,
    metrics: Dict[str, Any],
    output_path: str = None
) -> str:
    """
    Generate full analysis report in Markdown format.
    """
    # Generate recommendations
    recommendations = generate_optimization_recommendations(
        bottleneck_analysis, rework_df, metrics, flow_stats
    )
    
    # Estimate gains
    gains = estimate_potential_gains(recommendations, metrics, lead_times)
    
    # Get top actions
    top_actions = get_top_3_actions(recommendations)
    
    # Get KPI summary
    kpi_summary = generate_kpi_summary(metrics, gains, top_actions)
    
    # Build report
    report = []
    report.append("# PLM AI Process Mining - Rapport d'Analyse")
    report.append(f"**Date de génération:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Executive Summary
    report.append("## 1. Résumé Exécutif / Executive Summary\n")
    report.append(f"Cette analyse porte sur **{metrics['total_cases']}** cas comprenant **{metrics['total_events']}** événements.")
    report.append(f"Le temps de cycle moyen actuel est de **{metrics['avg_lead_time_hours']:.2f} heures**.\n")
    
    report.append("### Indicateurs Clés de Performance (KPI)\n")
    report.append("| Métrique | Valeur Actuelle | Cible Après Optimisation |")
    report.append("|----------|-----------------|--------------------------|")
    report.append(f"| Lead Time Moyen | {metrics['avg_lead_time_hours']:.2f}h | {gains['estimated_new_lead_time_hours']:.2f}h ({gains['delta_lead_time_pct']:.1f}% ↓) |")
    report.append(f"| Réduction WIP Estimée | - | {gains['estimated_wip_reduction_pct']:.1f}% ↓ |")
    report.append(f"| Efficacité Processus | {metrics['process_efficiency_pct']:.1f}% | >70% |")
    report.append(f"| Taux de Reprise | {metrics['rework_rate_pct']:.1f}% | <2% |")
    report.append("")
    
    # Operations Chain
    report.append("## 2. Chaîne d'Opérations / Operations Chain\n")
    report.append("La chaîne d'opérations analysée comprend les étapes suivantes :\n")
    for op in OPERATIONS:
        report.append(f"- **{op.id}**: {op.name_fr} ({op.name}) - Durée moyenne: {op.avg_duration_minutes}min, Postes: {op.workstation_count}")
    report.append("")
    
    # Flow Discovery
    report.append("## 3. Découverte du Flux Réel / Real Flow Discovery\n")
    report.append("### 3.1 Volumes par Opération\n")
    volume_df = flow_stats["volume_per_operation"]
    report.append("| Opération | Événements Total | Cas Uniques | Événements Reprise |")
    report.append("|-----------|-----------------|-------------|-------------------|")
    for _, row in volume_df.iterrows():
        report.append(f"| {row['operation_id']} | {row['total_events']} | {row['unique_cases']} | {row['rework_events']} |")
    report.append("")
    
    report.append("### 3.2 Temps Moyens par Opération\n")
    time_df = flow_stats["time_statistics"]
    report.append("| Opération | Cycle Moyen (min) | Attente Moyenne (min) | Max Attente (min) |")
    report.append("|-----------|------------------|----------------------|-------------------|")
    for _, row in time_df.iterrows():
        report.append(f"| {row['operation_id']} | {row['avg_cycle_time']:.1f} | {row['avg_wait_time']:.1f} | {row['max_wait_time']:.1f} |")
    report.append("")
    
    report.append(f"### 3.3 Conformité du Processus\n")
    report.append(f"- **{flow_stats['standard_flow_percentage']:.1f}%** des cas suivent le flux standard")
    report.append(f"- **{100 - flow_stats['standard_flow_percentage']:.1f}%** incluent des déviations (reprises, etc.)\n")
    
    # Bottleneck Analysis
    report.append("## 4. Analyse des Goulots d'Étranglement / Bottleneck Analysis\n")
    bottleneck_df = bottleneck_analysis["bottleneck_analysis"]
    
    report.append("### 4.1 Identification des Goulots\n")
    report.append("| Opération | Ratio Attente/Cycle | Utilisation | Sévérité | Causes |")
    report.append("|-----------|---------------------|-------------|----------|--------|")
    for _, row in bottleneck_df.iterrows():
        report.append(f"| {row['operation_name']} | {row['wait_cycle_ratio']:.2f} | {row['utilization_pct']:.0f}% | {row['severity']} | {row['reasons']} |")
    report.append("")
    
    if bottleneck_analysis["critical_bottlenecks"]:
        report.append(f"**⚠️ Goulots Critiques:** {', '.join(bottleneck_analysis['critical_bottlenecks'])}\n")
    if bottleneck_analysis["high_bottlenecks"]:
        report.append(f"**⚡ Goulots Importants:** {', '.join(bottleneck_analysis['high_bottlenecks'])}\n")
    
    # Rework Analysis
    report.append("## 5. Analyse des Sources de Reprise / Rework Sources Analysis\n")
    report.append("| Opération | Taux Défaut Attendu | Taux Reprise Réel | Temps Perdu (h) |")
    report.append("|-----------|---------------------|-------------------|-----------------|")
    for _, row in rework_df.iterrows():
        report.append(f"| {row['operation_name']} | {row['expected_defect_rate_pct']:.1f}% | {row['actual_rework_rate_pct']:.1f}% | {row['rework_time_hours']:.1f}h |")
    report.append("")
    
    # Recommendations
    report.append("## 6. Recommandations d'Optimisation / Optimization Recommendations\n")
    for i, rec in enumerate(recommendations, 1):
        report.append(f"### Recommandation {i}: {rec['category']}")
        report.append(f"- **Opération concernée:** {rec['operation_fr']} ({rec['operation']})")
        report.append(f"- **Problème identifié:** {rec['issue_fr']}")
        report.append(f"- **Action recommandée:** {rec['recommendation_fr']}")
        report.append(f"- **Réduction estimée du lead time:** {rec['estimated_lead_time_reduction_pct']:.1f}%")
        report.append(f"- **Confiance:** {rec['confidence']}")
        report.append("")
    
    # Potential Gains
    report.append("## 7. Estimation des Gains Potentiels / Potential Gains Estimation\n")
    report.append(f"| Indicateur | Valeur |")
    report.append("|------------|--------|")
    report.append(f"| Lead Time Actuel | {gains['current_avg_lead_time_hours']:.2f}h |")
    report.append(f"| Lead Time Estimé Après | {gains['estimated_new_lead_time_hours']:.2f}h |")
    report.append(f"| **ΔWIP** | **-{gains['estimated_wip_reduction_pct']:.1f}%** |")
    report.append(f"| **ΔLead Time** | **-{gains['delta_lead_time_pct']:.1f}%** ({gains['delta_lead_time_hours']:.2f}h) |")
    report.append(f"| Écart au Théorique (avant) | +{gains['gap_to_theoretical_current']:.1f}% |")
    report.append(f"| Écart au Théorique (après) | +{gains['gap_to_theoretical_after']:.1f}% |")
    report.append("")
    
    # Top 3 Actions
    report.append("## 8. Top 3 Actions Prioritaires / Top 3 Priority Actions\n")
    for action in top_actions:
        report.append(f"### 🎯 Action #{action['rank']}: {action['category']}")
        report.append(f"**{action['action_fr']}**")
        report.append(f"- Opération cible: {action['target_operation']}")
        report.append(f"- Impact attendu: {action['expected_impact']}")
        report.append("")
    
    # KPI Summary
    report.append("## 9. Résumé des KPI de Succès / Success KPI Summary\n")
    report.append("```")
    report.append(f"┌──────────────────────────────────────────────────────────────┐")
    report.append(f"│                    KPI DE SUCCÈS                             │")
    report.append(f"├──────────────────────────────────────────────────────────────┤")
    report.append(f"│  ΔWIP (Work In Progress)     : -{gains['estimated_wip_reduction_pct']:.1f}% (Cible: -15 à -25%)  │")
    report.append(f"│  ΔLead Time                  : -{gains['delta_lead_time_pct']:.1f}% (Cible: -20 à -30%)  │")
    report.append(f"├──────────────────────────────────────────────────────────────┤")
    report.append(f"│  TOP 3 ACTIONS:                                              │")
    for i, action in enumerate(top_actions, 1):
        action_text = action['action_fr'][:50] + "..." if len(action['action_fr']) > 50 else action['action_fr']
        report.append(f"│  {i}. {action_text:<54} │")
    report.append(f"└──────────────────────────────────────────────────────────────┘")
    report.append("```\n")
    
    # Conclusion
    report.append("## 10. Conclusion\n")
    report.append(f"L'analyse du processus de fabrication révèle un potentiel d'amélioration significatif. ")
    report.append(f"En mettant en œuvre les {len(recommendations)} recommandations identifiées, ")
    report.append(f"une réduction du lead time de **{gains['delta_lead_time_pct']:.1f}%** et une réduction ")
    report.append(f"du WIP de **{gains['estimated_wip_reduction_pct']:.1f}%** sont estimées réalisables.\n")
    
    report.append("Les actions prioritaires se concentrent sur :")
    report.append("1. La résolution des goulots d'étranglement critiques")
    report.append("2. La réduction des reprises par l'amélioration de la qualité")
    report.append("3. L'optimisation des temps de réglage et de l'ordonnancement\n")
    
    report.append("---")
    report.append("*Rapport généré par PLM AI Process Mining v1.0*")
    
    # Join report lines
    report_text = "\n".join(report)
    
    # Save if output path provided
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"Report saved to {output_path}")
    
    return report_text
