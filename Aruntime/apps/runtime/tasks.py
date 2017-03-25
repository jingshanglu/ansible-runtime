from ansible.utils.display import Display
from ansibleservice import Ansi_Play2
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.errors import  AnsibleParserError
from downutil import down_playbook
from celeryapp import app
import mycallback
import os
from hostutil import generate_host
import shutil
from runtime.setting import appsetting

@app.task(bind=True)
def run(self,playbook,host):
    taskid="ansible-output-"+self.request.id
    host_list=generate_host(host)
    book2 = Ansi_Play2(host_list=host_list)
    url = down_playbook(playbook)
    baseurl=os.path.dirname(os.path.dirname(url))
    book2.set_playbook(url)
    if not os.path.exists(book2.playbook):
        code = 1000
        result = 'not exists playbook: ' + book2.playbook
        return {'code': code, 'result': result, 'complex': None}
    pbex = PlaybookExecutor(playbooks=[book2.playbook],
                            inventory=book2.inventory,
                            variable_manager=book2.variable_manager,
                            loader=book2.loader,
                            options=book2.options,
                            passwords=book2.passwords)
    display=Display()
    results_callback = mycallback.CallbackModule(redispath=appsetting['broker_redis_path'],redisport=appsetting['broker_redis_port'],redisdb=appsetting['broker_redis_db'],taskid=taskid,dis=display)
    pbex._tqm._stdout_callback = results_callback
    try:
        code = pbex.run()
    except AnsibleParserError:
        code = 1001
        result = 'syntax problems in ' + book2.playbook
        shutil.rmtree(baseurl,True)
        return {'code': code, 'result': result}
    stats = pbex._tqm._stats
    hosts = sorted(stats.processed.keys())
    result = [{h: stats.summarize(h)} for h in hosts]
    if not result:
        code = 1002
        result = 'no host executed in ' + book2.playbook
        shutil.rmtree(baseurl,True)
        return {'code': code, 'result': result}
    os.remove(host_list)
    shutil.rmtree(baseurl,True)
    return {'code': code, 'result': result}

