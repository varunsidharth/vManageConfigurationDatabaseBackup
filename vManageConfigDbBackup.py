from getpass import getpass
from pprint import pprint
from netmiko import ConnectHandler
from datetime import datetime
import stdiomask
import json

log = ""

def getHostname(net_connect):
    global log
    command = "show running-config system host-name | display json"
    try:
        output = net_connect.send_command(command)
        print("Successfully extracted hostname!")
    except:
        print("Failed hostname extraction!")
    log = log + "\n" + output
    output = json.loads(output)
    hostname = output['data']['viptela-system:system']['host-name']
    return hostname

def getUniqueId(net_connect):
    global log
    command = "show control local-properties uuid | display json"
    try:
        output = net_connect.send_command(command)
        print("Successfully extracted UUID!")
    except:
        print("Failed UUID extraction!")
    log = log + "\n" + output
    output = json.loads(output)
    uniqueId = output['data']['viptela-security:control']['local-properties']['uuid']
    return uniqueId

def generateConfigDbBackup(net_connect, filePath, filenameWithoutExt):
    global log
    command = "request nms configuration-db backup path " + filePath + filenameWithoutExt
    try:
        output = net_connect.send_command(command)
        print("Successfully created Configuration DB Backup!")
    except:
        print("Configuration DB Backup creation failed")
    log = log + "\n" + output

def vShellLogin(net_connect):
    global log
    command = "vshell"
    try:
        output = net_connect.send_command_timing(command)
        print("Successfully logged into vShell!")
    except:
        print("vShell Login failed!")
    log = log + "\n" + output

def vShellLogout(net_connect):
    global log
    command = "exit"
    try:
        output = net_connect.send_command_timing(command)
        print("Successfully logged out from vShell!")
    except:
        print("vShell Logout failed!")
    log = log + "\n" + output

def scpFile(net_connect, filePath, filename, remoteHost, remoteFilePath, remoteUser, remotePassword):
    command = f"scp {filePath}{filename} {remoteUser}@{remoteHost}:{remoteFilePath}{filename}"
    global log
    try:
        output = net_connect.send_command_timing(command)
        if "Are you sure you want to continue connecting (yes/no)?" in output:
            output += net_connect.send_command_timing("yes")
        if "password:" in output:
            output += net_connect.send_command_timing(remotePassword)
        print("Successfully exported the file!")
    except:
        print("File export failed!")
    log = log + "\n" + output


def deleteBackupFile(net_connect, filePath, filename):
    command = f"rm -rfv {filePath}{filename}"
    global log
    try:
        output = net_connect.send_command(command)
        print("Successfully deleted the file!")
    except:
        print("File deletion failed!")
    log = log + "\n" + output

def main():
    vmanage = {
        "device_type": "linux",
        "ip": input("vManage IP/Hostname: "),
        "username": input("vManage Username: "),
        "password": stdiomask.getpass(prompt='vManage Password: ')
    }
    remoteHost = input("SCP Server IP: ")
    remoteFilePath = input("SCP Server Path: ")
    remoteUser = input("SCP Username: ")
    remotePassword = stdiomask.getpass(prompt='SCP Password: ')

    try:
        net_connect = ConnectHandler(**vmanage)
        login = "Success"
    except:
        login = "Failed"

    if login == "Success":
        print("Login Successful!")
        hostname = getHostname(net_connect)
        uniqueId = getUniqueId(net_connect)

        dateTime = datetime.now().strftime("%Y%m%d%H%M%S")
        filePath = "/opt/data/backup/"
        filenameWithoutExt = hostname + '-' + uniqueId.split("-")[4] + '-backup-' + dateTime
        filename = filenameWithoutExt + ".tar.gz"

        generateConfigDbBackup(net_connect, filePath, filenameWithoutExt)

        vShellLogin(net_connect)
        scpFile(net_connect, filePath, filename, remoteHost, remoteFilePath, remoteUser, remotePassword)
        deleteBackupFile(net_connect, filePath, filename)
        vShellLogout(net_connect)

        net_connect.disconnect()
        file = open(filenameWithoutExt + '-output.log', 'w')
        file.write(log)
        file.close()
    else:
        print("Login Failed!")

if __name__=="__main__":
    main()
