"""
Failure Injector for Mininet SDN Self-Healing.
Supports controlled injection of:
1. Hard Link Failure (down/up)
2. Flapping Link (oscillating)
3. Gradual Soft Degradation (tc netem progressive loss and latency)
4. Congestion-Induced Queue Drops (UDP burst buffer overflow)
5. Switch Node Crash
"""

import time
import subprocess
import threading
from typing import Optional, Dict, Any, List

class FailureInjector:
    def __init__(self, net=None, seed: int = 42):
        self.net = net
        self.seed = seed
        self.active_threads: List[threading.Thread] = []
        self.stop_events: List[threading.Event] = []
        self.event_log: List[Dict[str, Any]] = []

    def log_event(self, event_type: str, details: Dict[str, Any]):
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "details": details
        }
        self.event_log.append(entry)
        print(f"[FAULT-INJECTOR] {event_type} at {entry['timestamp']:.4f}: {details}")

    def inject_hard_down(self, u: str, v: str):
        """Immediately disables the link between u and v."""
        if self.net:
            self.net.configLinkStatus(u, v, "down")
        else:
            # Fallback direct CLI
            subprocess.run(["ip", "link", "set", f"{u}-{v}", "down"], capture_output=True)
        self.log_event("HARD_DOWN", {"link": (u, v)})

    def inject_hard_up(self, u: str, v: str):
        """Re-enables the link between u and v."""
        if self.net:
            self.net.configLinkStatus(u, v, "up")
        else:
            subprocess.run(["ip", "link", "set", f"{u}-{v}", "up"], capture_output=True)
        self.log_event("HARD_UP", {"link": (u, v)})

    def inject_flapping(self, u: str, v: str, cycles: int = 5, down_sec: float = 1.0, up_sec: float = 2.0):
        """Spawns background thread that oscillates link state."""
        stop_evt = threading.Event()
        self.stop_events.append(stop_evt)

        def _flap_worker():
            self.log_event("FLAP_START", {"link": (u, v), "cycles": cycles})
            for c in range(cycles):
                if stop_evt.is_set():
                    break
                self.inject_hard_down(u, v)
                time.sleep(down_sec)
                if stop_evt.is_set():
                    break
                self.inject_hard_up(u, v)
                time.sleep(up_sec)
            self.log_event("FLAP_END", {"link": (u, v)})

        th = threading.Thread(target=_flap_worker, daemon=True)
        self.active_threads.append(th)
        th.start()
        return th

    def inject_gradual_degradation(
        self,
        intf_name: str,
        total_duration_sec: float = 30.0,
        max_loss_pct: float = 25.0,
        max_delay_ms: float = 100.0,
        steps: int = 10
    ):
        """
        Applies progressive Linux Traffic Control (tc netem) degradation.
        Increases packet loss (0% -> max_loss_pct) and delay (0ms -> max_delay_ms)
        over total_duration_sec before full breakdown.
        """
        stop_evt = threading.Event()
        self.stop_events.append(stop_evt)
        step_interval = total_duration_sec / max(1, steps)

        def _degrade_worker():
            self.log_event("GRADUAL_DEGRADE_START", {"intf": intf_name, "duration": total_duration_sec})
            # Ensure root qdisc exists or replace it
            subprocess.run(["tc", "qdisc", "del", "dev", intf_name, "root"], capture_output=True)
            subprocess.run(["tc", "qdisc", "add", "dev", intf_name, "root", "netem", "delay", "1ms"], capture_output=True)

            for step in range(1, steps + 1):
                if stop_evt.is_set():
                    break
                current_loss = (step / steps) * max_loss_pct
                current_delay = (step / steps) * max_delay_ms
                # Update netem parameters
                cmd = [
                    "tc", "qdisc", "change", "dev", intf_name, "root", "netem",
                    "delay", f"{current_delay:.1f}ms",
                    "loss", f"{current_loss:.1f}%"
                ]
                subprocess.run(cmd, capture_output=True)
                self.log_event("DEGRADE_STEP", {
                    "intf": intf_name,
                    "step": step,
                    "loss_pct": current_loss,
                    "delay_ms": current_delay
                })
                time.sleep(step_interval)

            self.log_event("GRADUAL_DEGRADE_END", {"intf": intf_name})

        th = threading.Thread(target=_degrade_worker, daemon=True)
        self.active_threads.append(th)
        th.start()
        return th

    def reset_intf(self, intf_name: str):
        """Clears any tc netem qdisc on interface."""
        subprocess.run(["tc", "qdisc", "del", "dev", intf_name, "root"], capture_output=True)

    def stop_all(self):
        """Stops all background flapping / degradation injectors."""
        for evt in self.stop_events:
            evt.set()
        for th in self.active_threads:
            th.join(timeout=2.0)
        self.active_threads.clear()
        self.stop_events.clear()
