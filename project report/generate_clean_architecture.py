import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_system_architecture():
    # Academic publication dimensions with ample breathing room
    fig, ax = plt.subplots(figsize=(13.2, 7.4), dpi=300)
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 7.4)
    ax.axis('off')

    # Pure white background
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')

    # Color Palette - Professional Academic Theme
    c_ctl_head = '#1E3A8A'     # Deep Navy
    c_ctl_bg   = '#F8FAFC'     # Crisp Slate White
    c_ctl_border = '#2563EB'   # Royal Blue

    c_ai_head = '#065F46'      # Deep Forest
    c_ai_bg   = '#F0FDF4'      # Mint White
    c_ai_border = '#059669'    # Emerald Green

    c_dp_head = '#4A154B'      # Deep Plum
    c_dp_bg   = '#FAF5FA'      # Lilac White
    c_dp_border = '#7C3AED'    # Violet Purple

    # Helper function to draw cards with headers
    def draw_component_card(x, y, w, h, header_h, title, subtitle, items, head_c, bg_c, border_c):
        # Body box
        body = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.03,rounding_size=0.16",
            facecolor=bg_c, edgecolor=border_c, linewidth=1.5, zorder=2
        )
        ax.add_patch(body)

        # Header box
        header = patches.FancyBboxPatch(
            (x, y + h - header_h), w, header_h,
            boxstyle="round,pad=0.03,rounding_size=0.16",
            facecolor=head_c, edgecolor=border_c, linewidth=1.5, zorder=3
        )
        ax.add_patch(header)

        # Seam connector
        connector = patches.Rectangle(
            (x, y + h - header_h), w, 0.08,
            facecolor=head_c, edgecolor=head_c, zorder=4
        )
        ax.add_patch(connector)

        # Header text
        ax.text(x + w / 2, y + h - header_h * 0.40, title,
                ha='center', va='center', fontsize=11.5, fontweight='bold', color='white', zorder=5)
        ax.text(x + w / 2, y + h - header_h * 0.78, subtitle,
                ha='center', va='center', fontsize=8.8, fontstyle='italic', color='#E2E8F0', zorder=5)

        # Bullet items
        start_y = y + h - header_h - 0.28
        spacing = (h - header_h - 0.42) / max(len(items), 1)
        for i, item in enumerate(items):
            cur_y = start_y - i * spacing
            ax.text(x + 0.32, cur_y, "•", fontsize=10.5, color=border_c, fontweight='bold', va='center', zorder=5)
            ax.text(x + 0.60, cur_y, item, fontsize=8.4, color='#1E293B', va='center', zorder=5)

    # 1. Top-Left: SDN Controller Core
    ctl_x, ctl_y, ctl_w, ctl_h = 0.7, 3.9, 4.8, 3.2
    ctl_items = [
        "OpenFlow 1.3 Core Engine (Ryu Framework)",
        "RESTful Northbound & Telemetry Dispatcher",
        "Dynamic Risk-Barrier Routing Optimization",
        "Make-Before-Break (MBB) Flow Manager",
        "Two-Phase Commit Downstream Flow Pre-Installation"
    ]
    draw_component_card(ctl_x, ctl_y, ctl_w, ctl_h, 0.95,
                        "SDN Controller Core", "Ryu OpenFlow 1.3 Controller Engine",
                        ctl_items, c_ctl_head, c_ctl_bg, c_ctl_border)

    # 2. Top-Right: AI Decision Engine
    ai_x, ai_y, ai_w, ai_h = 7.7, 3.9, 4.8, 3.2
    ai_items = [
        "12-D Telemetry Feature Normalization Engine",
        "Multi-Scale Temporal Gradients (∇l, ∇²l, ∇τ, δ_EMA)",
        "Bidirectional LSTM Sequence Predictor (PyTorch)",
        "Proactive Failure Risk Head: P_fail(t) ∈ [0, 1]",
        "EMA Divergence Tracking & Flap Dampening Filter"
    ]
    draw_component_card(ai_x, ai_y, ai_w, ai_h, 0.95,
                        "AI Predictive Decision Engine", "Temporal Multi-Scale Deep Learning",
                        ai_items, c_ai_head, c_ai_bg, c_ai_border)

    # 3. Bottom: Data Plane Forwarding Fabric
    dp_x, dp_y, dp_w, dp_h = 0.7, 0.4, 11.8, 2.4
    dp_items = [
        "OpenFlow 1.3 Datapaths (Open vSwitch v3.3.0 & Mininet Emulated Substrate)",
        "Evaluated Topologies: 6-Switch Mesh, Fat-Tree (k=4), B4 WAN Enterprise Backbone",
        "Traffic Generation: iperf3 High-Throughput TCP/UDP Streams (10 / 50 / 90 Mbps)",
        "Controlled Fault Injection: Linux tc-netem (Hard Cuts, Flapping, Soft Packet Loss, Queue Latency)"
    ]
    draw_component_card(dp_x, dp_y, dp_w, dp_h, 0.85,
                        "Data Plane Forwarding Fabric", "Open vSwitch / Mininet Emulated Substrate",
                        dp_items, c_dp_head, c_dp_bg, c_dp_border)

    # Helper function for badges
    def draw_badge(x, y, text, fg_color, bg_color='#ffffff', border_color=None, font_size=8.0):
        if border_color is None:
            border_color = fg_color
        ax.text(x, y, text, ha='center', va='center', fontsize=font_size, fontweight='bold',
                color=fg_color, zorder=8,
                bbox=dict(boxstyle='round,pad=0.32,rounding_size=0.14',
                          facecolor=bg_color, edgecolor=border_color, linewidth=1.1, alpha=0.98))

    # ================= ARROWS & TELEMETRY LOOPS =================
    # Gap between Controller and AI: from x=5.5 to x=7.7 (center x=6.6)
    gap_cx = (ctl_x + ctl_w + ai_x) / 2.0  # 6.6

    # Arrow 1: Controller -> AI Module (12-D Feature Vector)
    ax.annotate('', xy=(ai_x, 5.75), xytext=(ctl_x + ctl_w, 5.75),
                arrowprops=dict(arrowstyle="->,head_width=0.32,head_length=0.45",
                                color=c_ctl_border, lw=2.2), zorder=6)
    draw_badge(gap_cx, 6.10, "12-D Telemetry Features", c_ctl_border, bg_color='#ffffff')

    # Arrow 2: AI Module -> Controller (Failure Risk & Lead Time)
    ax.annotate('', xy=(ctl_x + ctl_w, 4.55), xytext=(ai_x, 4.55),
                arrowprops=dict(arrowstyle="->,head_width=0.32,head_length=0.45",
                                color=c_ai_border, lw=2.2), zorder=6)
    draw_badge(gap_cx, 4.20, "Risk P_fail > 0.85 (Lead ~9.8s)", c_ai_border, bg_color='#ffffff')

    # Arrow 3: Data Plane -> Controller (PortStats Telemetry Uplink)
    ax.annotate('', xy=(1.9, ctl_y), xytext=(1.9, dp_y + dp_h),
                arrowprops=dict(arrowstyle="->,head_width=0.32,head_length=0.45",
                                color=c_ctl_border, lw=2.2), zorder=6)
    draw_badge(1.9, 3.35, "Port & Queue Stats (1.0 s)", c_ctl_border, bg_color='#ffffff')

    # Arrow 4: Controller -> Data Plane (MBB FlowMod Downlink)
    ax.annotate('', xy=(4.3, dp_y + dp_h), xytext=(4.3, ctl_y),
                arrowprops=dict(arrowstyle="->,head_width=0.32,head_length=0.45",
                                color='#DC2626', lw=2.2), zorder=6)
    draw_badge(4.3, 3.35, "Two-Phase FlowMod (MBB)", '#DC2626', bg_color='#ffffff')

    plt.tight_layout()
    plt.savefig('figures/fig0_architecture_loop.png', dpi=300, bbox_inches='tight', facecolor='white')
    print("Successfully generated high-res system architecture diagram at figures/fig0_architecture_loop.png")

if __name__ == '__main__':
    create_system_architecture()
