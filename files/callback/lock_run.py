#
# Copyright (c) 2016 Michael Scherer <mscherer@redhat.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# This callback plugin just ensure that only 1 single instance of ansible is
# running # at a time by default. Since multiple people can push to the same
# repo, I do not want to have issues with multiple concurent runs
#

from ansible.plugins.callback import CallbackBase
import os
import sys
import atexit


class CallbackModule(CallbackBase):
    CALLBACK_NAME = 'lock'

    def __init__(self):
        super(CallbackModule, self).__init__()

    def v2_playbook_on_start(self, playbook):
        lock_file = os.path.expanduser('{}/ansible_run_lock'.format(
            os.environ.get('XDG_RUNTIME_DIR', '~')))
        if os.path.exists(lock_file):
            # TODO verify if the PID in the file still exist
            self._display.display("Deployment already started, exiting")
            self._display.display("Remove {} if you want to proceed".format(
                lock_file))
            sys.exit(2)

        # TODO try/except, show a better error message
        fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()))
        os.close(fd)
        atexit.register(os.unlink, lock_file)
