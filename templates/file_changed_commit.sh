#!/bin/bash
#
# {{ ansible_managed }}
#
# Copyright (c) 2014 Michael Scherer <mscherer@redhat.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 

refname="$1"
oldrev="$2"
newrev="$3"

SCRIPT=$(mktemp /tmp/ansible_commit-XXXXXX)

echo "#!/bin/bash"  >> $SCRIPT
echo "cd /etc/ansible" >> $SCRIPT

generate_ansible_command.py $( git diff --name-status --diff-filter=ACDMR ${oldrev}..${newrev} | awk '{print $2}') >> $SCRIPT
echo "rm -f $SCRIPT" >> $SCRIPT
chown {{ ansible_username }} $SCRIPT
chmod +rx $SCRIPT

su - {{ ansible_username }} -c "$SCRIPT"
