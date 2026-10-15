#!/usr/bin/env python3
"""
make_fig_architecture.py
Generates the system architecture diagram for Figure 4.1 in both vector PDF and high-res PNG formats.
Follows publication design guidelines:
- Minimum 9pt font size at print scale
- Equal box sizes and balanced spacing
- Orthogonal arrows that never cross boxes
- Labels placed beside arrows on white backgrounds
- Restrained 3-color palette with grayscale legibility
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_architecture_diagram():
    # Target text width in standard report is ~6.2 inches. We create a 12x7.2 canvas
    # which scales cleanly down with readable >= 9pt fonts.
    fig, ax = plt.subplots(figsize=(12, 7.2), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.2)
    ax.axis('off')

    # Canvas background
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')

    # Color Palette - Professional academic 3-color scheme (tested for grayscale contrast)
    c_ctl_head = '#1E3A8A'     # Navy
    c_ctl_bg   = '#F8FAFC'     # Crisp Light Slate
    c_ctl_border = '#2563EB'   # Royal Blue

    c_ai_head = '#065F46'      # Deep Forest
    c_ai_bg   = '#F0FDF4'      # Mint White
    c_ai_border = '#059669'    # Emerald Green

    c_dp_head = '#4A154B'      # Deep Plum
    c_dp_bg   = '#FAF5FA'      # Lilac White
    c_dp_border = '#7C3AED'    # Violet Purple

    def draw_card(x, y, w, h, header_h, title, subtitle, items, head_c, bg_c, border_c):
        # Body box
        body = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.15",
            facecolor=bg_c, edgecolor=border_c, linewidth=1.5, zorder=2
        )
        ax.add_patch(body)

        # Header box
        header = patches.FancyBboxPatch(
            (x, y + h - header_h), w, header_h,
            boxstyle="round,pad=0.02,rounding_size=0.15",
            facecolor=head_c, edgecolor=border_c, linewidth=1.5, zorder=3
        )
        ax.add_patch(header)

        # Seamless connection between header and body
        connector = patches.Rectangle(
            (x, y + h - header_h), w, 0.06,
            facecolor=head_c, edgecolor=head_c, zorder=4
        )
        ax.add_patch(connector)

        # Header text
        ax.text(x + w / 2, y + h - header_h * 0.40, title,
                ha='center', va='center', fontsize=12, fontweight='bold', color='white', zorder=5)
        ax.text(x + w / 2, y + h - header_h * 0.78, subtitle,
                ha='center', va='center', fontsize=9.2, fontstyle='italic', color='#E2E8F0', zorder=5)

        # Content bullet points
        start_y = y + h - header_h - 0.28
        spacing = (h - header_h - 0.40) / max(len(items), 1)
        for i, item in enumerate(items):
            cur_y = start_y - i * spacing
            ax.text(x + 0.35, cur_y, "•", fontsize=11, color=border_c, fontweight='bold', va='center', zorder=5)
            ax.text(x + 0.65, cur_y, item, fontsize=9.5, color='#1E293B', va='center', zorder=5)

    # 1. Top-Left Box: SDN Controller (Ryu, OpenFlow 1.3)
    ctl_x, ctl_y, ctl_w, ctl_h = 0.8, 3.8, 4.3, 3.0
    ctl_items = [
        "Southbound REST interface",
        "Make-before-break engine",
        "Dynamic risk-barrier router",
        "Two-phase commit flow manager"
    ]
    draw_card(ctl_x, ctl_y, ctl_w, ctl_h, 0.90,
              "SDN Controller", "Ryu (OpenFlow 1.3)",
              ctl_items, c_ctl_head, c_ctl_bg, c_ctl_border)

    # 2. Top-Right Box: AI Decision Module (PyTorch) - Exactly equal size
    ai_x, ai_y, ai_w, ai_h = 6.9, 3.8, 4.3, 3.0
    ai_items = [
        "Multi-scale gradient extractor",
        "Bidirectional LSTM predictor",
        "EMA divergence tracker",
        "Failure-probability head ($P_{\\mathrm{fail}}$)"
    ]
    draw_card(ai_x, ai_y, ai_w, ai_h, 0.90,
              "AI Decision Module", "PyTorch Deep Learning Engine",
              ai_items, c_ai_head, c_ai_bg, c_ai_border)

    # 3. Bottom Box: Data Plane (Mininet / Open vSwitch)
    dp_x, dp_y, dp_w, dp_h = 0.8, 0.5, 10.4, 2.2
    dp_items = [
        "OpenFlow 1.3 switches & hardware forwarding pipelines",
        "Traffic slicing with atomic ingress pointer swap",
        "High-resolution port counters and queue-depth telemetry",
        "Linux tc-netem fault injector (link cuts, flapping, soft degradation)"
    ]
    draw_card(dp_x, dp_y, dp_w, dp_h, 0.80,
              "Data Plane", "Mininet / Open vSwitch Substrate",
              dp_items, c_dp_head, c_dp_bg, c_dp_border)

    # Helper function for labels beside arrows
    def draw_side_label(x, y, text, fg_color, ha='center', va='center', font_size=8.8):
        ax.text(x, y, text, ha=ha, va=va, fontsize=font_size, fontweight='bold',
                color=fg_color, zorder=8,
                bbox=dict(boxstyle='round,pad=0.25,rounding_size=0.10',
                          facecolor='#ffffff', edgecolor=fg_color, linewidth=1.0, alpha=0.98))

    # ================= ORTHOGONAL ARROWS & LABELS BESIDE ARROWS =================
    gap_cx = (ctl_x + ctl_w + ai_x) / 2.0  # x = 6.0

    # Arrow 1: Controller -> AI Module (12-D feature vector)
    # Horizontal arrow at y = 5.5, label placed ABOVE the arrow
    ax.annotate('', xy=(ai_x, 5.5), xytext=(ctl_x + ctl_w, 5.5),
                arrowprops=dict(arrowstyle="->,head_width=0.28,head_length=0.42",
                                color=c_ctl_border, lw=2.0), zorder=6)
    draw_side_label(gap_cx, 5.88, "12-D feature vector", c_ctl_border, ha='center', va='center')

    # Arrow 2: AI Module -> Controller (P_fail > 0.85, lead time ~9.8 s)
    # Horizontal arrow at y = 4.4, label placed BELOW the arrow
    ax.annotate('', xy=(ctl_x + ctl_w, 4.4), xytext=(ai_x, 4.4),
                arrowprops=dict(arrowstyle="->,head_width=0.28,head_length=0.42",
                                color=c_ai_border, lw=2.0), zorder=6)
    draw_side_label(gap_cx, 3.98, "$P_{\\mathrm{fail}} > 0.85$\nlead time $\\approx 9.8$ s", c_ai_border, ha='center', va='center')

    # Arrow 3: Data Plane -> Controller (port and queue stats, 1 s epoch)
    # Vertical arrow at x = 1.8, label placed to the LEFT of arrow
    ax.annotate('', xy=(1.8, ctl_y), xytext=(1.8, dp_y + dp_h),
                arrowprops=dict(arrowstyle="->,head_width=0.28,head_length=0.42",
                                color=c_ctl_border, lw=2.0), zorder=6)
    draw_side_label(1.72, 3.25, "Port & queue stats\n(1 s epoch)", c_ctl_border, ha='right', va='center')

    # Arrow 4: Controller -> Data Plane (two-phase commit FlowMod)
    # Vertical arrow at x = 4.0, label placed to the RIGHT of arrow
    ax.annotate('', xy=(4.0, dp_y + dp_h), xytext=(4.0, ctl_y),
                arrowprops=dict(arrowstyle="->,head_width=0.28,head_length=0.42",
                                color='#DC2626', lw=2.0), zorder=6)
    draw_side_label(4.08, 3.25, "Two-phase commit\nFlowMod (MBB)", '#DC2626', ha='left', va='center')

    os.makedirs('figures', exist_ok=True)
    pdf_out = os.path.join('figures', 'fig0_architecture_loop.pdf')
    png_out = os.path.join('figures', 'fig0_architecture_loop.png')

    plt.tight_layout()
    plt.savefig(pdf_out, format='pdf', bbox_inches='tight', facecolor='white')
    plt.savefig(png_out, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Generated {pdf_out} and {png_out}")

if __name__ == '__main__':
    generate_architecture_diagram()
