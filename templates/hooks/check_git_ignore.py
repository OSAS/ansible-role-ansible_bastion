#!/usr/bin/python
#
# {{ ansible_managed }}
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
# This script verify that all modules in requirements.yml are also
# in the .gitignore file
# It doesn't handle branch, and will only verify the last commit of a whole
# series of patch, mostly because that's a minor issue (and because that's
# easier to code
#

import yaml
import sys
import subprocess

last_ref = '0'
for line in sys.stdin.readlines():
    last_ref = line.split(' ')[1]

req = subprocess.check_output(['git', 'show', last_ref + ':requirements.yml'])
doc = yaml.load(req)
module_names = set([i['name'] for i in doc])

gitignore = subprocess.check_output(['git', 'show', last_ref + ':.gitignore'])
ignored_dirs = set([l.replace('roles/', '') for l in gitignore.split('\n')
                    if l.startswith("roles/")])

diff = module_names.difference(ignored_dirs)
if len(diff) > 0:
    print "error, there is modules in requirements.yml " \
          "who are not in .gitignore"
    print "please copy this:"
    for d in diff:
        print "roles/" + d
    sys.exit(1)
