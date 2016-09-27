#!/usr/bin/env python

from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect
import atexit
import ssl
from ConfigParser import SafeConfigParser


def getvCenter(vcConf='esx.conf'):
    vc = {}
    config = SafeConfigParser()
    config.read(vcConf)
    vc['vCenterIp'] = config.get('vcenter', 'ip')
    vc['vCenterUser'] = config.get('vcenter', 'user')
    vc['vCenterPassword'] = config.get('vcenter', 'password')
    return vc


def get_esx_host(vc, esx_host_ip):
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.verify_mode = ssl.CERT_NONE
    si = SmartConnect(host=vc['vCenterIp'], user=vc['vCenterUser'], pwd=vc[
                      'vCenterPassword'], port=443, sslContext=context)
    if not si:
        print(
            "Could not connect to the specified host using specified username and password")
        return -1
    atexit.register(Disconnect, si)
    content = si.RetrieveContent()
    return content.searchIndex.FindByIp(ip=esx_host_ip, vmSearch=False)


def create_port_group(esx_host_id, SwitchName, vlan_id):
    host_network_system = esx_host_id.configManager.networkSystem
    port_group_spec = vim.host.PortGroup.Specification()
    pg_name = 'VLAN_' + str(vlan_id)
    host_ip = host_network_system.networkInfo.vnic[0].spec.ip.ipAddress
    port_group_spec.name = pg_name
    port_group_spec.vlanId = vlan_id
    port_group_spec.vswitchName = SwitchName
    security_policy = vim.host.NetworkPolicy.SecurityPolicy()
    security_policy.allowPromiscuous = True
    security_policy.forgedTransmits = True
    security_policy.macChanges = False
    port_group_spec.policy = vim.host.NetworkPolicy(security=security_policy)
    try:
        host_network_system.AddPortGroup(portgrp=port_group_spec)
        print "Successfully created PortGroup %s on host %s" % (pg_name, host_ip)
    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg


def delete_port_group(esx_host_id, pg_name):
    host_network_system = esx_host_id.configManager.networkSystem
    host_ip = host_network_system.networkInfo.vnic[0].spec.ip.ipAddress
    try:
        host_network_system.RemovePortGroup(pgName=pg_name)
        print "Successfully removed PortGroup %s on host %s" % (pg_name, host_ip)
    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg


def start_sshd(host):
    serviceManager = host.configManager.serviceSystem
    print ('Starting sshd service on ')
    serviceManager.StartService(id='TSM-SSH')


def enter_maint(host):
    host_ip = host.configManager.networkSystem.networkInfo.vnic[
        0].spec.ip.ipAddress
    try:
        host.EnterMaintenanceMode(0)
        print 'Enter maintenance mode for host %s .....' % host_ip
    except:
        print 'Some failure during enter maintanence mode'


def exit_maint(host):
    host_ip = host.configManager.networkSystem.networkInfo.vnic[
        0].spec.ip.ipAddress
    try:
        host.ExitMaintenanceMode(0)
        print 'Exit maintenance mode for host %s .....' % host_ip
    except:
        print 'Some failure!'


def set_dns(EsxHostId, DNS_Ip):
    host_network_system = EsxHostId.configManager.networkSystem
    host_ip = host_network_system.networkInfo.vnic[0].spec.ip.ipAddress
    dns_spec = host_network_system.dnsConfig
    dns_spec.address.append(str(DNS_Ip))
    try:
        host_network_system.UpdateDnsConfig(dns_spec)
        print "Successfully added DNS Server %s on host %s" % (DNS_Ip, host_ip)
    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg


def set_gateway(EsxHostId, Gw_Ip):
    host_network_system = EsxHostId.configManager.networkSystem
    host_ip = host_network_system.networkInfo.vnic[0].spec.ip.ipAddress
    route_spec = host_network_system.ipRouteConfig
    route_spec.defaultGateway = str(Gw_Ip)
    try:
        host_network_system.UpdateIpRouteConfig(route_spec)
        print "Successfully added Gateway %s on host %s" % (str(Gw_Ip), host_ip)
    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg


def read_host_ip(EsxHosts='esx.hosts'):
    with open('esx.hosts') as f:
        EsxHostsIp = [x.strip('\n') for x in f.readlines() if x.strip() != '']
    return EsxHostsIp


def main():
    with open('esx.hosts') as f:
        esx_hosts = [x.strip('\n') for x in f.readlines() if x.strip() != '']

    vCenter = getvCenter('esx.conf')
    host_ip = raw_input('Enter esx host ip to put into Maintanance Mode: ')
    EsxHostId = get_esx_host(vCenter, host_ip)


if __name__ == '__main__':
    main()
