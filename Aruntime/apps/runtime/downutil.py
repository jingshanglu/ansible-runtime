# -*- coding: utf-8 -*-
import urllib2
import tarfile
import os
from Aruntime.setting import appsetting
# base='/home/playbook/'
def down_playbook(url,base=appsetting['playbook_location']):
    """
        根据URL下载playbook文件到指定文件
        :param url: playbook下载地址
        :param base: 存储playbook文件的目录
        :return: 本地可执行的yml文件路径
    """
    if not os.path.exists(base):
        os.makedirs(base)
    f = urllib2.urlopen(url)
    data = f.read()
    n = url.count("/")
    l=url.split("/", n)
    fileaddress=base+l[n].split("_",l[n].count("_"))[0]+"_files"+"/method/execute.yml"
    with open(base+l[n], "wb") as code:
        code.write(data)
    uncompress_tar_gz(base+l[n],base)
    os.remove(base+l[n])
    return fileaddress
def uncompress_tar_gz(file_name,dest):
    """
    解压tar.gz文件
    :param
        file_name: 文件全路径名称
        dest: 解压缩目的路径
    :return:
    """
    tar = None
    try:
        tar = tarfile.open(file_name)
        names = tar.getnames()
        for name in names:
            tar.extract(name,dest)
    except Exception,e:
        raise Exception("解压缩失败,%s",e)
    finally:
        if tar is not None:
            tar.close()


