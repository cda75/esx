#!/usr/bin/env python

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
from ConfigParser import SafeConfigParser

import argparse
import atexit
import sys
import ssl



def getArgs(vcConf='esx.conf'):
	parser = argparse.ArgumentParser(description='Process args for powering on a Virtual Machine')
	parser.add_argument('-vm', '--vmname', required=True, nargs='+', help='Names of the Virtual Machines to power on')
	args = parser.parse_args()
	config = SafeConfigParser()
	config.read(vcConf)
	ip = config.get('vcenter', 'ip')
	user = config.get('vcenter', 'user')
	password = config.get('vcenter', 'password')
	if args.vmname:
   		return ip ,user, password, args.vmname
   	else:
   		print("No virtual machine has been specified")
   		sys.exit()


def main():
   	vcIp, vcUser, vcPassword, vmNames = getArgs()
   	try:
   		context = ssl._create_unverified_context()
   		si = SmartConnect(host=vcIp, user=vcUser, pwd=vcPassword, sslContext=context)
   		if not si:
   			print("Cannot connect to specified host using specified username and password")
   			sys.exit()

		atexit.register(Disconnect, si)
		content = si.content
		objView = content.viewManager.CreateContainerView(content.rootFolder,[vim.VirtualMachine],True)
		vmList = objView.view
		objView.Destroy()

		for vm in vmList:
			if vm.name in vmNames:
				vm.PowerOff()
				print("Virtual Machine(s) have been Powered Off successfully")

	except vmodl.MethodFault as e:
		print("Caught vmodl fault : " + e.msg)
	except Exception as e:
		print("Caught Exception : " + str(e))



if __name__ == "__main__":
   main()
