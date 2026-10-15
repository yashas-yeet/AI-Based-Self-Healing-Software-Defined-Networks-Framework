"""
Ryu / OS-Ken Unified Compatibility Layer.
Transparently imports modern OpenStack OS-Ken (Ryu fork for Python 3.10+) or upstream Ryu.
"""

try:
    import os_ken
    import os_ken.base.app_manager as app_manager
    from os_ken.controller import ofp_event
    from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
    from os_ken.ofproto import ofproto_v1_3
    from os_ken.lib import hub
    from os_ken.lib.packet import packet, ethernet, ether_types
    from os_ken.topology import event as topo_event
    from os_ken.topology.api import get_switch, get_link
except (ImportError, AttributeError):
    import ryu
    from ryu.base import app_manager
    from ryu.controller import ofp_event
    from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
    from ryu.ofproto import ofproto_v1_3
    from ryu.lib import hub
    from ryu.lib.packet import packet, ethernet, ether_types
    from ryu.topology import event as topo_event
    from ryu.topology.api import get_switch, get_link
