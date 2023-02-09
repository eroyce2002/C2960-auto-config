from netmiko import ConnectHandler,redispatch #imports netmiko for device connection
import sys
import time
import re
#import logging #for logging netmiko errors
#logging.basicConfig(filename= "/var/log/netmiko/" + str(time.time()) + "ansibleprep.log", level=logging.DEBUG) #debugging netmiko errors
#logger = logging.getLogger("netmiko") #debugging netmiko errors

output = []

user = sys.argv[1] #collects username from user
password = sys.argv[2] #collects password from user
port = sys.argv[3] #collects port from user
hostname = sys.argv[4]

siteSearch = r'^\w+'
site = re.search(siteSearch, hostname).group()

networkConnection = {
    "device_type": "terminal_server",
    "host" : "uwstout.edu",
    "username": "",
    "password": "",
    "port": 22,
}

#IPs that will be assigned to each port
IPAssignment = {
}

if networkConnection["host"] == "uwstout.edu":
    IP = "ip addr " + IPAssignment[port] + " 255.255.255.0"

if networkConnection["host"] == "uwstout.edu":
    gateway = "10.36.1.1"

networkConnection["username"] = user #puts user gathered into networkConnection dictionary
networkConnection["password"] = password #puts password gathered from getpass into networkConnection dictionary
networkConnection["port"] = port #puts port gathered from user into networkConnection dictionary
networkConnection["secret"] = password

net_connect = ConnectHandler(**networkConnection) #connects to the device specified

net_connect.write_channel("\r")
time.sleep(1)
net_connect.write_channel("\r")
time.sleep(1)
output = net_connect.read_channel()

print(output)

net_connect.write_channel("no\r")
net_connect.write_channel("\r")
time.sleep(1)
net_connect.write_channel("\r")

redispatch(net_connect, device_type="cisco_ios") #switches Netmiko from terminal server mode to Cisco ios mode

output = net_connect.read_channel()
print(output)

net_connect.enable() #enters Priv Exec mode
time.sleep(1) #Adding delay to prevent Cisco stroking out

output = net_connect.send_config_set("no logging console", read_timeout=5) #This is needed to stop netmiko from failing because console logs make it think the commands don't go through
print(output)
time.sleep(1)

show_version = net_connect.send_command("show version | i cisco") #does show version command to grab model
print(show_version)
time.sleep(1)

#use show version to figure out what model device it is and decide which port is the management port

if "C2960" in show_version:
    dhcpCommands = [
        "int fa0/1",
        "no shut",
        IP,
        "end",
    ]

else:
    print('No device detected, exitting.')
    quit()

#minimum config added so that ansible can SSH to device
commands = [
    "hostname " + hostname,
    "ip domain name " + site + "uwstout.edu",
    "ip default-gateway " + gateway,
    "user " + user + " algorithm-type scrypt secret " + password,
    "enable password 0 " + password,
    "ip ssh version 2",
    "line vty 0 15",
    "login local",
    "transport input ssh",
    "exit",
]

keyCommands = [
    "crypto key gen rsa modulus 2048",
]

#inputs commands to device for Ansible prep

output = net_connect.send_config_set(dhcpCommands)
print(output)
time.sleep(1)

output = net_connect.send_config_set(commands, read_timeout=20)
print(output)
time.sleep(1)

while True:
    try:
        output = net_connect.send_config_set(keyCommands, read_timeout=20)
        print(output)
        time.sleep(1)
        break
    except:
        print('Crypto key generation failed, trying again...')

print("done")
