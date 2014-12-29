#!/usr/bin/python
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

import yaml
from sets import Set
import os
import sys

playbook_file = "/etc/ansible/playbooks/deploy.yml"


def parse_roles_playbook(playbook_file):

    playbook = yaml.load(open(playbook_file, 'r'))
    result = {}

    for doc in playbook:
        host = doc['hosts']
        roles = Set()
        for r in doc['roles']:
            if isinstance(r, str):
                roles.add(r)
            elif isinstance(r, dict):
                roles.add(r['role'])
        result[host] = roles
    return result


def parse_roles_meta(directory):
    roles = {}
    for r in os.listdir(directory):
        meta_file = "%s/%s/meta/main.yml" % (directory, r)
        if os.path.exists(meta_file):
            meta = yaml.load(open(meta_file, 'r'))
            if meta and 'dependencies' in meta:
                roles[r] = Set()
                for dep in meta['dependencies']:
                    roles[r].add(dep['role'])
    return roles


def get_roles_deps(roles, r):
    result = [r]
    if r not in roles:
        return result
    for i in roles[r]:
        result.append(i)
        if i in roles:
            result.extend(get_roles_deps(roles, i))
    return result


def get_host_roles_dict(playbook_file, roles_path='/etc/ansible/roles'):
    result = {}
    roles = parse_roles_meta(roles_path)
    hosts = parse_roles_playbook(playbook_file)

    for host in hosts:
        result[host] = Set()
        for r in hosts[host]:
            for r2 in get_roles_deps(roles, r):
                result[host].add(r2)
    return result


def get_hosts_for_role(role):
    result = []
    host_roles = get_host_roles_dict(playbook_file)
    for i in host_roles:
        if role in host_roles[i]:
            result.append(i)
    return result


hosts_to_update = Set()
apply_all = False
update_requirements = False
for path in sys.argv[1:]:
    splitted_path = path.split('/')
    if path == playbook_file:
        apply_all = True
    elif path == 'requirements.yml':
        update_requirements = True
    elif splitted_path[0] == 'roles':
        for i in get_hosts_for_role(splitted_path[1]):
            hosts_to_update.add(i)

if update_requirements:
    print 'sudo /usr/local/bin/update_galaxy.sh'
if not apply_all:
    for h in hosts_to_update:
        print 'ansible-playbook -l %s %s' % (h, playbook_file)
else:
    print 'ansible-playbook %s' % playbook_file
