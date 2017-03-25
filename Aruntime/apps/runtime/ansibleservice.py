# !/usr/bin/python
# _*_ coding: utf-8 _*_
import json
import os
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.plugins.callback import CallbackBase
# 处理运行日志的插件类
class ResultCallback(CallbackBase):
    def __init__(self, *args):
        super(ResultCallback, self).__init__(*args)
        self.ok = json.dumps({})
        self.fail = json.dumps({})
        self.unreachable = json.dumps({})
        self.playbook = ''
        self.no_hosts = False

    def v2_runner_on_ok(self, result):
        host = result._host.get_name()
        self.runner_on_ok(host, result._result)
        data = json.dumps({host: result._result}, indent=4)
        self.ok = data

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        self.runner_on_failed(host, result._result, ignore_errors)
        data = json.dumps({host: result._result}, indent=4)
        self.fail = data

    def v2_runner_on_unreachable(self, result):
        host = result._host.get_name()
        self.runner_on_unreachable(host, result._result)
        data = json.dumps({host: result._result}, indent=4)
        self.unreachable = data

    def v2_playbook_on_play_start(self, play):
        self.playbook_on_play_start(play.name)
        self.playbook = play.name

    def v2_playbook_on_no_hosts_matched(self):
        self.playbook_on_no_hosts_matched()
        self.no_hosts = True
# 运行playbook接口类
class Ansi_Play2(object):
    def __init__(self, playbook=None, extra_vars={},
                 host_list='',
                 connection='ssh',
                 become=False,
                 become_user=None,
                 module_path=None,
                 fork=50,
                 ansible_cfg=None,  # os.environ["ANSIBLE_CONFIG"] = None
                 passwords=dict(conn_pass="lujingshang"),
                 check=False):
        self.playbook = playbook
        self.extra_vars = extra_vars
        self.passwords = passwords
        self.host_list=host_list
        Options = namedtuple('Options',
                             ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection', 'module_path',
                              'forks', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
                              'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check'])
        self.options = Options(listtags=False, listtasks=False,
                               listhosts=False, syntax=False,
                               connection=connection, module_path=module_path,
                               forks=fork, private_key_file=None,
                               ssh_common_args=None, ssh_extra_args=None,
                               sftp_extra_args=None, scp_extra_args=None,
                               become=become, become_method=None,
                               become_user=become_user,
                               verbosity=None, check=check)
        if ansible_cfg != None:
            os.environ["ANSIBLE_CONFIG"] = ansible_cfg
        self.variable_manager = VariableManager()
        self.loader = DataLoader()
        self.inventory = Inventory(loader=self.loader, variable_manager=self.variable_manager,host_list=self.host_list)
    def set_host(self,host):
        self.host_list=host
    def set_playbook(self,playbook):
        self.playbook=playbook
    # # 运行playbook把日志写入log指定路径文件，playbook inventory在类初始化时指定
    # def run(self, log):
    #     if log:
    #         log_file.append(log)
    #     if not os.path.exists(self.playbook):
    #         code = 1000
    #         results = 'not exists playbook: ' + self.playbook
    #         return code, results, None
    #     pbex = PlaybookExecutor(playbooks=[self.playbook],
    #                             inventory=self.inventory,
    #                             variable_manager=self.variable_manager,
    #                             loader=self.loader,
    #                             options=self.options,
    #                             passwords=self.passwords)
    #     try:
    #         code = pbex.run()
    #     except AnsibleParserError:
    #         code = 1001
    #         result = 'syntax problems in ' + self.playbook
    #         return code, result, None
    #     stats = pbex._tqm._stats
    #     hosts = sorted(stats.processed.keys())
    #     results = [{h: stats.summarize(h)} for h in hosts]
    #     if not results:
    #         code = 1002
    #         result = 'no host executed in ' + self.playbook
    #         return code, results, None
    #     complex = '\n'.join(log_add)
    #     return code, results, complex
    # #使用了插件功能
    # def run_need_data(self):
    #     if not os.path.exists(self.playbook):
    #         code = 1000
    #         complex = {'playbook': self.playbook,
    #                    'msg': self.playbook + ' playbook does not exist', 'flag': False}
    #         simple = 'playbook does not exist about ' + self.playbook
    #         return code, simple, complex
    #     pbex = PlaybookExecutor(playbooks=[self.playbook],
    #                             inventory=self.inventory,
    #                             variable_manager=self.variable_manager,
    #                             loader=self.loader,
    #                             options=self.options,
    #                             passwords=self.passwords)
    #     results_callback = ResultCallback()
    #     pbex._tqm._stdout_callback = results_callback #添加了处理信息的插件实例
    #     try:
    #         code = pbex.run()
    #     except AnsibleParserError:
    #         code = 1001
    #         complex = {'playbook': self.playbook,
    #                    'msg': 'syntax problems in ' + self.playbook, 'flag': False}
    #         simple = 'syntax problems in ' + self.playbook
    #         return code, simple, complex
    #     if results_callback.no_hosts:
    #         code = 1002
    #         complex = 'no hosts matched in ' + self.playbook
    #         simple = {'executed': False, 'flag': False, 'playbook': self.playbook,
    #                   'msg': 'no_hosts'}
    #         return code, simple, complex
    #     else:
    #         ok = json.loads(results_callback.ok)
    #         fail = json.loads(results_callback.fail)
    #         unreachable = json.loads(results_callback.unreachable)
    #         if code != 0:
    #             complex = {'playbook': results_callback.playbook, 'ok': ok,
    #                        'fail': fail, 'unreachable': unreachable, 'flag': False}
    #             simple = {'executed': True, 'flag': False, 'playbook': self.playbook,
    #                       'msg': {'playbook': self.playbook, 'ok_hosts': ok.keys(), 'fail': fail.keys(),
    #                               'unreachable': unreachable.keys()}}
    #             return code, simple, complex
    #         else:
    #             complex = {'playbook': results_callback.playbook, 'ok': ok,
    #                        'fail': fail, 'unreachable': unreachable, 'flag': True}
    #             simple = {'executed': True, 'flag': True, 'playbook': self.playbook,
    #                       'msg': {'playbook': self.playbook, 'ok_hosts': ok.keys(), 'fail': fail.keys(),
    #                               'unreachable': unreachable.keys()}}
    #             return code, simple, complex

# if __name__=="__main__":
#     book2 = Ansi_Play2('/root/test.yml')
#     code, simple, complex = book2.run('/var/log/myansible.log')  # get simple result about playbook, and log detail in log_file
#     print code, simple, complex

