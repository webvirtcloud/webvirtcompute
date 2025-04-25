import os
import time
from subprocess import DEVNULL, STDOUT, call

from firewall.client import FirewallClient

from settings import (
    FIREWALL_CHAIN_PREFIX,
    FIREWALL_IN_NAME,
    FIREWALL_INSERT_LINE,
    FIREWALL_OUT_NAME,
    FIREWALLD_STATE_FILE,
    FIREWALLD_STATE_TIMEOUT,
)

from .exceptions import FirewallRuleError


class FirewallMgr(object):
    def __init__(self, rules_id, ipv4_public_addr=None, ipv4_private_addr=None):
        self.fw = FirewallClient()
        self.config = self.fw.config()
        self.fw_direct = self.config.direct()
        self.prio = 0
        self.ipv = "ipv4"
        self.table = "filter"
        self.chain = "FORWARD"
        self.rules_id = rules_id
        self.ipv4_public_addr = ipv4_public_addr
        self.ipv4_private_addr = ipv4_private_addr
        self.firewall_in_chain = f"{FIREWALL_IN_NAME}{str(rules_id)}"
        self.firewall_out_chain = f"{FIREWALL_OUT_NAME}{str(rules_id)}"

    def attach(self, rules_inbound, rules_outbound):
        if self.is_locked():
            return (
                f"Firewall closed connection by timeout {FIREWALLD_STATE_TIMEOUT}sec."
            )
        self.set_state()
        self.create_firewall()
        self.create_rule("inbound", rules_inbound)
        self.create_rule("outbound", rules_outbound)
        self.save()
        return None

    def detach(self):
        if self.is_locked():
            return (
                f"Firewall closed connection by timeout {FIREWALLD_STATE_TIMEOUT}sec."
            )
        self.set_state()
        self.delete_firewall()
        self.save()
        return None

    def attach_rule(self, rules_inbound, rules_outbound):
        if self.is_locked():
            return (
                f"Firewall closed connection by timeout {FIREWALLD_STATE_TIMEOUT}sec."
            )
        self.set_state()
        if rules_inbound:
            self.create_rule("inbound", rules_inbound)
        if rules_outbound:
            self.create_rule("outbound", rules_outbound)
        self.save()
        return None

    def detach_rule(self, rules_inbound, rules_outbound):
        if self.is_locked():
            return (
                f"Firewall closed connection by timeout {FIREWALLD_STATE_TIMEOUT}sec."
            )
        self.set_state()
        if rules_inbound:
            self.delete_rule("inbound", rules_inbound)
        if rules_outbound:
            self.delete_rule("outbound", rules_outbound)
        self.save()
        return None

    def set_state(self):
        f = open(FIREWALLD_STATE_FILE, "w")
        f.write("1")
        f.close()

    def unset_state(self):
        f = open(FIREWALLD_STATE_FILE, "w")
        f.write("0")
        f.close()

    def read_state(self):
        state = False
        if os.path.isfile(FIREWALLD_STATE_FILE):
            f = open(FIREWALLD_STATE_FILE, "r")
            f_data = f.read()
            f.close()
            if f_data:
                state = f_data == "1"
        return state

    def is_locked(self):
        if self.read_state():
            seconds = 0
            while self.read_state():
                seconds += 1
                time.sleep(1)
                if seconds >= FIREWALLD_STATE_TIMEOUT:
                    return True
        return False

    def save(self):
        self.fw_direct.update(self.fw_direct.getSettings())
        self.unset_state()

    def query_rule(self, args):
        chain = self.chain + FIREWALL_CHAIN_PREFIX
        ipt_cmd = f"iptables -t {self.table} -C {chain} {' '.join(args)}"
        run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
        if run_ipt_cmd == 1:
            return False
        return True

    def query_rule_cfg(self, args):
        check = self.fw_direct.queryRule(
            self.ipv, self.table, self.chain, self.prio, args
        )
        return check

    def query_chain(self, chain):
        ipt_cmd = f"iptables -t {self.table} -L {chain}"
        run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
        if run_ipt_cmd == 1:
            return False
        return True

    def query_chain_cfg(self, chain):
        check = self.fw_direct.queryChain(self.ipv, self.table, chain)
        return check

    def query_chain_rule(self, chain, args):
        ipt_cmd = f"iptables -t {self.table} -C {chain} {' '.join(args)}"
        run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
        if run_ipt_cmd == 1:
            return False
        return True

    def query_chain_rule_cfg(self, chain, args):
        check = self.fw_direct.queryRule(self.ipv, self.table, chain, self.prio, args)
        return check

    def rule_args(self, chain, rule):
        ports = rule.get("ports")
        action = rule.get("action")
        protocol = rule.get("protocol")
        addresses = rule.get("addresses")
        opt = "-s" if chain == "inbound" else "-d"

        if isinstance(addresses, list):
            addresses = ", ".join(map(str, addresses))

        if action == "DROP":
            # Dirty hack for icmp request
            if protocol == "icmp":
                args = [
                    "-p",
                    "icmp",
                    "-m",
                    "conntrack",
                    "--ctstate",
                    "NEW",
                    "-j",
                    action,
                ]
            # Dirty hack for TCP dynamic socket ports
            if protocol == "tcp":
                args = [
                    "-p",
                    "tcp",
                    "-m",
                    "conntrack",
                    "--ctstate",
                    "NEW",
                    "-j",
                    action,
                ]
            # Dirty hack for UDP dynamic socket ports
            if protocol == "udp":
                args = [
                    "-p",
                    "udp",
                    "-m",
                    "conntrack",
                    "--ctstate",
                    "NEW",
                    "-j",
                    action,
                ]
            # Block all type of protocols
            if not protocol:
                args = ["-m", "conntrack", "--ctstate", "NEW", "-j", action]

        if action == "ACCEPT":
            if addresses:
                if protocol == "icmp":
                    args = ["-p", protocol, opt, addresses, "-j", action]
                if protocol == "tcp" or protocol == "udp":
                    if ports and ports != "0":
                        ports = str(ports)
                        if "-" in ports:
                            ports = ports.replace("-", ":")
                        args = [
                            "-p",
                            protocol,
                            opt,
                            addresses,
                            "--match",
                            "multiport",
                            "--dports",
                            ports,
                            "-j",
                            action,
                        ]
                    else:
                        args = ["-p", protocol, opt, addresses, "-j", action]
                # Allow all traffic from address
                if not protocol and not ports:
                    args = [opt, addresses, "-j", action]

        return args

    def create_firewall(self):
        ipv4_addrs = []

        # IPv4 Public
        if self.ipv4_public_addr:
            ipv4_addrs.append(self.ipv4_public_addr)
        # IPv4 Private
        if self.ipv4_private_addr:
            ipv4_addrs.append(self.ipv4_private_addr)

        for ipaddr in ipv4_addrs:
            in_args = ["-d", ipaddr, "-j", self.firewall_in_chain]
            out_args = ["-s", ipaddr, "-j", self.firewall_out_chain]

            # Create firewall IN chain
            if not self.query_chain(self.firewall_in_chain):
                ipt_cmd = f"iptables -N {self.firewall_in_chain}"
                run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
                if run_ipt_cmd == 0:
                    if not self.query_chain_cfg(self.firewall_in_chain):
                        self.fw_direct.addChain(
                            self.ipv, self.table, self.firewall_in_chain
                        )

            # Create firewall IN rule
            if not self.query_rule(in_args):
                chain = self.chain + FIREWALL_CHAIN_PREFIX
                ipt_cmd = f"iptables -t {self.table} -I {chain} {FIREWALL_INSERT_LINE} {' '.join(in_args)}"
                run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
                if run_ipt_cmd == 0:
                    if not self.query_rule_cfg(in_args):
                        self.fw_direct.addRule(
                            self.ipv, self.table, self.chain, self.prio, in_args
                        )

            # Create firewall OUT chain
            if not self.query_chain(self.firewall_out_chain):
                ipt_cmd = f"iptables -N {self.firewall_out_chain}"
                run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
                if run_ipt_cmd == 0:
                    if not self.query_chain_cfg(self.firewall_out_chain):
                        self.fw_direct.addChain(
                            self.ipv, self.table, self.firewall_out_chain
                        )

            # Create firewall OUT rule
            if not self.query_rule(out_args):
                chain = self.chain + FIREWALL_CHAIN_PREFIX
                ipt_cmd = f"iptables -t {self.table} -I {chain} {FIREWALL_INSERT_LINE} {' '.join(out_args)}"
                run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
                if run_ipt_cmd == 0:
                    if not self.query_rule_cfg(out_args):
                        self.fw_direct.addRule(
                            self.ipv, self.table, self.chain, self.prio, out_args
                        )

    def delete_firewall(self):
        ipv4_addrs = []

        # IPv4 Public
        if self.ipv4_public_addr:
            ipv4_addrs.append(self.ipv4_public_addr)
        # IPv4 Private
        if self.ipv4_private_addr:
            ipv4_addrs.append(self.ipv4_private_addr)

        for ipaddr in ipv4_addrs:
            in_args = ["-d", ipaddr, "-j", self.firewall_in_chain]
            out_args = ["-s", ipaddr, "-j", self.firewall_out_chain]

            # Remove firewall IN rule
            if self.query_rule(in_args):
                chain = self.chain + FIREWALL_CHAIN_PREFIX
                ipt_cmd = f"iptables -t {self.table} -D {chain} {' '.join(in_args)}"
                run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
                if run_ipt_cmd == 0:
                    if self.query_rule_cfg(in_args):
                        self.fw_direct.removeRule(
                            self.ipv, self.table, self.chain, self.prio, in_args
                        )

            # Remove firewall OUT rule
            if self.query_rule(out_args):
                chain = self.chain + FIREWALL_CHAIN_PREFIX
                ipt_cmd = f"iptables -t {self.table} -D {chain} {' '.join(out_args)}"
                run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
                if run_ipt_cmd == 0:
                    if self.query_rule_cfg(out_args):
                        self.fw_direct.removeRule(
                            self.ipv, self.table, self.chain, self.prio, out_args
                        )

            # Remove firewall rules
            for rule in self.fw_direct.getAllRules():
                if self.firewall_in_chain in rule:
                    ipt_cmd = f"iptables -t {self.table} -D {self.firewall_in_chain} {' '.join(rule[4])}"
                    run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
                    if run_ipt_cmd == 0:
                        self.fw_direct.removeRule(
                            rule[0], rule[1], rule[2], rule[3], rule[4]
                        )
                if self.firewall_out_chain in rule:
                    ipt_cmd = f"iptables -t {self.table} -D {self.firewall_out_chain} {' '.join(rule[4])}"
                    run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
                    if run_ipt_cmd == 0:
                        self.fw_direct.removeRule(
                            rule[0], rule[1], rule[2], rule[3], rule[4]
                        )

            # Remove firewall chains
            for chain in self.fw_direct.getAllChains():
                if self.firewall_in_chain in chain:
                    ipt_cmd = f"iptables -X {self.firewall_in_chain}"
                    run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
                    if run_ipt_cmd == 0:
                        self.fw_direct.removeChain(chain[0], chain[1], chain[2])
                if self.firewall_out_chain in chain:
                    ipt_cmd = f"iptables -X {self.firewall_out_chain}"
                    run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
                    if run_ipt_cmd == 0:
                        self.fw_direct.removeChain(chain[0], chain[1], chain[2])

    def create_rule(self, chain, rules):
        if chain == "inbound":
            firewall_chain = self.firewall_in_chain
        else:
            firewall_chain = self.firewall_out_chain
        for rule in rules:
            args = self.rule_args(chain, rule)
            if not self.query_chain_rule(firewall_chain, args):
                ipt_cmd = (
                    f"iptables -t {self.table} -I {firewall_chain} {' '.join(args)}"
                )
                if "DROP" in args:
                    ipt_cmd = (
                        f"iptables -t {self.table} -A {firewall_chain} {' '.join(args)}"
                    )
                run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
                if run_ipt_cmd == 0:
                    if "DROP" in args:
                        self.prio = 1
                    else:
                        self.prio = 0
                    if not self.query_chain_rule_cfg(firewall_chain, args):
                        self.fw_direct.addRule(
                            self.ipv, self.table, firewall_chain, self.prio, args
                        )

    def delete_rule(self, chain, rules):
        if chain == "inbound":
            firewall_chain = self.firewall_in_chain
        else:
            firewall_chain = self.firewall_out_chain
        for rule in rules:
            args = self.rule_args(chain, rule)
            if self.query_chain_rule(firewall_chain, args):
                ipt_cmd = (
                    f"iptables -t {self.table} -D {firewall_chain} {' '.join(args)}"
                )
                run_ipt_cmd = call(ipt_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
                if run_ipt_cmd == 0:
                    if "DROP" in args:
                        self.prio = 1
                    else:
                        self.prio = 0
                    if self.query_chain_rule_cfg(firewall_chain, args):
                        self.fw_direct.removeRule(
                            self.ipv, self.table, firewall_chain, self.prio, args
                        )
