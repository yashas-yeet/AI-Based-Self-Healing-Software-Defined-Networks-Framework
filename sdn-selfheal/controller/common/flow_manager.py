"""
OpenFlow 1.3 Flow and Group Table Management Helpers for Ryu.
Provides clean primitives for flow installation, modification, deletion, and fast-failover group setup.
"""

from controller.common.ryu_compat import ofproto_v1_3
from typing import List, Optional

def add_flow(
    datapath,
    priority: int,
    match,
    actions: List,
    buffer_id: Optional[int] = None,
    idle_timeout: int = 0,
    hard_timeout: int = 0,
    cookie: int = 0,
    table_id: int = 0
):
    """Installs an OpenFlow 1.3 flow entry with OFPFC_ADD."""
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser

    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
    if buffer_id is not None:
        mod = parser.OFPFlowMod(
            datapath=datapath,
            cookie=cookie,
            buffer_id=buffer_id,
            priority=priority,
            match=match,
            instructions=inst,
            idle_timeout=idle_timeout,
            hard_timeout=hard_timeout,
            table_id=table_id
        )
    else:
        mod = parser.OFPFlowMod(
            datapath=datapath,
            cookie=cookie,
            priority=priority,
            match=match,
            instructions=inst,
            idle_timeout=idle_timeout,
            hard_timeout=hard_timeout,
            table_id=table_id
        )
    datapath.send_msg(mod)

def delete_flow(
    datapath,
    match,
    cookie: int = 0,
    cookie_mask: int = 0,
    out_port: int = ofproto_v1_3.OFPP_ANY,
    out_group: int = ofproto_v1_3.OFPG_ANY,
    table_id: int = ofproto_v1_3.OFPTT_ALL
):
    """Deletes matching OpenFlow 1.3 flow entries using OFPFC_DELETE."""
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser

    mod = parser.OFPFlowMod(
        datapath=datapath,
        command=ofproto.OFPFC_DELETE,
        out_port=out_port,
        out_group=out_group,
        table_id=table_id,
        cookie=cookie,
        cookie_mask=cookie_mask,
        match=match
    )
    datapath.send_msg(mod)

def install_ff_group(
    datapath,
    group_id: int,
    primary_port: int,
    backup_port: int
):
    """
    Creates or modifies an OpenFlow 1.3 Fast Failover Group Table (OFPGT_FF).
    Bucket 0: Watch primary_port -> output to primary_port.
    Bucket 1: Watch backup_port -> output to backup_port.
    """
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser

    # Bucket 0: Primary path
    action_primary = [parser.OFPActionOutput(primary_port)]
    bucket_primary = parser.OFPBucket(
        watch_port=primary_port,
        watch_group=ofproto.OFPG_ANY,
        actions=action_primary
    )

    # Bucket 1: Backup path
    action_backup = [parser.OFPActionOutput(backup_port)]
    bucket_backup = parser.OFPBucket(
        watch_port=backup_port,
        watch_group=ofproto.OFPG_ANY,
        actions=action_backup
    )

    buckets = [bucket_primary, bucket_backup]
    mod = parser.OFPGroupMod(
        datapath=datapath,
        command=ofproto.OFPGC_ADD,
        type_=ofproto.OFPGT_FF,
        group_id=group_id,
        buckets=buckets
    )
    datapath.send_msg(mod)
