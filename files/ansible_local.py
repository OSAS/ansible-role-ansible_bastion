#!/usr/bin/python
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

import sys
import socket
import subprocess

if len(sys.argv) != 2:
    print("Error, not enough arguments")
    sys.exit(1)

path = sys.argv[1]
fqdn = socket.getfqdn()
authorized_path = ['local.yml', fqdn + '.yml', fqdn.split('.')[0] + '.yml']
authorized_path = ['/etc/ansible/playbooks/' + i for i in authorized_path]

if path not in authorized_path:
    print("Unauthorized path %s" % path)
    sys.exit(1)

subprocess.call('ansible-playbook', '-c', 'local', '-D', path)
