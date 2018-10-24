#!/usr/bin/python
#
# Copyright (c) 2017 Michael Scherer <mscherer@redhat.com>
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
import re
import subprocess

if len(sys.argv) != 2:
    print "Usage: %s hostname" % sys.argv[0]
    print "Remove the hostname from .ssh/known_hosts"
    sys.exit(1)

target = sys.argv[1]

# use a minimal verification on the argument, since we already verify
# with ssh-keygen after.
if not re.match('^[\\w.]+$', target):
    print "Invalid hostname %s" % target
    sys.exit(1)

if subprocess.call(['ssh-keygen', '-F', target]) != 0:
    print "Nothing to clean for %s" % target
    sys.exit(0)

if subprocess.call(['ssh-keygen', '-R', target]) != 0:
    print "Error when cleaning %s" % target
    sys.exit(1)

print "SSH public key got cleaned for %s" % target
