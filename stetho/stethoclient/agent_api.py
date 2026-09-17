#!/usr/bin/python
# Copyright 2015 UnitedStack, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import jsonrpclib
import sys

from cliff.command import Command
from cliff.lister import Lister

LISTEN_PORT = 9698
SETUP_LINK_IP_PRE = "192.168.100."


def get_ip_suffix(agent_name):
    try:
        return agent_name.split("-")[1]
    except (IndexError, ValueError):
        pass
    try:
        agent_ip = AGENT_INFOS.get(agent_name)
        if agent_ip:
            return agent_ip.rsplit(".", 1)[1]
    except Exception:
        pass
    return "1"


class Logger:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"

    @staticmethod
    def log_normal(info):
        print(Logger.OKBLUE + info + Logger.ENDC)

    @staticmethod
    def log_high(info):
        print(Logger.OKGREEN + info + Logger.ENDC)

    @staticmethod
    def log_fail(info):
        print(Logger.FAIL + info + Logger.ENDC)


try:
    from stetho.stethoclient.constants import AGENT_INFOS
except:
    AGENT_INFOS = {
        "agent-64": "127.0.0.1",
        "agent-65": "127.0.0.1",
    }
    Logger.log_fail("Import stetho configure file fail. Use fake data!")


def setup_server(agent):
    log = logging.getLogger(__name__)
    if agent in AGENT_INFOS:
        log.debug("get agent:%s ip_address:%s" % (agent, AGENT_INFOS[agent]))
    else:
        log.error("Agent %s not configured. Please check it." % (agent))
        sys.exit()
    log.debug("Begin create connection with http://%s:9698." % (agent))
    server = jsonrpclib.Server("http://%s:%s" % (AGENT_INFOS[agent], LISTEN_PORT))
    log.debug("Create connection with %s success." % (agent))
    return server


class TearDownLink(Command):
    "Delete a link"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(TearDownLink, self).get_parser(prog_name)
        parser.add_argument("agent", default="bad")
        parser.add_argument("interface", default=".")
        return parser

    def take_action(self, parsed_args):
        self.log.debug("Get parsed_args: %s" % parsed_args)
        self.log.debug("Agent is %s" % parsed_args.agent)
        self.log.debug("Interface is %s" % parsed_args.interface)
        server = setup_server(parsed_args.agent)
        try:
            server.teardown_link(parsed_args.interface)
        except Exception as e:
            self.log.error("Error %s has occured." % str(e))


class SetUpLink(Lister):
    "Setup a link"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SetUpLink, self).get_parser(prog_name)
        parser.add_argument("agent", default="bad")
        parser.add_argument("interface", default="eth0")
        parser.add_argument("cidr", default=".")
        return parser

    def take_action(self, parsed_args):
        self.log.debug("Get parsed_args: %s" % parsed_args)
        self.log.debug("Agent is %s" % parsed_args.agent)
        self.log.debug("Interface is %s" % parsed_args.interface)
        self.log.debug("Cidr is %s" % parsed_args.cidr)
        server = setup_server(parsed_args.agent)
        try:
            res = server.setup_link(parsed_args.interface, parsed_args.cidr)
            self.log.debug("Response is %s" % res)
            if res["code"] == 1:
                Logger.log_fail(res["message"])
                sys.exit()
            res = server.get_interface(parsed_args.interface)
            self.log.debug("Response is %s" % res)
            if res["code"] == 1:
                Logger.log_fail(res["message"])
                sys.exit()
            if res["code"] == 0:
                return (("Field", "Value"), ((k, v) for k, v in res["data"].items()))
        except Exception as e:
            self.log.error("Agent %s return error: %s!" % (parsed_args.agent, e))
            sys.exit()


class GetInterface(Lister):
    "A test function that show a message"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(GetInterface, self).get_parser(prog_name)
        parser.add_argument("agent", default="bad")
        parser.add_argument("interface", default="eth0")
        return parser

    def take_action(self, parsed_args):
        self.log.debug("Get parsed_args: %s" % parsed_args)
        self.log.debug("Agent is %s" % parsed_args.agent)
        self.log.debug("Interface is %s" % parsed_args.interface)
        server = setup_server(parsed_args.agent)
        try:
            res = server.get_interface(parsed_args.interface)
            self.log.debug("Response is %s" % res)
            if res["code"] == 1:
                Logger.log_fail(res["message"])
                sys.exit()
            if res["code"] == 0:
                return (("Field", "Value"), ((k, v) for k, v in res["data"].items()))
        except:
            self.log.error("Agent %s return error!" % parsed_args.agent)
            sys.exit()


class AddVlanToInterface(Lister):
    "Setup a link"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(AddVlanToInterface, self).get_parser(prog_name)
        parser.add_argument("agent", default="bad")
        parser.add_argument("interface", default="eth0")
        parser.add_argument("vlan_id", default="1124")
        return parser

    def take_action(self, parsed_args):
        self.log.debug("Get parsed_args: %s" % parsed_args)
        self.log.debug("Agent is %s" % parsed_args.agent)
        self.log.debug("Interface is %s" % parsed_args.interface)
        self.log.debug("Vlan_id is %s" % parsed_args.vlan_id)
        server = setup_server(parsed_args.agent)
        try:
            server.add_vlan_to_interface(parsed_args.interface, parsed_args.vlan_id)
            new_interface = parsed_args.interface + "." + parsed_args.vlan_id
            res = server.get_interface(new_interface)
            self.log.debug("Response is %s" % res)
            if res["code"] == 1:
                Logger.log_fail(res["message"])
                sys.exit()
            if res["code"] == 0:
                return (("Field", "Value"), ((k, v) for k, v in res["data"].items()))
        except Exception as e:
            self.log.error("Agent %s return error: %s!" % (parsed_args.agent, e))
            sys.exit()


class AgentPing(Lister):
    "Ping a destination from one agent"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(AgentPing, self).get_parser(prog_name)
        parser.add_argument("agent", default="bad")
        parser.add_argument("destination", default="1.2.4.8")
        parser.add_argument("--count", nargs="?", default="2")
        parser.add_argument("--timeout", nargs="?", default="2")
        parser.add_argument("--interface", nargs="?", default="eth0")
        return parser

    def take_action(self, parsed_args):
        self.log.debug("Get parsed_args: %s" % parsed_args)
        server = setup_server(parsed_args.agent)
        try:
            dest = parsed_args.destination.split(",")
            res = server.ping(
                ips=dest,
                count=parsed_args.count,
                timeout=parsed_args.timeout,
                interface=parsed_args.interface,
            )
            self.log.debug("Response is %s" % res)
            if res["code"] == 1:
                Logger.log_fail(res["message"])
                sys.exit()
            if res["code"] == 0:
                return (
                    ("Destination", "Packet Loss (%)"),
                    ((k, v) for k, v in res["data"].items()),
                )
        except Exception as e:
            self.log.error("Agent %s return error: %s!" % (parsed_args.agent, e))
            sys.exit()


class CheckPortsOnBr(Lister):
    "Check a port if exists on a ovs bridge"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(CheckPortsOnBr, self).get_parser(prog_name)
        parser.add_argument("agent", default="bad")
        parser.add_argument("bridge", default="br-int")
        parser.add_argument("port", default="br-int")
        return parser

    def take_action(self, parsed_args):
        self.log.debug("Get parsed_args: %s" % parsed_args)
        server = setup_server(parsed_args.agent)
        try:
            res = server.check_ports_on_br(parsed_args.bridge, parsed_args.port)
            self.log.debug("Response is %s" % res)
            if res["code"] == 1:
                Logger.log_fail(res["message"])
                sys.exit()
            if res["code"] == 0:
                return (("Port", "Exists"), ((k, v) for k, v in res["data"].items()))
        except Exception as e:
            self.log.error("Agent %s return error: %s!" % (parsed_args.agent, e))
            sys.exit()


class CheckVlanInterface(Lister):
    """Check vlan if exists in switch"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(CheckVlanInterface, self).get_parser(prog_name)
        parser.add_argument("agentA", default="bad")
        parser.add_argument("agentB", default="bad")
        parser.add_argument("interface", default="eth0")
        parser.add_argument("vlan_id", default="1124")
        return parser

    def take_action(self, parsed_args):
        self.log.debug("Get parsed_args: %s" % parsed_args)
        serverA = setup_server(parsed_args.agentA)
        serverB = setup_server(parsed_args.agentB)
        try:
            interface = parsed_args.interface + "." + parsed_args.vlan_id
            resA = serverA.get_interface(interface)
            resB = serverB.get_interface(interface)
            if resA["code"] == 1:
                msg = "Agent: %s has no interface named %s!" % (
                    parsed_args.agentA,
                    interface,
                )
                Logger.log_fail(msg)
                sys.exit()
            if resB["code"] == 1:
                msg = "Agent: %s has no interface named %s!" % (
                    parsed_args.agentB,
                    interface,
                )
                Logger.log_fail(msg)
                sys.exit()
            resA = serverA.add_vlan_to_interface(
                parsed_args.interface, parsed_args.vlan_id
            )
            self.log.debug("Response is %s" % resA)
            if resA["code"] == 1:
                Logger.log_fail("AgentA add vlan failed: %s" % resA["message"])
                sys.exit()
            resB = serverB.add_vlan_to_interface(
                parsed_args.interface, parsed_args.vlan_id
            )
            self.log.debug("Response is %s" % resB)
            if resB["code"] == 1:
                Logger.log_fail("AgentB add vlan failed: %s" % resB["message"])
                sys.exit()
            Logger.log_normal(
                ("AgentA and agentB has already added the " "interface %s ")
                % (interface)
            )
            ipA = SETUP_LINK_IP_PRE + get_ip_suffix(parsed_args.agentA) + "/24"
            resA = serverA.setup_link(interface, ipA)
            self.log.debug("Response is %s" % resA)
            if resA["code"] == 1:
                Logger.log_fail("AgentA setup link failed: %s" % resA["message"])
                sys.exit()
            ipB = SETUP_LINK_IP_PRE + get_ip_suffix(parsed_args.agentB) + "/24"
            resB = serverB.setup_link(interface, ipB)
            self.log.debug("Response is %s" % resB)
            if resB["code"] == 1:
                Logger.log_fail("AgentB setup link failed: %s" % resB["message"])
                sys.exit()
            Logger.log_normal(
                ("AgentA and agentB has already setup the " "IP %s and IP %s")
                % (ipA, ipB)
            )
            ipB_for_ping = ipB.split("/")[0]
            res = serverA.ping(ips=[ipB_for_ping])
            resA = serverA.teardown_link(interface)
            self.log.debug("Response is %s" % resA)
            resB = serverB.teardown_link(interface)
            self.log.debug("Response is %s" % resB)
            Logger.log_normal(
                ("AgentA and agentB has already deleted the" "vlan %s in %s")
                % (parsed_args.vlan_id, parsed_args.interface)
            )
            if res["code"] == 0:
                return (
                    ("Destination", "Packet Loss (%)"),
                    ((k, v) for k, v in res["data"].items()),
                )
        except Exception as e:
            self.log.error("Agent error occurred: %s!" % str(e))
            sys.exit()
