"""NAPALM Netgear ProSafe Handler."""
import re
import socket

from napalm.base.base import NetworkDriver
from napalm.base.exceptions import (
    ConnectionClosedException
)
from napalm.base.helpers import (
    generate_regex_or
)
from napalm.base.netmiko_helpers import netmiko_args

from .parser import parseFixedLenght, parseList

MAP_INTERFACE_SPEED = {
    "10G Full": 10*1000,
    "1000 Full": 1000,
    "100 Full": 100,
    "100 Half": 100,
    "10 Full": 10,
    "10 Half": 10,
}


class NetgearDriver(NetworkDriver):
    """NAPALM Netgear ProSafe Handler."""

    def __init__(self, hostname, username, password, timeout=60, optional_args=None):
        """NAPALM Netgear ProSafe Handler."""
        if optional_args is None:
            optional_args = {}
        self.config = ""
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout

        self.transport = optional_args.get("transport", "ssh")

        self.netmiko_optional_args = netmiko_args(optional_args)

        self.device = None

        self.platform = "netgear_prosafe"

    def open(self):
        """Open a connection to the device."""
        self.device = self._netmiko_open(
            self.platform, netmiko_optional_args=self.netmiko_optional_args
        )

    def close(self):
        """Close the connection to the device and do the necessary cleanup."""
        self._netmiko_close()

    def _send_command(self, command):
        """Wrapper for self.device.send.command().

        If command is a list will iterate through commands until valid command.
        """
        try:
            if isinstance(command, list):
                for cmd in command:
                    output = self.device.send_command(cmd)
                    if "% Invalid" not in output:
                        break
            else:
                output = self.device.send_command(command)
            return self._send_command_postprocess(output)
        except (socket.error, EOFError) as e:
            raise ConnectionClosedException(str(e))

    @staticmethod
    def _send_command_postprocess(output):
        """
        Cleanup actions on send_command() for NAPALM getters.
        """
        return output.strip()

    def is_alive(self):
        """Returns a flag with the state of the connection."""
        null = chr(0)
        if self.device is None:
            return {"is_alive": False}
        # SSH
        try:
            # Try sending ASCII null byte to maintain the connection alive
            self.device.write_channel(null)
            return {"is_alive": self.device.remote_conn.transport.is_active()}
        except (socket.error, EOFError):
            # If unable to send, we can tell for sure that the connection is unusable
            return {"is_alive": False}

    def get_interfaces(self):
        """
        Get interface details.

        last_flapped is not implemented

        Example Output:

        {   u'Vlan1': {   'description': u'N/A',
                      'is_enabled': True,
                      'is_up': True,
                      'last_flapped': -1.0,
                      'mac_address': u'a493.4cc1.67a7',
                      'speed': 100},
        u'Vlan100': {   'description': u'Data Network',
                        'is_enabled': True,
                        'is_up': True,
                        'last_flapped': -1.0,
                        'mac_address': u'a493.4cc1.67a7',
                        'speed': 100},
        u'Vlan200': {   'description': u'Voice Network',
                        'is_enabled': True,
                        'is_up': True,
                        'last_flapped': -1.0,
                        'mac_address': u'a493.4cc1.67a7',
                        'speed': 100}}
        """
        # default values.
        last_flapped = -1.0

        command = "show interfaces status all"
        output = self._send_command(command)
        fields = parseFixedLenght(["name", "label", "state", "", "speed"], output.splitlines())

        interface_dict = {}
        for item in fields:
            if(item["name"].startswith("lag")):
                continue
            try:
                speed = MAP_INTERFACE_SPEED[item["speed"]]
            except KeyError:
                speed = 1000
            interface_dict[item["name"]] = {
                "is_enabled": True,
                "is_up": (item["state"] == "Up"),
                "description": item["label"],
                "mac_address": "",
                "last_flapped": last_flapped,
                "mtu": 1500,
                "speed": speed
            }

        return interface_dict

    def get_interfaces_counters(self):
        """
        Return interface counters and errors.

        'tx_errors': int,
        'rx_errors': int,
        'tx_discards': int,
        'rx_discards': int,
        'tx_octets': int,
        'rx_octets': int,
        'tx_unicast_packets': int,
        'rx_unicast_packets': int,
        'tx_multicast_packets': int,
        'rx_multicast_packets': int,
        'tx_broadcast_packets': int,
        'rx_broadcast_packets': int,

        Currently doesn't determine output broadcasts, multicasts
        """
        res = {}
        command = "show interfaces status all"
        output = self._send_command(command)
        interfaces = parseFixedLenght(["name"], output.splitlines())
        for a in interfaces:
            name = a["name"]
            if(name.startswith("lag")):
                break
            command = "show interface %s" % name
            output = self._send_command(command)
            stats = parseList(output.splitlines())
            res[name] = {
                'tx_errors': int(stats['Transmit Packet Errors']),
                'rx_errors': int(stats['Packets Received With Error']),
                'tx_discards': int(stats['Transmit Packets Discarded']),
                'rx_discards': int(stats['Receive Packets Discarded']),
                'tx_octets': -1,
                'rx_octets': -1,
                'tx_unicast_packets': int(stats['Packets Transmitted Without Errors']),
                'rx_unicast_packets': int(stats['Packets Received Without Error']),
                'tx_multicast_packets': -1,
                'rx_multicast_packets': -1,
                'tx_broadcast_packets': -1,
                'rx_broadcast_packets': int(stats['Broadcast Packets Received']),
            }
        return res

    def get_mac_address_table(self):
        """
        Returns a lists of dictionaries. Each dictionary represents an entry in the MAC Address
        Table, having the following keys
            * mac (string)
            * interface (string)
            * vlan (int)
            * active (boolean)
            * static (boolean)
            * moves (int)
            * last_move (float)
        """
        res = []
        command = "show mac-addr-table"
        output = self._send_command(command)
        fields = parseFixedLenght(["vlan", "mac", "interface", "", "status"], output.splitlines())
        for item in fields:
            res.append({
                "mac": item["mac"],
                "interface": item["interface"],
                "vlan": int(item["vlan"]),
                "active": True,
                "static": (item["status"] == "Learned"),
                "moves": -1,
                "last_move": -1.0
            })
        return res

    def get_config(self, retrieve="all", full=False, sanitized=False):
        """Implementation of get_config for Netgear Prosafe.

        Returns the startup or/and running configuration as dictionary.
        The keys of the dictionary represent the type of configuration
        (startup or running). The candidate is always empty string,
        since IOS does not support candidate configuration.
        """

        # The output of get_config should be directly usable by load_replace_candidate()
        # IOS adds some extra, unneeded lines that should be filtered.
        filter_strings = [
            r"^!System Up Time .*$",
            r"^!Current SNTP Synchronized Time:.*$",
        ]
        filter_pattern = generate_regex_or(filter_strings)

        configs = {"startup": "", "running": "", "candidate": ""}
        # Netgear only supports "all" on "show run"
        run_full = " all" if full else ""

        if retrieve in ("startup", "all"):
            command = "show startup-config"
            output = self._send_command(command)
            output = re.sub(filter_pattern, "", output, flags=re.M)
            configs["startup"] = output.strip()

        if retrieve in ("running", "all"):
            command = f"show running-config{run_full}"
            output = self._send_command(command)
            output = re.sub(filter_pattern, "", output, flags=re.M)
            configs["running"] = output.strip()

        return configs

    def load_replace_candidate(self, filename=None, config=None):
        """
        Populates the candidate configuration. You can populate it from a file or from a string.
        If you send both a filename and a string containing the configuration, the file takes
        precedence.
        If you use this method the existing configuration will be replaced entirely by the
        candidate configuration once you commit the changes. This method will not change the
        configuration by itself.
        :param filename: Path to the file containing the desired configuration. By default is None.
        :param config: String containing the desired configuration.
        :raise ReplaceConfigException: If there is an error on the configuration sent.
        """
        if(filename is not None):
            with open(filename, 'r') as f:
                config = f.read()
        self.config = config

    def load_merge_candidate(self, filename=None, config=None):
        """
        Populates the candidate configuration. You can populate it from a file or from a string.
        If you send both a filename and a string containing the configuration, the file takes
        precedence.
        If you use this method the existing configuration will be merged with the candidate
        configuration once you commit the changes. This method will not change the configuration
        by itself.
        :param filename: Path to the file containing the desired configuration. By default is None.
        :param config: String containing the desired configuration.
        :raise MergeConfigException: If there is an error on the configuration sent.
        """
        if(filename is not None):
            with open(filename, 'r') as f:
                config = f.read()
        self.config = config

    def compare_config(self):
        """
        :return: A string showing the difference between the running configuration and the \
        candidate configuration. The running_config is loaded automatically just before doing the \
        comparison so there is no need for you to do it.
        """
        return "some stuff might be different"

    def commit_config(self, message="", revert_in=None):
        """
        Commits the changes requested by the method load_replace_candidate or load_merge_candidate.
        NAPALM drivers that support 'commit confirm' should cause self.has_pending_commit
        to return True when a 'commit confirm' is in progress.
        Implementations should raise an exception if commit_config is called multiple times while a
        'commit confirm' is pending.
        :param message: Optional - configuration session commit message
        :type message: str
        :param revert_in: Optional - number of seconds before the configuration will be reverted
        :type revert_in: int|None
        """
        output = ""
        output = self.device.send_config_set(
            config_commands=self.config.splitlines(),
            enter_config_mode=False
        )
        output += self.device.save_config(confirm=True, confirm_response="")

    def get_facts(self):
        """
        Returns a dictionary containing the following information:
         * uptime - Uptime of the device in seconds.
         * vendor - Manufacturer of the device.
         * model - Device model.
         * hostname - Hostname of the device
         * fqdn - Fqdn of the device
         * os_version - String with the OS version running on the device.
         * serial_number - Serial number of the device
         * interface_list - List of the interfaces of the device
        Example::
            {
            'uptime': 151005.57332897186,
            'vendor': u'Arista',
            'os_version': u'4.14.3-2329074.gaatlantarel',
            'serial_number': u'SN0123A34AS',
            'model': u'vEOS',
            'hostname': u'eos-router',
            'fqdn': u'eos-router',
            'interface_list': [u'Ethernet2', u'Management1', u'Ethernet1', u'Ethernet3']
            }
        """

        command = "show ver"
        output = self._send_command(command)
        fields = parseList(output.splitlines())

        return {
            'uptime': 0.0,
            'vendor': 'Netgear',
            'os_version': fields["Software Version"],
            'serial_number': fields["Serial Number"],
            'model': fields["Machine Model"],
            'hostname': '',
            'fqdn': '',
            'interface_list': []
        }
