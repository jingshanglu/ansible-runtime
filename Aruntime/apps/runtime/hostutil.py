# !/usr/bin/env python
# -*- coding: utf-8 -*-
from ConfigParser import DEFAULTSECT,RawConfigParser
import datetime
import json
#import logging
#logger = logging.getLogger("travelsky.apps.Aruntime.hostutil")
class KconfigParser(RawConfigParser):
    def write(self,fp):
        if self._defaults:
            fp.write("[%s]/n" % DEFAULTSECT)
            for (key,value) in self._defaults.items():
                fp.write("%s  %s" %(key,str(value).replace('\n','\n\t')))
                fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" %section)
            for (key,value) in self._sections[section].items():
                if key !="__name__":
                    fp.write("%s %s\n" %(key,str(value).replace('\n','\n\t')))
            fp.write("\n")
#生成host文件的类
class Generate_ansible_hosts(object):
    def __init__(self,host_file):
        self.config=KconfigParser(allow_no_value=True)
        self.host_file=host_file
    def create_all_servers(self,items):
        for i in items:
            group=i['group']
            self.config.add_section(group)
            for j in i['items']:
                name=j['hostname']
                ssh_port=j['ansible_ssh_port']
                ssh_host=j['ansible_ssh_host']
                ssh_user=j['ansible_ssh_user']
                ssh_pass=j['ansible_ssh_pass']
                build="ansible_ssh_port={0} ansible_ssh_host={1} ansible_ssh_user={2} ansible_ssh_pass={3}" \
                    .format(ssh_port,ssh_host,ssh_user,ssh_pass)
                self.config.set(group,name,build)
        with open(self.host_file,'wb') as configfile:
            self.config.write(configfile)
        return True
def generate_host(jsondata,fileaddress='/tmp/'):
    now = datetime.datetime.now()
    fileaddress=fileaddress+now.strftime('%Y-%m-%d%H-%M-%S')
    generate_host = Generate_ansible_hosts(fileaddress)
    #jsondata=json.loads(jsondata)
    generate_host.create_all_servers(jsondata)
    return fileaddress

if __name__=="__main__":
    data='[{"group":"demo","items":[{"host_name": "test1","ansible_ssh_host": "172.27.44.99","ansible_ssh_port": "22","ansible_ssh_user": "root","ansible_ssh_pass": "lujingshang"}]}]'
    # data=json.loads(data)
    print data
    # # data={'webservers': {'hosts': ['172.27.44.99']}}
    # generate_host=Generate_ansible_hosts('D:/ahost')
    # generate_host.create_all_servers(data)
    result=generate_host(data,'D:/')
    print result
