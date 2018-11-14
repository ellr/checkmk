#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# | Copyright Mathias Kettner 2014             mk@mathias-kettner.de |
# +------------------------------------------------------------------+
#
# This file is part of Check_MK.
# The official homepage is at http://mathias-kettner.de/check_mk.
#
# check_mk is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# tails. You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

import cmk.gui.watolib as watolib
from cmk.gui.i18n import _
from cmk.gui.exceptions import MKUserError
from cmk.gui.valuespec import (
    HTTPUrl,
    ListChoice,
    Checkbox,
    ListOf,
    FixedValue,
    Dictionary,
    Integer,
    TextAscii,
    Password,
    Alternative,
    ListOfStrings,
    DropdownChoice,
    Transform,
    TextUnicode,
    Tuple,
    ID,
    CascadingDropdown,
    Float,
    RegExp,
    RegExpUnicode,
    MonitoringState,
)

from cmk.gui.plugins.wato import (
    register_rulegroup,
    register_rule,
    monitoring_macro_help,
    IndividualOrStoredPassword,
)

import cmk.gui.bi as bi

group = "datasource_programs"

register_rulegroup(
    group,
    _("Datasource Programs"),
    _("Specialized agents, e.g. check via SSH, ESX vSphere, SAP R/3"),
)

register_rule(
    group, "datasource_programs",
    TextAscii(
        title=_("Individual program call instead of agent access"),
        help=_("For agent based checks Check_MK allows you to specify an alternative "
               "program that should be called by Check_MK instead of connecting the agent "
               "via TCP. That program must output the agent's data on standard output in "
               "the same format the agent would do. This is for example useful for monitoring "
               "via SSH.") + monitoring_macro_help(),
        label=_("Command line to execute"),
        empty_text=_("Access Check_MK Agent via TCP"),
        size=80,
        attrencode=True))

register_rule(
    group,
    "special_agents:ddn_s2a",
    Dictionary(
        elements=[
            ("username", TextAscii(title=_(u"Username"), allow_empty=False)),
            ("password", Password(title=_(u"Password"), allow_empty=False)),
            ("port", Integer(title=_(u"Port"), default_value=8008)),
        ],
        optional_keys=["port"],
    ),
    match="first",
    title=_(u"DDN S2A"),
)

register_rule(
    group,
    "special_agents:vsphere",
    Transform(
        valuespec=Dictionary(
            elements=[
                ("user", TextAscii(
                    title=_("vSphere User name"),
                    allow_empty=False,
                )),
                ("secret", Password(
                    title=_("vSphere secret"),
                    allow_empty=False,
                )),
                ("direct",
                 DropdownChoice(
                     title=_("Type of query"),
                     choices=[
                         (True, _("Queried host is a host system")),
                         ("hostsystem_agent",
                          _("Queried host is a host system with Check_MK Agent installed")),
                         (False, _("Queried host is the vCenter")),
                         ("agent", _("Queried host is the vCenter with Check_MK Agent installed")),
                     ],
                     default=True,
                 )),
                ("tcp_port",
                 Integer(
                     title=_("TCP Port number"),
                     help=_("Port number for HTTPS connection to vSphere"),
                     default_value=443,
                     minvalue=1,
                     maxvalue=65535,
                 )),
                ("ssl",
                 Alternative(
                     title=_("SSL certificate checking"),
                     elements=[
                         FixedValue(False, title=_("Deactivated"), totext=""),
                         FixedValue(True, title=_("Use hostname"), totext=""),
                         TextAscii(
                             title=_("Use other hostname"),
                             help=
                             _("The IP of the other hostname needs to be the same IP as the host address"
                              ))
                     ],
                     default_value=False)),
                ("timeout",
                 Integer(
                     title=_("Connect Timeout"),
                     help=_(
                         "The network timeout in seconds when communicating with vSphere or "
                         "to the Check_MK Agent. The default is 60 seconds. Please note that this "
                         "is not a total timeout but is applied to each individual network transation."
                     ),
                     default_value=60,
                     minvalue=1,
                     unit=_("seconds"),
                 )),
                ("use_pysphere",
                 Checkbox(
                     title=_("Compatibility mode"),
                     label=_("Support ESX 4.1 (using slower PySphere implementation)"),
                     true_label=_("Support 4.1"),
                     false_label=_("fast"),
                     help=_("The current very performant implementation of the ESX special agent "
                            "does not support older ESX versions than 5.0. Please use the slow "
                            "compatibility mode for those old hosts."),
                 )),
                ("infos",
                 Transform(
                     ListChoice(
                         choices=[
                             ("hostsystem", _("Host Systems")),
                             ("virtualmachine", _("Virtual Machines")),
                             ("datastore", _("Datastores")),
                             ("counters", _("Performance Counters")),
                             ("licenses", _("License Usage")),
                         ],
                         default_value=["hostsystem", "virtualmachine", "datastore", "counters"],
                         allow_empty=False,
                     ),
                     forth=lambda v: [x.replace("storage", "datastore") for x in v],
                     title=_("Retrieve information about..."),
                 )),
                ("skip_placeholder_vms",
                 Checkbox(
                     title=_("Placeholder VMs"),
                     label=_("Do no monitor placeholder VMs"),
                     default_value=True,
                     true_label=_("ignore"),
                     false_label=_("monitor"),
                     help=
                     _("Placeholder VMs are created by the Site Recovery Manager(SRM) and act as backup "
                       "virtual machines in case the default vm is unable to start. This option tells the "
                       "vsphere agent to exclude placeholder vms in its output."))),
                ("host_pwr_display",
                 DropdownChoice(
                     title=_("Display ESX Host power state on"),
                     choices=[
                         (None, _("The queried ESX system (vCenter / Host)")),
                         ("esxhost", _("The ESX Host")),
                         ("vm", _("The Virtual Machine")),
                     ],
                     default=None,
                 )),
                ("vm_pwr_display",
                 DropdownChoice(
                     title=_("Display VM power state <i>additionally</i> on"),
                     help=_("The power state can be displayed additionally either "
                            "on the ESX host or the VM. This will result in services "
                            "for <i>both</i> the queried system and the ESX host / VM. "
                            "By disabling the unwanted services it is then possible "
                            "to configure where the services are displayed."),
                     choices=[
                         (None, _("The queried ESX system (vCenter / Host)")),
                         ("esxhost", _("The ESX Host")),
                         ("vm", _("The Virtual Machine")),
                     ],
                     default=None,
                 )),
                ("snapshot_display",
                 DropdownChoice(
                     title=_("<i>Additionally</i> display snapshots on"),
                     help=_("The created snapshots can be displayed additionally either "
                            "on the ESX host or the vCenter. This will result in services "
                            "for <i>both</i> the queried system and the ESX host / vCenter. "
                            "By disabling the unwanted services it is then possible "
                            "to configure where the services are displayed."),
                     choices=[
                         (None, _("The Virtual Machine")),
                         ("esxhost", _("The ESX Host")),
                         ("vCenter", _("The queried ESX system (vCenter / Host)")),
                     ],
                     default=None,
                 )),
                ("vm_piggyname",
                 DropdownChoice(
                     title=_("Piggyback name of virtual machines"),
                     choices=[
                         ("alias", _("Use the name specified in the ESX system")),
                         ("hostname",
                          _("Use the VMs hostname if set, otherwise fall back to ESX name")),
                     ],
                     default="alias",
                 )),
                ("spaces",
                 DropdownChoice(
                     title=_("Spaces in hostnames"),
                     choices=[
                         ("cut", _("Cut everything after first space")),
                         ("underscore", _("Replace with underscores")),
                     ],
                     default="underscore",
                 )),
            ],
            optional_keys=[
                "tcp_port",
                "timeout",
                "vm_pwr_display",
                "host_pwr_display",
                "vm_piggyname",
            ],
        ),
        title=_("Check state of VMWare ESX via vSphere"),
        help=_("This rule selects the vSphere agent instead of the normal Check_MK Agent "
               "and allows monitoring of VMWare ESX via the vSphere API. You can configure "
               "your connection settings here."),
        forth=lambda a: dict([("skip_placeholder_vms", True), ("ssl", False), ("use_pysphere" , False), ("spaces", "underscore")] + a.items())
    ),
    factory_default=watolib.Rulespec.
    FACTORY_DEFAULT_UNUSED,  # No default, do not use setting if no rule matches
    match='first')

register_rule(
    group,
    "special_agents:hp_msa",
    Dictionary(
        elements=[
            ("username", TextAscii(
                title=_("Username"),
                allow_empty=False,
            )),
            ("password", Password(
                title=_("Password"),
                allow_empty=False,
            )),
        ],
        optional_keys=False),
    title=_("Check HP MSA via Web Interface"),
    help=_("This rule selects the Agent HP MSA instead of the normal Check_MK Agent "
           "which collects the data through the HP MSA web interface"),
    match='first')

vs_ipmi_common_elements = [
    ("username", TextAscii(
        title=_("Username"),
        allow_empty=False,
    )),
    ("password", Password(
        title=_("Password"),
        allow_empty=False,
    )),
    ("privilege_lvl",
     TextAscii(
         title=_("Privilege Level"),
         help=_("Possible are 'user', 'operator', 'admin'"),
         allow_empty=False,
     )),
]

vs_freeipmi = Dictionary(
    elements=vs_ipmi_common_elements + [
        ("ipmi_driver", TextAscii(title=_("IPMI driver"))),
        ("driver_type", TextAscii(title=_("IPMI driver type"))),
        ("BMC_key", TextAscii(title=_("BMC key"))),
        ("quiet_cache", Checkbox(title=_("Quiet cache"), label=_("Enable"))),
        ("sdr_cache_recreate", Checkbox(title=_("SDR cache recreate"), label=_("Enable"))),
        ("interpret_oem_data", Checkbox(title=_("OEM data interpretation"), label=_("Enable"))),
        ("output_sensor_state", Checkbox(title=_("Sensor state"), label=_("Enable"))),
        ("output_sensor_thresholds", Checkbox(title=_("Sensor threshold"), label=_("Enable"))),
        ("ignore_not_available_sensors",
         Checkbox(title=_("Suppress not available sensors"), label=_("Enable"))),
    ],
    optional_keys=[
        "ipmi_driver",
        "driver_type",
        "quiet_cache",
        "sdr_cache_recreate",
        "interpret_oem_data",
        "output_sensor_state",
        "output_sensor_thresholds",
        "ignore_not_available_sensors",
        "BMC_key",
    ])

vs_ipmitool = Dictionary(elements=vs_ipmi_common_elements, optional_keys=[])


def transform_ipmi_sensors(params):
    if isinstance(params, dict):
        return ("freeipmi", params)
    return params


register_rule(
    group,
    "special_agents:ipmi_sensors",
    Transform(
        CascadingDropdown(
            title=_("IPMI"),
            choices=[
                ("freeipmi", _("Use FreeIPMI"), vs_freeipmi),
                ("ipmitool", _("Use IPMItool"), vs_ipmitool),
            ],
            required_keys=["username", "password", "privilege_lvl"],
        ),
        forth=transform_ipmi_sensors),
    title=_("Check IPMI Sensors via Freeipmi or IPMItool"),
    help=_("This rule selects the Agent IPMI Sensors instead of the normal Check_MK Agent "
           "which collects the data through the FreeIPMI resp. IPMItool command"),
    match='first')

register_rule(
    group,
    "special_agents:netapp",
    Transform(
        Dictionary(
            title=_("Username and password for the NetApp Filer."),
            elements=[
                ("username", TextAscii(
                    title=_("Username"),
                    allow_empty=False,
                )),
                ("password", Password(
                    title=_("Password"),
                    allow_empty=False,
                )),
                ("skip_elements",
                 ListChoice(
                     choices=[
                         ("ctr_volumes", _("Do not query volume performance counters")),
                     ],
                     title=_("Performance improvements"),
                     help=_(
                         "Here you can configure whether the performance counters should get queried. "
                         "This can save quite a lot of CPU load on larger systems."),
                 )),
            ],
            optional_keys=False),
        forth=lambda x: dict([("skip_elements", [])] + x.items())),
    title=_("Check NetApp via WebAPI"),
    help=_(
        "This rule set selects the NetApp special agent instead of the normal Check_MK Agent "
        "and allows monitoring via the NetApp Web API. To access the data the "
        "user requires permissions to several API classes. They are shown when you call the agent with "
        "<tt>agent_netapp --help</tt>. The agent itself is located in the site directory under "
        "<tt>~/share/check_mk/agents/special</tt>."),
    match='first')


def transform_activemq(value):
    if not isinstance(value, tuple):
        return value

    new_value = {}
    new_value["servername"] = value[0]
    new_value["port"] = value[1]
    new_value["use_piggyback"] = "piggybag" in value[2]  # piggybag...
    return new_value


register_rule(
    group,
    "special_agents:activemq",
    Transform(
        Dictionary(
            elements=[("servername", TextAscii(title=_("Server Name"))),
                      ("port", Integer(title=_("Port Number"), default_value=8161)),
                      ("use_piggyback", Checkbox(title=_("Use Piggyback"), label=_("Enable"))),
                      ("basicauth",
                       Tuple(
                           title=_("BasicAuth settings (optional)"),
                           elements=[TextAscii(title=_("Username")),
                                     Password(title=_("Password"))]))],
            optional_keys=["basicauth"]),
        title=_("Apache ActiveMQ queues"),
        forth=transform_activemq),
    factory_default=watolib.Rulespec.
    FACTORY_DEFAULT_UNUSED,  # No default, do not use setting if no rule matches
    match="first")

register_rule(
    group,
    "special_agents:emcvnx",
    Dictionary(
        title=_("Check state of EMC VNX storage systems"),
        help=_("This rule selects the EMC VNX agent instead of the normal Check_MK Agent "
               "and allows monitoring of EMC VNX storage systems by calling naviseccli "
               "commandline tool locally on the monitoring system. Make sure it is installed "
               "and working. You can configure your connection settings here."),
        elements=[
            ("user",
             TextAscii(
                 title=_("EMC VNX admin user name"),
                 allow_empty=True,
                 help=_(
                     "If you leave user name and password empty, the special agent tries to "
                     "authenticate against the EMC VNX device by Security Files. "
                     "These need to be created manually before using. Therefor run as "
                     "instance user (if using OMD) or Nagios user (if not using OMD) "
                     "a command like "
                     "<tt>naviseccli -AddUserSecurity -scope 0 -password PASSWORD -user USER</tt> "
                     "This creates <tt>SecuredCLISecurityFile.xml</tt> and "
                     "<tt>SecuredCLIXMLEncrypted.key</tt> in the home directory of the user "
                     "and these files are used then."),
             )),
            ("password", Password(
                title=_("EMC VNX admin user password"),
                allow_empty=True,
            )),
            ("infos",
             Transform(
                 ListChoice(
                     choices=[
                         ("disks", _("Disks")),
                         ("hba", _("iSCSI HBAs")),
                         ("hwstatus", _("Hardware status")),
                         ("raidgroups", _("RAID groups")),
                         ("agent", _("Model and revsion")),
                         ("sp_util", _("Storage processor utilization")),
                         ("writecache", _("Write cache state")),
                         ("mirrorview", _("Mirror views")),
                         ("storage_pools", _("Storage pools")),
                     ],
                     default_value=[
                         "disks",
                         "hba",
                         "hwstatus",
                     ],
                     allow_empty=False,
                 ),
                 title=_("Retrieve information about..."),
             )),
        ],
        optional_keys=[],
    ),
    factory_default=watolib.Rulespec.
    FACTORY_DEFAULT_UNUSED,  # No default, do not use setting if no rule matches
    match='first')

register_rule(
    group,
    "special_agents:ibmsvc",
    Dictionary(
        title=_("Check state of IBM SVC / V7000 storage systems"),
        help=_(
            "This rule set selects the <tt>ibmsvc</tt> agent instead of the normal Check_MK Agent "
            "and allows monitoring of IBM SVC / V7000 storage systems by calling "
            "ls* commands there over SSH. "
            "Make sure you have SSH key authentication enabled for your monitoring user. "
            "That means: The user your monitoring is running under on the monitoring "
            "system must be able to ssh to the storage system as the user you gave below "
            "without password."),
        elements=[
            ("user",
             TextAscii(
                 title=_("IBM SVC / V7000 user name"),
                 allow_empty=True,
                 help=_("User name on the storage system. Read only permissions are sufficient."),
             )),
            ("accept-any-hostkey",
             Checkbox(
                 title=_("Accept any SSH Host Key"),
                 label=_("Accept any SSH Host Key"),
                 default_value=False,
                 help=_(
                     "Accepts any SSH Host Key presented by the storage device. "
                     "Please note: This might be a security issue because man-in-the-middle "
                     "attacks are not recognized! Better solution would be to add the "
                     "SSH Host Key of the monitored storage devices to the .ssh/known_hosts "
                     "file for the user your monitoring is running under (on OMD: the site user)"))
            ),
            ("infos",
             Transform(
                 ListChoice(
                     choices=[
                         ("lshost", _("Hosts Connected")),
                         ("lslicense", _("Licensing Status")),
                         ("lsmdisk", _("MDisks")),
                         ("lsmdiskgrp", _("MDisksGrps")),
                         ("lsnode", _("IO Groups")),
                         ("lsnodestats", _("Node Stats")),
                         ("lssystem", _("System Info")),
                         ("lssystemstats", _("System Stats")),
                         ("lseventlog", _("Event Log")),
                         ("lsportfc", _("FC Ports")),
                         ("lsportsas", _("SAS Ports")),
                         ("lsenclosure", _("Enclosures")),
                         ("lsenclosurestats", _("Enclosure Stats")),
                         ("lsarray", _("RAID Arrays")),
                         ("disks", _("Physical Disks")),
                     ],
                     default_value=[
                         "lshost", "lslicense", "lsmdisk", "lsmdiskgrp", "lsnode", "lsnodestats",
                         "lssystem", "lssystemstats", "lsportfc", "lsenclosure", "lsenclosurestats",
                         "lsarray", "disks"
                     ],
                     allow_empty=False,
                 ),
                 title=_("Retrieve information about..."),
             )),
        ],
        optional_keys=[],
    ),
    factory_default=watolib.Rulespec.
    FACTORY_DEFAULT_UNUSED,  # No default, do not use setting if no rule matches
    match='first')

register_rule(
    group,
    "special_agents:random",
    FixedValue(
        {},
        title=_("Create random monitoring data"),
        help=_("By configuring this rule for a host - instead of the normal "
               "Check_MK agent random monitoring data will be created."),
        totext=_("Create random monitoring data"),
    ),
    factory_default=watolib.Rulespec.
    FACTORY_DEFAULT_UNUSED,  # No default, do not use setting if no rule matches
    match='first')

register_rule(
    group,
    "special_agents:acme_sbc",
    FixedValue(
        {},
        title=_("Check ACME Session Border Controller"),
        help=_("This rule activates an agent which connects "
               "to an ACME Session Border Controller (SBC). This agent uses SSH, so "
               "you have to exchange an SSH key to make a passwordless connect possible."),
        totext=_("Connect to ACME SBC"),
    ),
    factory_default=watolib.Rulespec.
    FACTORY_DEFAULT_UNUSED,  # No default, do not use setting if no rule matches
    match='first')

register_rule(
    group,
    "special_agents:fritzbox",
    Dictionary(
        title=_("Check state of Fritz!Box Devices"),
        help=_("This rule selects the Fritz!Box agent, which uses UPNP to gather information "
               "about configuration and connection status information."),
        elements=[
            ("timeout",
             Integer(
                 title=_("Connect Timeout"),
                 help=_("The network timeout in seconds when communicating via UPNP. "
                        "The default is 10 seconds. Please note that this "
                        "is not a total timeout, instead it is applied to each API call."),
                 default_value=10,
                 minvalue=1,
                 unit=_("seconds"),
             )),
        ],
        optional_keys=["timeout"],
    ),
    factory_default=watolib.Rulespec.
    FACTORY_DEFAULT_UNUSED,  # No default, do not use setting if no rule matches
    match='first')

register_rulegroup("datasource_programs", _("Datasource Programs"),
                   _("Specialized agents, e.g. check via SSH, ESX vSphere, SAP R/3"))

group = "datasource_programs"

register_rule(
    group,
    "special_agents:innovaphone",
    Tuple(
        title=_("Innovaphone Gateways"),
        help=_("Please specify the user and password needed to access the xml interface"),
        elements=[
            TextAscii(title=_("Username")),
            Password(title=_("Password")),
        ]),
    factory_default=watolib.Rulespec.FACTORY_DEFAULT_UNUSED,
    match="first")

register_rule(
    group,
    "special_agents:hivemanager",
    Tuple(
        title=_("Aerohive HiveManager"),
        help=_("Activate monitoring of host via a HTTP connect to the HiveManager"),
        elements=[
            TextAscii(title=_("Username")),
            Password(title=_("Password")),
        ]),
    factory_default=watolib.Rulespec.FACTORY_DEFAULT_UNUSED,
    match="first")

register_rule(
    group,
    "special_agents:hivemanager_ng",
    Dictionary(
        title=_("Aerohive HiveManager NG"),
        help=_("Activate monitoring of the HiveManagerNG cloud."),
        elements=[
            ("url",
             HTTPUrl(
                 title=_("URL to HiveManagerNG, e.g. https://cloud.aerohive.com"),
                 allow_empty=False,
             )),
            ("vhm_id", TextAscii(
                title=_("Numerical ID of the VHM, e.g. 102"),
                allow_empty=False,
            )),
            ("api_token", TextAscii(
                title=_("API Access Token"),
                size=64,
                allow_empty=False,
            )),
            ("client_id", TextAscii(
                title=_("Client ID"),
                allow_empty=False,
            )),
            ("client_secret", Password(
                title=_("Client secret"),
                allow_empty=False,
            )),
            ("redirect_url", HTTPUrl(
                title=_("Redirect URL (has to be https)"),
                allow_empty=False,
            )),
        ],
        optional_keys=None,
    ),
    factory_default=watolib.Rulespec.FACTORY_DEFAULT_UNUSED,
    match="first",
)

register_rule(
    group,
    "special_agents:allnet_ip_sensoric",
    Dictionary(
        title=_("Check state of ALLNET IP Sensoric Devices"),
        help=_("This rule selects the ALLNET IP Sensoric agent, which fetches "
               "/xml/sensordata.xml from the device by HTTP and extracts the "
               "needed monitoring information from this file."),
        elements=[
            ("timeout",
             Integer(
                 title=_("Connect Timeout"),
                 help=_("The network timeout in seconds when communicating via HTTP. "
                        "The default is 10 seconds."),
                 default_value=10,
                 minvalue=1,
                 unit=_("seconds"),
             )),
        ],
        optional_keys=["timeout"],
    ),
    factory_default=watolib.Rulespec.
    FACTORY_DEFAULT_UNUSED,  # No default, do not use setting if no rule matches
    match='first')

register_rule(
    group,
    "special_agents:ucs_bladecenter",
    Dictionary(
        elements=[
            ("username", TextAscii(
                title=_("Username"),
                allow_empty=False,
            )),
            ("password", Password(
                title=_("Password"),
                allow_empty=False,
            )),
            ("no_cert_check",
             FixedValue(
                 True,
                 title=_("Disable SSL certificate validation"),
                 totext=_("SSL certificate validation is disabled"),
             )),
        ],
        optional_keys=['no_cert_check']),
    title=_("Check state of UCS Bladecenter"),
    help=_("This rule selects the UCS Bladecenter agent instead of the normal Check_MK Agent "
           "which collects the data through the UCS Bladecenter Web API"),
    match='first')


def validate_siemens_plc_values(value, varprefix):
    valuetypes = {}
    for index, (_db_number, _address, _datatype, valuetype, ident) in enumerate(value):
        valuetypes.setdefault(valuetype, [])
        if ident in valuetypes[valuetype]:
            raise MKUserError("%s_%d_%d" % (varprefix, index + 1, 4),
                              _("The ident of a value needs to be unique per valuetype."))
        valuetypes[valuetype].append(ident)


_siemens_plc_value = [
    Transform(
        CascadingDropdown(
            title=_("The Area"),
            choices=[
                ("db", _("Datenbaustein"),
                 Integer(
                     title="<nobr>%s</nobr>" % _("DB Number"),
                     minvalue=1,
                 )),
                ("input", _("Input")),
                ("output", _("Output")),
                ("merker", _("Merker")),
                ("timer", _("Timer")),
                ("counter", _("Counter")),
            ],
            orientation="horizontal",
            sorted=True,
        ),
        # Transform old Integer() value spec to new cascading dropdown value
        forth=lambda x: isinstance(x, int) and ("db", x) or x,
    ),
    Float(
        title=_("Address"),
        display_format="%.1f",
        help=_("Addresses are specified with a dot notation, where number "
               "before the dot specify the byte to fetch and the number after the "
               "dot specifies the bit to fetch. The number of the bit is always "
               "between 0 and 7."),
    ),
    CascadingDropdown(
        title=_("Datatype"),
        choices=[
            ("dint", _("Double Integer (DINT)")),
            ("real", _("Real Number (REAL)")),
            ("bit", _("Single Bit (BOOL)")),
            ("str", _("String (STR)"), Integer(
                minvalue=1,
                title=_("Size"),
                unit=_("Bytes"),
            )),
            ("raw", _("Raw Bytes (HEXSTR)"), Integer(
                minvalue=1,
                title=_("Size"),
                unit=_("Bytes"),
            )),
        ],
        orientation="horizontal",
        sorted=True,
    ),
    DropdownChoice(
        title=_("Type of the value"),
        choices=[
            (None, _("Unclassified")),
            ("temp", _("Temperature")),
            ("hours_operation", _("Hours of operation")),
            ("hours_since_service", _("Hours since service")),
            ("hours", _("Hours")),
            ("seconds_operation", _("Seconds of operation")),
            ("seconds_since_service", _("Seconds since service")),
            ("seconds", _("Seconds")),
            ("counter", _("Increasing counter")),
            ("flag", _("State flag (on/off)")),
            ("text", _("Text")),
        ],
        sorted=True,
    ),
    ID(
        title=_("Ident of the value"),
        help=_(" An identifier of your choice. This identifier "
               "is used by the Check_MK checks to access "
               "and identify the single values. The identifier "
               "needs to be unique within a group of VALUETYPES."),
    ),
]

group = "datasource_programs"
register_rule(
    group,
    "special_agents:siemens_plc",
    Dictionary(
        elements=[
            ("devices",
             ListOf(
                 Dictionary(
                     elements=[
                         ('host_name',
                          TextAscii(
                              title=_('Name of the PLC'),
                              allow_empty=False,
                              help=_(
                                  'Specify the logical name, e.g. the hostname, of the PLC. This name '
                                  'is used to name the resulting services.'))),
                         ('host_address',
                          TextAscii(
                              title=_('Network Address'),
                              allow_empty=False,
                              help=
                              _('Specify the hostname or IP address of the PLC to communicate with.'
                               ))),
                         ("rack", Integer(
                             title=_("Number of the Rack"),
                             minvalue=0,
                         )),
                         ("slot", Integer(
                             title=_("Number of the Slot"),
                             minvalue=0,
                         )),
                         ("tcp_port",
                          Integer(
                              title=_("TCP Port number"),
                              help=_("Port number for communicating with the PLC"),
                              default_value=102,
                              minvalue=1,
                              maxvalue=65535,
                          )),
                         ("timeout",
                          Integer(
                              title=_("Connect Timeout"),
                              help=_(
                                  "The connect timeout in seconds when establishing a connection "
                                  "with the PLC."),
                              default_value=60,
                              minvalue=1,
                              unit=_("seconds"),
                          )),
                         ("values",
                          ListOf(
                              Tuple(
                                  elements=_siemens_plc_value,
                                  orientation="horizontal",
                              ),
                              title=_("Values to fetch from this device"),
                              validate=validate_siemens_plc_values,
                              magic='@?@',
                          )),
                     ],
                     optional_keys=["timeout"],
                 ),
                 title=_("Devices to fetch information from"),
             )),
            ("values",
             ListOf(
                 Tuple(
                     elements=_siemens_plc_value,
                     orientation="horizontal",
                 ),
                 title=_("Values to fetch from all devices"),
                 validate=validate_siemens_plc_values,
             )),
        ],
        optional_keys=["timeout"],
        title=_("Siemens PLC (SPS)"),
        help=_("This rule selects the Siemens PLC agent instead of the normal Check_MK Agent "
               "and allows monitoring of Siemens PLC using the Snap7 API. You can configure "
               "your connection settings and values to fetch here."),
    ),
    factory_default=watolib.Rulespec.
    FACTORY_DEFAULT_UNUSED,  # No default, do not use setting if no rule matches
    match='first')

register_rule(
    group,
    "special_agents:ruckus_spot",
    Dictionary(
        elements=[
            ("address",
             Alternative(
                 title=_("Server Address"),
                 help=_("Here you can set a manual address if the server differs from the host"),
                 elements=[
                     FixedValue(True, title=_("Use host address"), totext=""),
                     TextAscii(title=_("Enter address"))
                 ],
                 default_value=True)),
            ("port", Integer(title=_("Port"), allow_empty=False, default_value=8443)),
            ("venueid", TextAscii(
                title=_("Venue ID"),
                allow_empty=False,
            )),
            ("api_key", TextAscii(title=_("API key"), allow_empty=False, size=70)),
            ("cmk_agent",
             Dictionary(
                 title=_("Also contact Check_MK agent"),
                 help=_("With this setting, the special agent will also contact the "
                        "Check_MK agent on the same system at the specified port."),
                 elements=[("port", Integer(
                     title=_("Port"),
                     default_value=6556,
                     allow_empty=False,
                 ))],
                 optional_keys=[])),
        ],
        optional_keys=["cmk_agent"]),
    title=_("Agent for Ruckus Spot"),
    help=_("This rule selects the Agent Ruckus Spot agent instead of the normal Check_MK Agent "
           "which collects the data through the Ruckus Spot web interface"),
    match='first')

group = 'datasource_programs'
register_rule(
    group,
    'special_agents:appdynamics',
    Dictionary(
        elements=[
            ('username', TextAscii(
                title=_('AppDynamics login username'),
                allow_empty=False,
            )),
            ('password', Password(
                title=_('AppDynamics login password'),
                allow_empty=False,
            )),
            ('application',
             TextAscii(
                 title=_('AppDynamics application name'),
                 help=
                 _('This is the application name used in the URL. If you enter for example the application '
                   'name <tt>foobar</tt>, this would result in the URL being used to contact the REST API: '
                   '<tt>/controller/rest/applications/foobar/metric-data</tt>'),
                 allow_empty=False,
                 size=40,
             )),
            ('port',
             Integer(
                 title=_('TCP port number'),
                 help=_('Port number that AppDynamics is listening on. The default is 8090.'),
                 default_value=8090,
                 minvalue=1,
                 maxvalue=65535,
             )),
            ('timeout',
             Integer(
                 title=_('Connection timeout'),
                 help=_('The network timeout in seconds when communicating with AppDynamics.'
                        'The default is 30 seconds.'),
                 default_value=30,
                 minvalue=1,
                 unit=_('seconds'),
             )),
        ],
        optional_keys=['port', 'timeout'],
    ),
    title=_('AppDynamics via REST API'),
    help=_('This rule allows querying an AppDynamics server for information about Java applications'
           'via the AppDynamics REST API. You can configure your connection settings here.'),
    factory_default=watolib.Rulespec.
    FACTORY_DEFAULT_UNUSED,  # No default, do not use setting if no rule matches
    match='first')

mk_jolokia_elements = [
    ("port",
     Integer(
         title=_("TCP port for connection"),
         default_value=8080,
         minvalue=1,
         maxvalue=65535,
     )),
    ("login",
     Tuple(
         title=_("Optional login (if required)"),
         elements=[
             TextAscii(
                 title=_("User ID for web login (if login required)"),
                 default_value="monitoring",
             ),
             Password(title=_("Password for this user")),
             DropdownChoice(
                 title=_("Login mode"),
                 choices=[
                     ("basic", _("HTTP Basic Authentication")),
                     ("digest", _("HTTP Digest")),
                 ])
         ])),
    ("suburi",
     TextAscii(
         title=_("relative URI under which Jolokia is visible"),
         default_value="jolokia",
         size=30,
     )),
    ("instance",
     TextUnicode(
         title=_("Name of the instance in the monitoring"),
         help=_("If you do not specify a name here, then the TCP port number "
                "will be used as an instance name."))),
    ("protocol", DropdownChoice(
        title=_("Protocol"), choices=[
            ("http", "HTTP"),
            ("https", "HTTPS"),
        ])),
]

group = 'datasource_programs'
register_rule(
    group,
    'special_agents:jolokia',
    Dictionary(elements=mk_jolokia_elements,),
    title=_('Jolokia'),
    help=_('This rule allows querying the Jolokia web API.'),
    factory_default=watolib.Rulespec.
    FACTORY_DEFAULT_UNUSED,  # No default, do not use setting if no rule matches
    match='first')

register_rule(
    group,
    "special_agents:tinkerforge",
    Dictionary(
        title=_("Settings for Tinkerforge agent"),
        elements=[
            ("port",
             Integer(
                 title=_('TCP port number'),
                 help=_('Port number that AppDynamics is listening on. The default is 8090.'),
                 default_value=4223,
                 minvalue=1,
                 maxvalue=65535)),
            ("segment_display_uid",
             TextAscii(
                 title=_("7-segment display uid"),
                 help=_(
                     "This is the uid of the sensor you want to display in the 7-segment display, "
                     "not the uid of the display itself. There is currently no support for "
                     "controling multiple displays."))),
            ("segment_display_brightness",
             Integer(title=_("7-segment display brightness"), minvalue=0, maxvalue=7))
        ],
    ),
    title=_("Tinkerforge"),
    match='first')

register_rule(
    group,
    'special_agents:prism',
    Dictionary(
        elements=[
            ("port",
             Integer(
                 title=_("TCP port for connection"), default_value=9440, minvalue=1,
                 maxvalue=65535)),
            ("username", TextAscii(title=_("User ID for web login"),)),
            ("password", Password(title=_("Password for this user"))),
        ],
        optional_keys=["port"]),
    title=_("Nutanix Prism"),
    match='first')


def _transform_3par_add_verify_cert(v):
    v.setdefault("verify_cert", False)
    return v


register_rule(
    "datasource_programs",
    "special_agents:3par",
    Transform(
        Dictionary(
            elements=[
                ("user", TextAscii(
                    title=_("Username"),
                    allow_empty=False,
                )),
                ("password", IndividualOrStoredPassword(
                    title=_("Password"),
                    allow_empty=False,
                )),
                ("verify_cert",
                 DropdownChoice(
                     title=_("SSL certificate verification"),
                     choices=[
                         (True, _("Activate")),
                         (False, _("Deactivate")),
                     ],
                 )),
                ("values",
                 ListOfStrings(
                     title=_("Values to fetch"),
                     orientation="horizontal",
                     help=_("Possible values are the following: cpgs, volumes, hosts, capacity, "
                            "system, ports, remotecopy, hostsets, volumesets, vluns, flashcache, "
                            "users, roles, qos.\n"
                            "If you do not specify any value the first seven are used as default."),
                 )),
            ],
            optional_keys=["values"],
        ),
        # verify_cert was added with 1.5.0p1
        forth=_transform_3par_add_verify_cert,
    ),
    title=_("Agent 3PAR Configuration"),
    match='first',
)

register_rule(
    group,
    "special_agents:storeonce",
    Dictionary(
        optional_keys=["cert"],
        elements=[
            ("user", TextAscii(title=_("Username"), allow_empty=False)),
            ("password", Password(title=_("Password"), allow_empty=False)),
            ("cert",
             DropdownChoice(
                 title=_("SSL certificate verification"),
                 choices=[
                     (True, _("Activate")),
                     (False, _("Deactivate")),
                 ])),
        ],
    ),
    title=_("Check HPE StoreOnce"),
    help=_("This rule set selects the special agent for HPE StoreOnce Applainces "
           "instead of the normal Check_MK agent and allows monitoring via Web API. "),
    match="first",
)

register_rule(
    group,
    "special_agents:salesforce",
    Dictionary(
        elements=[
            ("instances", ListOfStrings(title=_("Instances"), allow_empty=False)),
        ],
        optional_keys=[]),
    title=_("Check Salesforce"),
    help=_("This rule selects the special agent for Salesforce."),
    match="first",
)


def _azure_resource_config():
    return Dictionary(
        orientation="horizontal",
        elements=[
            ('resource', ListOfStrings(
                title=_('Resource names'),
                allow_empty=False,
            )),
            ('metric',
             ListOfStrings(
                 title=_('Metric names'),
                 help=_("Specify a comma separated list of metric "
                        "names. If ommited, all metrics are fetched."),
                 allow_empty=True,
             )),
            #               TextAscii(
            #                    title = _('Metric aggregations'),
            #                    help = _("Specify a comma separated list of metric "
            #                             "aggregations. If ommited, all available "
            #                             "aggregations are fetched."),
            #                    allow_empty = True,
            #               ),
            ('filters',
             TextAscii(
                 title=_('Metric filters'),
                 help=_("Specify a filter that is applied to metric. "
                        "Required for some metrics with dimensions."
                        "If ommited, no filter is applied."),
                 allow_empty=True,
             )),
            ('time_grain',
             DropdownChoice(
                 title=_('Metric time grain'),
                 choices=[('PT1M', _('one minute')), ('PT1H', _('one hour'))],
             )),
        ],
        optional_keys=False,
    )


def _azure_group_config():
    return Dictionary(
        elements=[
            ('group_name', TextAscii(
                title=_('Name of the resource group'),
                allow_empty=False,
            )),
            ('group_config',
             Alternative(
                 title=_("Resources to monitor"),
                 style="dropdown",
                 elements=[
                     ListOf(
                         _azure_resource_config(),
                         title=_("Explicitly specify resources"),
                         allow_empty=False,
                         magic="@-resources-@",
                     ),
                     FixedValue(
                         'fetchall',
                         title=_("Monitor all available resources"),
                         totext="",
                     ),
                 ],
             )),
        ],
        optional_keys=False,
    )


register_rule(
    'datasource_programs',
    "special_agents:azure",
    Dictionary(
        title=_("Agent Azure Configuration"),
        help=_("To monitor Azure resources add this datasource to <b>one</b> host. "
               "The data will be transported using the piggyback mechanism, so make "
               "sure to create one host for every monitored resource group. You can "
               "learn about the discovered groups in the <i>Agent Azure Info</i> "
               "service of the host owning the datasource program."),
        # element names starting with "--" will be passed do cmd line w/o parsing!
        elements=[
            ("--subscription-id", TextAscii(
                title=_("Subscription ID"),
                allow_empty=False,
            )),
            ("--tenant-id", TextAscii(
                title=_("Tenant ID / Directory ID"),
                allow_empty=False,
            )),
            ("--client-id", TextAscii(
                title=_("Client ID / Application ID"),
                allow_empty=False,
            )),
            ("--secret", Password(
                title=_("Secret"),
                allow_empty=False,
            )),
            ("config",
             Dictionary(
                 title=_("Monitoring Settings"),
                 help=_("You can choose to to monitor all resources known to "
                        "the Azure API. However, be aware that Microsoft limits"
                        " API calls to 15,000 per hour (250 per minute)."),
                 elements=[
                     ('explicit-config',
                      ListOf(
                          _azure_group_config(),
                          title=_("Explicitly specify groups"),
                          allow_empty=False,
                          magic="@-groups-@",
                      )),
                     ('fetchall',
                      FixedValue(
                          "fetchall",
                          title=_(
                              "Monitor all available resource groups (overrides previous settings)"
                          ),
                          totext="",
                      )),
                 ],
             )),
            ("--piggyback-vms",
             DropdownChoice(
                 title=_("Create piggyback VM data"),
                 help=_("You can choose to <i>additionally</i> send data concerning VMs to"
                        " the host that is associated with the special agent, to a piggyback"
                        " host with name of the VM itself, or both. By default data is sent"
                        " to the corresponding resource group only."),
                 choices=[
                     ("agenthost", _("Send data to agent host")),
                     ("self", _("Send data to the VM itself")),
                     ("all", _("Send data to both the agent host and the VM itself")),
                 ],
             )),
            ("--sequential",
             Checkbox(
                 title=_("Run in single thread"),
                 help=_("Check this to avoid multiprocessing. "
                        "Recommended for debugging purposes only."),
             )),
        ],
        optional_keys=["--piggyback-vms"],
    ),
    match='first',
)


class MultisiteBiDatasource(object):
    def get_valuespec(self):
        return Dictionary(
            elements=self._get_dynamic_valuespec_elements(),
            optional_keys=["filter", "options", "assignments"],
        )

    def _get_dynamic_valuespec_elements(self):
        return [
            ("site",
             CascadingDropdown(
                 choices=[
                     ("local", _("Connect to the local site")),
                     ("url", _("Connect to site url"),
                      HTTPUrl(
                          help=_("URL of the remote site, for example https://10.3.1.2/testsite"))),
                 ],
                 sorted=False,
                 orientation="horizontal",
                 title=_("Site connection"))),
            ("credentials",
             CascadingDropdown(
                 choices=[("automation", _("Use the credentials of the 'automation' user")),
                          ("configured", _("Use the following credentials"),
                           Tuple(
                               elements=[
                                   TextAscii(title=_("Automation Username"), allow_empty=True),
                                   Password(title=_("Automation Secret"), allow_empty=True)
                               ],))],
                 help=_(
                     "Here you can configured the credentials to be used. Keep in mind that the <tt>automation</tt> user need "
                     "to exist if you choose this option"),
                 title=_("Login credentials"),
                 default_value="automation")),
            ("filter", self._vs_filters()),
            ("assignments", self._vs_aggregation_assignments()),
            ("options", self._vs_options()),
        ]

    def _vs_aggregation_assignments(self):
        return Dictionary(
            title=_("Aggregation assignment"),
            elements=[
                ("querying_host",
                 FixedValue("querying_host", totext="", title=_("Assign to the querying host"))),
                ("affected_hosts",
                 FixedValue("affected_hosts", totext="", title=_("Assign to the affected hosts"))),
                ("regex",
                 ListOf(
                     Tuple(
                         orientation="horizontal",
                         elements=[
                             RegExpUnicode(
                                 title=_("Regular expression"),
                                 help=_("Must contain at least one subgroup <tt>(...)</tt>"),
                                 mingroups=0,
                                 maxgroups=9,
                                 size=30,
                                 allow_empty=False,
                                 mode=RegExp.prefix,
                                 case_sensitive=False,
                             ),
                             TextUnicode(
                                 title=_("Replacement"),
                                 help=
                                 _("Use <tt>\\1</tt>, <tt>\\2</tt> etc. to replace matched subgroups"
                                  ),
                                 size=30,
                                 allow_empty=False,
                             )
                         ],
                     ),
                     title=_("Assign via regular expressions"),
                     help=
                     _("You can add any number of expressions here which are executed succesively until the first match. "
                       "Please specify a regular expression in the first field. This expression should at "
                       "least contain one subexpression exclosed in brackets - for example <tt>vm_(.*)_prod</tt>. "
                       "In the second field you specify the translated aggregation and can refer to the first matched "
                       "group with <tt>\\1</tt>, the second with <tt>\\2</tt> and so on, for example <tt>\\1.example.org</tt>. "
                       ""),
                     add_label=_("Add expression"),
                     movable=False,
                 )),
            ])

    def _vs_filters(self):
        return Dictionary(
            elements=[
                ("aggr_name_regex",
                 ListOf(
                     RegExp(mode=RegExp.prefix, title=_("Pattern")),
                     title=_("By regular expression"),
                     add_label=_("Add new pattern"),
                     movable=False)),
                ("aggr_groups",
                 ListOf(
                     DropdownChoice(choices=bi.aggregation_group_choices),
                     title=_("By aggregation groups"),
                     add_label=_("Add new group"),
                     movable=False)),
            ],
            title=_("Filter aggregations"))

    def _vs_options(self):
        return Dictionary(
            elements=[
                ("state_scheduled_downtime",
                 MonitoringState(title=_("State, if BI aggregate is in scheduled downtime"))),
                ("state_acknowledged",
                 MonitoringState(title=_("State, if BI aggregate is acknowledged"))),
            ],
            optional_keys=["state_scheduled_downtime", "state_acknowledged"],
            title=_("Additional options"),
        )


register_rule(
    "datasource_programs",
    "special_agents:bi",
    ListOf(MultisiteBiDatasource().get_valuespec()),
    title=_("Check state of BI Aggregations"),
    help=_("This rule allows you to check multiple BI aggregations from multiple sites at once. "
           "You can also assign aggregations to specific hosts through the piggyback mechanism."),
    match='first')
