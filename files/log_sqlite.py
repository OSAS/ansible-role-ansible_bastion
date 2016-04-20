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
# This callback plugin log each run in a sqlite database, with the date of
# play, the file used, and the result (number of failure/success)

from ansible.plugins.callback import CallbackBase
import datetime
import sqlite3
import time
import os

DEFAULT_DB_NAME = '~/playbook_runs_log.db'


class CallbackModule(CallbackBase):
    CALLBACK_NAME = 'log_sqlite'
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.init_db()
        self._stats = {}
        self._stats['ok'] = 0
        self._stats['failed'] = 0
        self._stats['changed'] = 0
        # there is a slight difference between the 2 of the order
        # of a the microsecond
        # but that's just convenience for displaying
        self._stats['date'] = time.time()
        self._stats['date_human'] = datetime.datetime.now().strftime("%c")
        self._stats['playbook_file'] = 'foo'

    def init_db(self):
        self._db_file = os.path.expanduser(
            os.environ.get('DB_FILE', DEFAULT_DB_NAME))

        if not os.path.isfile(self._db_file):
            conn = sqlite3.connect(self._db_file)
            c = conn.cursor()
            c.execute(''' CREATE TABLE runs
                (ok INT,
                failed INT,
                changed INT,
                date REAL,
                date_human TEXT,
                playbook_file TEXT)
            ''')
            conn.commit()
            conn.close()

    def v2_playbook_on_stats(self, stats):
        conn = sqlite3.connect(self._db_file)
        c = conn.cursor()
        c.execute('''INSERT INTO runs VALUES (?,?,?,?,?,?)''',
                  (self._stats['ok'], self._stats['failed'],
                    self._stats['changed'],
                    self._stats['date'], self._stats['date_human'],
                    self._stats['playbook_file']))
        conn.commit()
        conn.close()

    def v2_runner_item_on_ok(self, result):
        self._stats['ok'] += 1
        if result._result.get('changed', False):
            self._stats['changed'] += 1

    def v2_runner_item_on_failed(self, result):
        self._stats['failed'] += 1

    # beware, the variable must be named 'playbook', due to some
    # hack in ansible for backward compat
    def v2_playbook_on_start(self, playbook):
        self._stats['playbook_file'] = playbook._file_name
