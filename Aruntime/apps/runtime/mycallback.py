from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase
from ansible.utils.color import colorize, hostcolor
import sys
import errno

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.utils.color import stringc
from ansible.module_utils._text import to_bytes, to_text
import redis
from ansible.utils.display import logger
import re
class CallbackModule(CallbackBase):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'mycallback'

    def __init__(self,redispath=None,redisport=None,redisdb=None,taskid=None,dis=None):

        self._play = None
        self._last_task_banner = None
        super(CallbackModule, self).__init__()
        self.r=redis.Redis(host=redispath,port=redisport,db=redisdb)
        self.task_id=taskid
        self.dis=dis
    def save_to_redis(self,msg):
        self.r.append(self.task_id, msg)

    def display(self, msg, color=None, stderr=False, screen_only=False, log_only=False):
        """ Display a message to the user

        Note: msg *must* be a unicode string to prevent UnicodeError tracebacks.
        """

        # FIXME: this needs to be implemented
        # msg = utils.sanitize_output(msg)
        nocolor = msg
        if color:
            msg = stringc(msg, color)

        if not log_only:
            if not msg.endswith(u'\n'):
                msg2 = msg + u'\n'
            else:
                msg2 = msg

            msg2 = to_bytes(msg2, encoding=self.dis._output_encoding(stderr=stderr))
            if sys.version_info >= (3,):
                # Convert back to text string on python3
                # We first convert to a byte string so that we get rid of
                # characters that are invalid in the user's locale
                msg2 = to_text(msg2, self.dis._output_encoding(stderr=stderr), errors='replace')

            if not stderr:
                fileobj = sys.stdout
            else:
                fileobj = sys.stderr

            fileobj.write(msg2)

            try:
                fileobj.flush()
            except IOError as e:
                # Ignore EPIPE in case fileobj has been prematurely closed, eg.
                # when piping to "head -n1"
                if e.errno != errno.EPIPE:
                    raise

        if logger and not screen_only:
            msg2 = nocolor.lstrip(u'\n')

            msg2 = to_bytes(msg2)
            if sys.version_info >= (3,):
                # Convert back to text string on python3
                # We first convert to a byte string so that we get rid of
                # characters that are invalid in the user's locale
                msg2 = to_text(msg2, self.dis._output_encoding(stderr=stderr))

            if color == C.COLOR_ERROR:
                logger.error(msg2)
            else:
                logger.info(msg2)
        if not msg2.endswith(u'\n'):
            msg2 = msg2 + u'\n'
        else:
            pass
        if msg2.find('before assignment') == -1:
            ansi_escape = re.compile(r'\x1b[^m]*m')
            msg3 = ansi_escape.sub('', msg2)
        else:
            msg3 = ''
        self.save_to_redis(msg3)
    def banner(self, msg, color=None):
        '''
        Prints a header-looking line with stars taking up to 80 columns
        of width (3 columns, minimum)
        '''
        if self.dis.b_cowsay:
            try:
                self.dis.banner_cowsay(msg)
                return
            except OSError:
                self.dis.warning("somebody cleverly deleted cowsay or something during the PB run.  heh.")

        msg = msg.strip()
        star_len = (79 - len(msg))
        if star_len < 0:
            star_len = 3
        stars = u"*" * star_len
        self.display(u"\n%s %s" % (msg, stars), color=color)

    def v2_runner_on_failed(self, result, ignore_errors=False):

        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if 'exception' in result._result:
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result._result['exception'].strip().split('\n')[-1]
                msg = "An exception occurred during task execution. To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = "An exception occurred during task execution. The full traceback is:\n" + result._result['exception']
            # self._display.display(msg, color=C.COLOR_ERROR)
            self.display(msg, color=C.COLOR_ERROR)

        if result._task.loop and 'results' in result._result:
            self._process_items(result)

        else:
            if delegated_vars:
                # self._display.display("fatal: [%s -> %s]: FAILED! => %s" % (result._host.get_name(), delegated_vars['ansible_host'], self._dump_results(result._result)), color=C.COLOR_ERROR)
                self.display("fatal: [%s -> %s]: FAILED! => %s" % (result._host.get_name(), delegated_vars['ansible_host'], self._dump_results(result._result)), color=C.COLOR_ERROR)
            else:
                # self._display.display("fatal: [%s]: FAILED! => %s" % (result._host.get_name(), self._dump_results(result._result)), color=C.COLOR_ERROR)
                self.display("fatal: [%s]: FAILED! => %s" % (result._host.get_name(), self._dump_results(result._result)), color=C.COLOR_ERROR)

        if ignore_errors:
            # self._display.display("...ignoring", color=C.COLOR_SKIP)
            self.display("...ignoring", color=C.COLOR_SKIP)

    def v2_runner_on_ok(self, result):

        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        self._clean_results(result._result, result._task.action)

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        self._clean_results(result._result, result._task.action)
        if result._task.action in ('include', 'include_role'):
            return
        elif result._result.get('changed', False):
            if delegated_vars:
                msg = "changed: [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
            else:
                msg = "changed: [%s]" % result._host.get_name()
            color = C.COLOR_CHANGED
        else:
            if delegated_vars:
                msg = "ok: [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
            else:
                msg = "ok: [%s]" % result._host.get_name()
            color = C.COLOR_OK

        if result._task.loop and 'results' in result._result:
            self._process_items(result)
        else:

            if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and not '_ansible_verbose_override' in result._result:
                msg += " => %s" % (self._dump_results(result._result),)
            # self._display.display(msg, color=color)
            self.display(msg, color=color)

        self._handle_warnings(result._result)

    def v2_runner_on_skipped(self, result):
        if C.DISPLAY_SKIPPED_HOSTS:
            if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
                self._print_task_banner(result._task)

            if result._task.loop and 'results' in result._result:
                self._process_items(result)
            else:
                msg = "skipping: [%s]" % result._host.get_name()
                if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and not '_ansible_verbose_override' in result._result:
                    msg += " => %s" % self._dump_results(result._result)
                # self._display.display(msg, color=C.COLOR_SKIP)
                self.display(msg, color=C.COLOR_SKIP)

    def v2_runner_on_unreachable(self, result):
        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if delegated_vars:
            # self._display.display("fatal: [%s -> %s]: UNREACHABLE! => %s" % (result._host.get_name(), delegated_vars['ansible_host'], self._dump_results(result._result)), color=C.COLOR_UNREACHABLE)
            self.display("fatal: [%s -> %s]: UNREACHABLE! => %s" % (result._host.get_name(), delegated_vars['ansible_host'], self._dump_results(result._result)), color=C.COLOR_UNREACHABLE)
        else:
            # self._display.display("fatal: [%s]: UNREACHABLE! => %s" % (result._host.get_name(), self._dump_results(result._result)), color=C.COLOR_UNREACHABLE)
            self.display("fatal: [%s]: UNREACHABLE! => %s" % (result._host.get_name(), self._dump_results(result._result)), color=C.COLOR_UNREACHABLE)

    def v2_playbook_on_no_hosts_matched(self):
        # self._display.display("skipping: no hosts matched", color=C.COLOR_SKIP)
        self.display("skipping: no hosts matched", color=C.COLOR_SKIP)

    def v2_playbook_on_no_hosts_remaining(self):
        # self._display.banner("NO MORE HOSTS LEFT")
        self.banner("NO MORE HOSTS LEFT")

    def v2_playbook_on_task_start(self, task, is_conditional):

        if self._play.strategy != 'free':
            self._print_task_banner(task)

    def _print_task_banner(self, task):
        # args can be specified as no_log in several places: in the task or in
        # the argument spec.  We can check whether the task is no_log but the
        # argument spec can't be because that is only run on the target
        # machine and we haven't run it thereyet at this time.
        #
        # So we give people a config option to affect display of the args so
        # that they can secure this if they feel that their stdout is insecure
        # (shoulder surfing, logging stdout straight to a file, etc).
        args = ''
        if not task.no_log and C.DISPLAY_ARGS_TO_STDOUT:
            args = u', '.join(u'%s=%s' % a for a in task.args.items())
            args = u' %s' % args

        # self._display.banner(u"TASK [%s%s]" % (task.get_name().strip(), args))
        # self._display.banner(u"TASK [%s%s]" % (task.get_name().strip(), args))
        self.banner(u"TASK [%s%s]" % (task.get_name().strip(), args))
        if self._display.verbosity >= 2:
            path = task.get_path()
            if path:
                # self._display.display(u"task path: %s" % path, color=C.COLOR_DEBUG)
                self.display(u"task path: %s" % path, color=C.COLOR_DEBUG)

        self._last_task_banner = task._uuid

    def v2_playbook_on_cleanup_task_start(self, task):
        # self._display.banner("CLEANUP TASK [%s]" % task.get_name().strip())
        self.banner("CLEANUP TASK [%s]" % task.get_name().strip())

    def v2_playbook_on_handler_task_start(self, task):
        # self._display.banner("RUNNING HANDLER [%s]" % task.get_name().strip())
        self.banner("RUNNING HANDLER [%s]" % task.get_name().strip())

    def v2_playbook_on_play_start(self, play):
        name = play.get_name().strip()
        if not name:
            msg = u"PLAY"
        else:
            msg = u"PLAY [%s]" % name

        self._play = play

        # self._display.banner(msg)
        self.banner(msg)

    def v2_on_file_diff(self, result):
        if result._task.loop and 'results' in result._result:
            for res in result._result['results']:
                if 'diff' in res and res['diff'] and res.get('changed', False):
                    diff = self._get_diff(res['diff'])
                    if diff:
                        # self._display.display(diff)
                        self.display(diff)
        elif 'diff' in result._result and result._result['diff'] and result._result.get('changed', False):
            diff = self._get_diff(result._result['diff'])
            if diff:
                # self._display.display(diff)
                self.display(diff)

    def v2_runner_item_on_ok(self, result):
        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if result._task.action in ('include', 'include_role'):
            return
        elif result._result.get('changed', False):
            msg = 'changed'
            color = C.COLOR_CHANGED
        else:
            msg = 'ok'
            color = C.COLOR_OK

        if delegated_vars:
            msg += ": [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
        else:
            msg += ": [%s]" % result._host.get_name()

        msg += " => (item=%s)" % (self._get_item(result._result),)

        if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and not '_ansible_verbose_override' in result._result:
            msg += " => %s" % self._dump_results(result._result)
        # self._display.display(msg, color=color)
        self.display(msg, color=color)

    def v2_runner_item_on_failed(self, result):
        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if 'exception' in result._result:
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result._result['exception'].strip().split('\n')[-1]
                msg = "An exception occurred during task execution. To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = "An exception occurred during task execution. The full traceback is:\n" + result._result['exception']

            # self._display.display(msg, color=C.COLOR_ERROR)
            self.display(msg, color=C.COLOR_ERROR)

        msg = "failed: "
        if delegated_vars:
            msg += "[%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
        else:
            msg += "[%s]" % (result._host.get_name())

        # self._display.display(msg + " (item=%s) => %s" % (self._get_item(result._result), self._dump_results(result._result)), color=C.COLOR_ERROR)
        self.display(msg + " (item=%s) => %s" % (self._get_item(result._result), self._dump_results(result._result)), color=C.COLOR_ERROR)
        self._handle_warnings(result._result)

    def v2_runner_item_on_skipped(self, result):
        if C.DISPLAY_SKIPPED_HOSTS:
            msg = "skipping: [%s] => (item=%s) " % (result._host.get_name(), self._get_item(result._result))
            if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and not '_ansible_verbose_override' in result._result:
                msg += " => %s" % self._dump_results(result._result)
            # self._display.display(msg, color=C.COLOR_SKIP)
            self.display(msg, color=C.COLOR_SKIP)

    def v2_playbook_on_include(self, included_file):
        msg = 'included: %s for %s' % (included_file._filename, ", ".join([h.name for h in included_file._hosts]))
        # self._display.display(msg, color=C.COLOR_SKIP)
        self.display(msg, color=C.COLOR_SKIP)

    def v2_playbook_on_stats(self, stats):
        # self._display.banner("PLAY RECAP")
        self.banner("PLAY RECAP")

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)

            # self._display.display(u"%s : %s %s %s %s" % (
            self.display(u"%s : %s %s %s %s" % (
                hostcolor(h, t),
                colorize(u'ok', t['ok'], C.COLOR_OK),
                colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                colorize(u'failed', t['failures'], C.COLOR_ERROR)),
                screen_only=True
            )

            # self._display.display(u"%s : %s %s %s %s" % (
            self.display(u"%s : %s %s %s %s" % (
                hostcolor(h, t, False),
                colorize(u'ok', t['ok'], None),
                colorize(u'changed', t['changed'], None),
                colorize(u'unreachable', t['unreachable'], None),
                colorize(u'failed', t['failures'], None)),
                log_only=True
            )

        self.display("", screen_only=True)
        # self._display.display("", screen_only=True)

    def v2_playbook_on_start(self, playbook):
        if self._display.verbosity > 1:
            from os.path import basename
            # self._display.banner("PLAYBOOK: %s" % basename(playbook._file_name))
            self.banner("PLAYBOOK: %s" % basename(playbook._file_name))

        if self._display.verbosity > 3:
            if self._options is not None:
                for option in dir(self._options):
                    if option.startswith('_') or option in ['read_file', 'ensure_value', 'read_module']:
                        continue
                    val =  getattr(self._options,option)
                    if val:
                        self._display.vvvv('%s: %s' % (option,val))

    def v2_runner_retry(self, result):
        msg = "FAILED - RETRYING: %s (%d retries left)." % (result._task, result._result['retries'] - result._result['attempts'])
        if (self._display.verbosity > 2 or '_ansible_verbose_always' in result._result) and not '_ansible_verbose_override' in result._result:
            msg += "Result was: %s" % self._dump_results(result._result)
        # self._display.display(msg, color=C.COLOR_DEBUG)
        self.display(msg, color=C.COLOR_DEBUG)
