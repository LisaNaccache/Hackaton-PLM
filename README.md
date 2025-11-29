# PLM AI Process Mining

> 🏭 **Manufacturing Workflow Analysis Tool** - A comprehensive process mining solution for optimizing production workflows using AI-powered analysis.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 Overview

This tool provides a complete process mining solution for manufacturing environments, enabling:

1. **Operations Chain Definition** - Define 4-8 workshop operations (digital twin simulation)
2. **Event Log Structuring** - Generate and structure XES-compatible event logs
3. **Flow Discovery** - Discover real process flows (volumes, average times) and visualize WIP
4. **Bottleneck Identification** - Identify bottlenecks (wait > cycle, persistent queues) and rework sources
5. **AI-Powered Analysis** - Generate optimization reports with recommendations and potential gains
6. **Success KPIs** - Track key performance indicators: ΔWIP, Δlead time, top 3 actions

## 🏗️ Manufacturing Operations Chain

The tool simulates a 6-operation manufacturing process:

| Operation | Description (FR) | Description (EN) | Avg. Duration | Workstations |
|-----------|-----------------|------------------|---------------|--------------|
| OP1 | Préparation Matière Première | Raw Material Preparation | 15 min | 2 |
| OP2 | Usinage CNC | CNC Machining | 45 min | 3 |
| OP3 | Traitement Thermique | Heat Treatment | 90 min | 1 |
| OP4 | Finition de Surface | Surface Finishing | 30 min | 2 |
| OP5 | Contrôle Qualité | Quality Control | 20 min | 2 |
| OP6 | Assemblage et Conditionnement | Assembly & Packaging | 25 min | 2 |

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/LisaNaccache/Hackaton-PLM.git
cd Hackaton-PLM

# Install dependencies
pip install -r requirements.txt

# Run the analysis
python main.py
```

### Command Line Options

```bash
python main.py [--cases N] [--output-dir DIR] [--seed SEED]

Options:
  --cases N       Number of cases to simulate (default: 500)
  --output-dir    Output directory for reports (default: reports)
  --seed          Random seed for reproducibility (default: 42)
```

## 📊 Output Files

After running the analysis, you'll find:

### Reports
- `reports/analysis_report.md` - Comprehensive analysis report in Markdown

### Visualizations
- `reports/wip_analysis.png` - Work In Progress by operation over time
- `reports/bottleneck_analysis.png` - Bottleneck identification charts
- `reports/rework_analysis.png` - Rework sources analysis
- `reports/flow_statistics.png` - Process flow statistics
- `reports/lead_time_distribution.png` - Lead time distribution

### Data
- `data/event_log.csv` - Structured event log (XES-compatible)

## 📈 Key Features

### Event Log Structure
```
case_id, activity, operation_id, timestamp_start, timestamp_end,
resource, is_rework, rework_count, wait_time_minutes, cycle_time_minutes
```

### Bottleneck Detection
The system identifies bottlenecks based on:
- Wait-to-Cycle Ratio > 1.0 (wait time exceeds processing time)
- Maximum wait time > 3x cycle time (persistent queues)
- Workstation utilization > 85% (capacity constraints)

### KPI Summary
The tool provides success KPIs including:
- **ΔWIP**: Estimated Work In Progress reduction
- **ΔLead Time**: Estimated lead time improvement
- **Top 3 Actions**: Priority improvement recommendations

## 📁 Project Structure

```
Hackaton-PLM/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── src/
│   ├── __init__.py
│   ├── operations.py      # Workshop operations definition
│   ├── event_log_generator.py  # Event log generation
│   ├── process_analyzer.py     # Flow discovery & bottleneck analysis
│   ├── visualizer.py          # WIP & metrics visualization
│   └── report_generator.py    # AI-powered report generation
├── data/
│   └── event_log.csv      # Generated event log
└── reports/
    ├── analysis_report.md # Analysis report
    └── *.png             # Visualization charts
```

## 🔧 Dependencies

- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- pm4py >= 2.7.0

## 📖 Sample Output

```
┌────────────────────────────────────────────────────────────────────┐
│                    INDICATEURS DE PERFORMANCE                      │
├────────────────────────────────────────────────────────────────────┤
│  Lead Time Actuel         :   203.71 heures                       │
│  Lead Time Estimé Après   :    72.11 heures                       │
├────────────────────────────────────────────────────────────────────┤
│  ✨ ΔWIP (Work In Progress): -64.6%                                │
│  ✨ ΔLead Time             : -64.6%                                │
├────────────────────────────────────────────────────────────────────┤
│  TOP 3 ACTIONS:                                                    │
│  1. Add workstation to Heat Treatment                              │
│  2. Implement error-proofing at CNC Machining                      │
│  3. Optimize scheduling at Surface Finishing                       │
└────────────────────────────────────────────────────────────────────┘
```

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
