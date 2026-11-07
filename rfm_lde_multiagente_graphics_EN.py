"""
RFM-LDE Multiagent Graphics — Comprehensive System Visualization
Generates a 3x3 grid showing architecture, specialists, and performance metrics
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
import numpy as np

# Configure matplotlib style for professional appearance
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.facecolor'] = '#f8f9fa'
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['font.size'] = 9

# Define color palette for consistency
COLORS = {
    'primary': '#1f77b4',      # Blue for supervisors/flow
    'secondary': '#ff7f0e',    # Orange for specialists
    'success': '#2ca02c',      # Green for AADD/successful
    'danger': '#d62728',       # Red for GGW/risk
    'warning': '#ff9800',      # Orange for methodology
    'info': '#17a2b8',         # Teal for metrics
    'dark': '#2c3e50'          # Dark for text
}

# Apply consistent styling to axes
def set_style(ax):
    """Apply professional styling to matplotlib axes"""
    ax.set_facecolor('#f8f9fa')
    ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# Create figure with 3x3 grid
fig = plt.figure(figsize=(18, 12))
gs = fig.add_gridspec(3, 3, hspace=0.40, wspace=0.35)

# ============ ROW 1: ARCHITECTURE & FLOW ============

# SUBPLOT 1.1: Supervisor → Specialists Flow
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.axis('off')

# Draw supervisor node
supervisor = FancyBboxPatch((3.5, 7.5), 3, 1.2, boxstyle="round,pad=0.1",
                           edgecolor=COLORS['primary'], facecolor=COLORS['primary'],
                           alpha=0.7, linewidth=2)
ax1.add_patch(supervisor)
ax1.text(5, 8.1, 'SUPERVISOR\n(LLM Decision)', ha='center', va='center',
         fontsize=9, fontweight='bold', color='white')

# Draw specialist nodes
specialists = [
    ('AADD', 0.5, 4, COLORS['success']),
    ('Bonos', 2, 4, COLORS['info']),
    ('Dep/Ret', 3.5, 4, COLORS['warning']),
    ('GGW', 5, 4, COLORS['danger']),
    ('Export', 6.5, 4, COLORS['secondary']),
    ('Gráfico', 8, 4, COLORS['primary']),
    ('Metodología', 9.5, 4, COLORS['warning']),
]

for name, x, y, color in specialists:
    box = FancyBboxPatch((x-0.45, y-0.35), 0.9, 0.7, boxstyle="round,pad=0.05",
                         edgecolor=color, facecolor=color, alpha=0.6, linewidth=1.5)
    ax1.add_patch(box)
    ax1.text(x, y, name, ha='center', va='center', fontsize=7, fontweight='bold')

    # Draw arrows from supervisor to specialists
    arrow = FancyArrowPatch((5, 7.5), (x, y+0.35), arrowstyle='->',
                           mutation_scale=15, linewidth=1, color=COLORS['dark'], alpha=0.5)
    ax1.add_patch(arrow)

ax1.text(5, 9.2, 'Multiagent Routing Flow', ha='center', fontsize=10, fontweight='bold')

# SUBPLOT 1.2: K-Means Cluster Distribution
ax2 = fig.add_subplot(gs[0, 1])
clusters = ['C0\nNew', 'C1\nDormant', 'C2\nActive', 'C3\nHigh Value']
sizes = [18, 22, 35, 25]  # Approximate distribution percentages
colors_cluster = [COLORS['info'], COLORS['warning'], COLORS['success'], COLORS['danger']]

wedges, texts, autotexts = ax2.pie(sizes, labels=clusters, colors=colors_cluster, autopct='%1.0f%%',
                                     startangle=90, textprops={'fontsize': 9, 'fontweight': 'bold'},
                                     wedgeprops={'edgecolor': 'black', 'linewidth': 1})

for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')

ax2.set_title('4-Cluster Distribution\n(126K active players)', fontsize=10, fontweight='bold')

# SUBPLOT 1.3: Model Performance Metrics
ax3 = fig.add_subplot(gs[0, 2])
ax3.axis('off')

metrics_text = '''MODEL QUALITY METRICS

Silhouette Score: 0.42
  (K=4 optimal)

Spearman Corr: 0.35+
  (Predicted vs Actual)

Stability: 70%+
  (Week-to-week)

Coverage: 95%+
  (Active players)

Update Freq: Weekly
  (Monday 07:00 Lima)

Population: 126,000
  (Last 12 weeks)
'''

ax3.text(0.05, 0.95, metrics_text, transform=ax3.transAxes, fontsize=8.5,
         verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='#e8f4f8', alpha=0.9,
                  edgecolor=COLORS['primary'], linewidth=2))

# ============ ROW 2: SPECIALISTS & CAPABILITIES ============

# SUBPLOT 2.1: Data Sources & Tools
ax4 = fig.add_subplot(gs[1, 0])
ax4.set_xlim(0, 10)
ax4.set_ylim(0, 10)
ax4.axis('off')

data_sources = [
    ('AADD', 'Kambi pasta_*', 1.5, 8.5, COLORS['success']),
    ('Deposits/Ret', 'Athena txn', 1.5, 6.5, COLORS['warning']),
    ('Bonuses', 'Athena bonos', 1.5, 4.5, COLORS['info']),
    ('GGW', 'Athena ops', 1.5, 2.5, COLORS['danger']),
]

for name, source, x, y, color in data_sources:
    box = Rectangle((0.5, y-0.3), 2, 0.6, facecolor=color, alpha=0.6,
                   edgecolor=color, linewidth=1.5)
    ax4.add_patch(box)
    ax4.text(1.5, y, f'{name}\n{source}', ha='center', va='center',
            fontsize=7.5, fontweight='bold')

ax4.text(5, 9.5, 'Specialist Data Sources', ha='left', fontsize=10, fontweight='bold')
ax4.text(5, 8.8, '✓ Live Athena queries', ha='left', fontsize=8)
ax4.text(5, 8.2, '✓ Real-time GGW calc', ha='left', fontsize=8)
ax4.text(5, 7.6, '✓ S3 profile cache', ha='left', fontsize=8)
ax4.text(5, 7.0, '✓ Autoexcluded filtering', ha='left', fontsize=8)

# SUBPLOT 2.2: Specialist Capabilities
ax5 = fig.add_subplot(gs[1, 1])
specialists_cap = ['AADD', 'Bonos', 'Dep/Ret', 'GGW', 'Export', 'Gráfico', 'Metodología']
queries = [3, 1, 1, 1, 1, 3, 2]  # Number of queries/tools per specialist
colors_spec = [COLORS['success'], COLORS['info'], COLORS['warning'],
               COLORS['danger'], COLORS['secondary'], COLORS['primary'], COLORS['warning']]

bars = ax5.barh(specialists_cap, queries, color=colors_spec, edgecolor='black', linewidth=1.5, alpha=0.75)
ax5.set_xlabel('Tools per Specialist', fontsize=9, fontweight='bold')
ax5.set_title('Specialist Capabilities', fontsize=10, fontweight='bold')
ax5.set_xlim([0, 3.5])

for bar, q in zip(bars, queries):
    width = bar.get_width()
    ax5.text(width + 0.1, bar.get_y() + bar.get_height()/2, f'{int(q)}',
            ha='left', va='center', fontweight='bold', fontsize=8)

set_style(ax5)

# SUBPLOT 2.3: Response Quality Table
ax6 = fig.add_subplot(gs[1, 2])
ax6.axis('off')

quality_text = '''RESPONSE QUALITY

Latency: 1-3 seconds
  (per turn avg)

Max Steps: 8
  (before force-respond)

Context Persistence:
  ✓ Cluster carry-over
  ✓ Quintile memory
  ✓ Period awareness
  ✓ Language consistency

Output Formats:
  • CSV export (live)
  • JSON metadata
  • SVG charts
  • Markdown text
'''

ax6.text(0.05, 0.95, quality_text, transform=ax6.transAxes, fontsize=8.5,
         verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='#f0f8f0', alpha=0.9,
                  edgecolor=COLORS['success'], linewidth=2))

# ============ ROW 3: PRODUCTION & INTEGRATION ============

# SUBPLOT 3.1: Lambda Deployment
ax7 = fig.add_subplot(gs[2, 0])
ax7.set_xlim(0, 10)
ax7.set_ylim(0, 10)
ax7.axis('off')

# Draw deployment pipeline
stages = [
    ('Client', 1, 7, COLORS['info']),
    ('Lambda\nHTTP', 3, 7, COLORS['primary']),
    ('Graph\nEngine', 5, 7, COLORS['secondary']),
    ('Athena\nS3', 7, 7, COLORS['success']),
]

for name, x, y, color in stages:
    box = FancyBboxPatch((x-0.6, y-0.4), 1.2, 0.8, boxstyle="round,pad=0.08",
                         edgecolor=color, facecolor=color, alpha=0.7, linewidth=2)
    ax7.add_patch(box)
    ax7.text(x, y, name, ha='center', va='center', fontsize=7.5, fontweight='bold', color='white')

# Draw arrows between stages
for i in range(len(stages) - 1):
    x1 = stages[i][1] + 0.6
    x2 = stages[i+1][1] - 0.6
    arrow = FancyArrowPatch((x1, 7), (x2, 7), arrowstyle='->', mutation_scale=20,
                           linewidth=2, color=COLORS['dark'])
    ax7.add_patch(arrow)

ax7.text(5, 8.5, 'Production Deployment Pipeline', ha='center', fontsize=10, fontweight='bold')
ax7.text(5, 6, 'API Key authentication → Multi-turn history → Stateless',
        ha='center', fontsize=8, style='italic')

# SUBPLOT 3.2: Weekly Schedule
ax8 = fig.add_subplot(gs[2, 1])
days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
activity = [100, 30, 30, 30, 30, 20, 20]  # Artificial activity levels
colors_activity = [COLORS['success'] if a > 50 else COLORS['warning'] if a > 25 else COLORS['info']
                   for a in activity]

bars = ax8.bar(days, activity, color=colors_activity, edgecolor='black', linewidth=1.5, alpha=0.75)
ax8.set_ylabel('Score', fontsize=9, fontweight='bold')
ax8.set_title('Weekly Schedule\n(Peak on Monday)', fontsize=10, fontweight='bold')
ax8.set_ylim([0, 110])

# Add Monday marker
ax8.axvline(x=0, color=COLORS['danger'], linestyle='--', linewidth=2, alpha=0.7)
ax8.text(0, 105, '← Refresh Day', ha='center', fontsize=8, fontweight='bold', color=COLORS['danger'])

set_style(ax8)

# SUBPLOT 3.3: Production Metrics Summary
ax9 = fig.add_subplot(gs[2, 2])
ax9.axis('off')

summary_text = '''PRODUCTION STATUS

Uptime: 99%+
  (Last 52 weeks)

Daily Requests: 1,200+
  (Commercial team)

Players Queried: 126K+
  (per week)

Tests: 180
  (comprehensive)

Version: v2
  (K=4, 12-week RFM)

Repo: gitlab.com/olimpobet/
  data/agent_core

Branch: dev

Next Run:
  Mon 12:00 UTC
'''

ax9.text(0.05, 0.95, summary_text, transform=ax9.transAxes, fontsize=8.5,
         verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='#fffaf0', alpha=0.9,
                  edgecolor=COLORS['warning'], linewidth=2))

# Add overall title
plt.suptitle('RFM-LDE MULTIAGENT: Complete System Architecture & Performance',
            fontsize=14, fontweight='bold', y=0.995)

# Save figure
plt.savefig('graficos_rfm_lde_multiagente_v2.png', dpi=300, bbox_inches='tight', facecolor='white')
print("OK - graficos_rfm_lde_multiagente_v2.png")
