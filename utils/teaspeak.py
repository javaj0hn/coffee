# -*- coding: utf-8 -*-
from telnetlib import *
import json

from core.conf import config

def get_talk_power(clients):
    return clients.get('client_talk_power')

def getRanks():
    with Telnet(config['TEAMSPEAK_URL'], 10011) as tn:
        tn.write(config['TEAMSPEAK_LOGIN'].encode('ascii') + b"\n")
        tn.read_until(b"error id=0 msg=ok")
        tn.write("servergrouplist".encode('ascii') + b"\n")
        tn.write(b"exit\n")
        servergroups = tn.read_all()
    return str(servergroups.decode('utf-8').replace("\s", "")) 

def getServerInfo():
    with Telnet(config['TEAMSPEAK_URL'], 10011) as tn:
        tn.write(config['TEAMSPEAK_LOGIN'].encode('ascii') + b"\n")
        tn.read_until(b"error id=0 msg=ok")
        tn.write("serverinfo".encode('ascii') + b"\n")
        tn.write(b"exit\n")
        serverinfo = tn.read_all()
        serverinfo = serverinfo.decode('utf-8').replace("\s", "")
        serverInfoList = serverinfo.split(" ")

        serverI = {"clients_connected": serverInfoList[6].replace("virtualserver_clientsonline=", "")}
    return serverI 

def getChannels():
    with Telnet(config['TEAMSPEAK_URL'], 10011) as tn:
        tn.write(config['TEAMSPEAK_LOGIN'].encode('ascii') + b"\n")
        tn.read_until(b"error id=0 msg=ok")
        tn.write("channellist".encode('ascii') + b"\n")
        tn.write(b"exit\n")
        channels = tn.read_all()
    return str(channels.decode('utf-8').replace("\s", ""))

def getClients():
    with Telnet(config['TEAMSPEAK_URL'], 10011) as tn:
        tn.write(config['TEAMSPEAK_LOGIN'].encode('ascii') + b"\n")
        tn.read_until(b"error id=0 msg=ok")
        tn.write("clientlist".encode('ascii') + b"\n")
        tn.write(b"exit\n")
        clients = tn.read_all()    
    return str(clients.decode('utf-8').replace("\s", ""))

def detailClient(clid):
    with Telnet(config['TEAMSPEAK_URL'], 10011) as tn:
        tn.write(config['TEAMSPEAK_LOGIN'].encode('ascii') + b"\n")
        tn.read_until(b"error id=0 msg=ok")
        lazyCode = "clientinfo clid="+clid
        tn.write(lazyCode.encode('ascii') + b"\n")
        tn.write(b"exit\n")
        clientsInfo = tn.read_all()
    return str(clientsInfo.decode('utf-8').replace("\s", ""))

def tsPic():
    clients = getClients()
    channels = getChannels()
    groups = getRanks()

    # channel & client string to list
    channelList = channels.split("|")
    clientList = clients.split("|")
    groupList = groups.split("|")
    
    # sort groups
    group = {}
    grpList = []

    for g in groupList:
        gClean = g.split(" ")
        group['id'] = gClean[0].replace("sgid=", "")
        group['name'] = gClean[2].replace("name=", "")
        grpList.append(group.copy())


    chan = {}
    chanList = []
    for c in channelList:
        cClean = c.split(" ")
        chan['cid'] = cClean[1].replace("cid=", "")
        chan['pid'] = cClean[2].replace("pid=", "")
        chan['channel_name'] = cClean[3].replace("channel_name=", "")
        chan['channel_order'] = cClean[4].replace("channel_order=", "")
        chan['total_clients'] = cClean[5].replace("total_clients=", "")

        user = {}
        userList = []
        for u in clientList:
            uClean = u.split(" ")
            if (uClean[1].replace("cid=", "") == chan['cid']):
                user['clid'] = uClean[0].replace("clid=", "")
                user['cid'] = uClean[1].replace("cid=", "")
                user['client_database_id'] = uClean[2].replace("client_database_id=", "")
                user['client_nickname'] = uClean[3].replace("client_nickname=", "")
                user['client_type'] = uClean[4].replace("client_type=", "")
                extraData = detailClient(user['clid'])
                extraData = extraData.split(" ")
                if extraData:
                    if (len(extraData) < 70):
                        break
                    user['client_version'] = extraData[2].replace("client_version=", "")
                    user['client_platform'] = extraData[3].replace("client_platform=", "")
                    user['client_input_muted'] = extraData[4].replace("client_input_muted=", "")
                    user['client_output_muted'] = extraData[5].replace("client_output_muted=", "")
                    user['client_outputonly_muted'] = extraData[6].replace("client_outputonly_muted=", "")
                    user['client_is_recording'] = extraData[10].replace("client_is_recording=", "")
                    user['client_talk_power'] = extraData[24].replace("client_talk_power=", "")
                    user['client_country'] = extraData[41].replace("client_country=", "")

                    # get user groups
                    allGroups = extraData[15].replace("client_servergroups=", "")
                    allGroupsClean = allGroups.split(",")
                    memGroupLst = []
                    for allG in allGroupsClean:
                        # look up code
                        for value in grpList:
                            if (value['id'] == allG):
                                # append value to our list
                                memGroupLst.append(value['name'])

                    user['member_groups'] = memGroupLst
                
                userList.append(user.copy())


        # order userList by talk power?
        userList.sort(key=get_talk_power, reverse=True)

        chan['clients'] = userList
        chanList.append(chan.copy())

    return chanList