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

# This script take a git repository, a git checkout, and 2 commits reference
# and run the appropriate ansible-playbook command
#
# It make a few assumptions on the directory tree:
# - that a file /usr/local/bin/update_galaxy.sh can be run by sudo, and update
#   the role tree. I want to not run it as root so that's required
# - that playbooks are splitted in $CHECKOUT/playbooks, and that the playbook
#   filename to deploy start by "deploy", see get_playbooks_to_run_pattern
# - that you are using a .yml extensions
#
# I keep a separate checkout from the main git repository due to the use of
# a private repository for password and the like
#
# Verbosity setting is still to be be added
# And so does unit tests...


import yaml
from sets import Set
import os
import glob
import subprocess
import re
import fnmatch
import syslog
import sys
import argparse
import shlex

# custom library
sys.path.append('/usr/local/lib')
from bastion_lib import extract_list_hosts_git, get_changed_files, \
    path_match_local_playbook  # noqa: E402

parser = argparse.ArgumentParser(description="Run ansible playbooks based "
                                             "on actual changes in git")
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-n", "--dry-run", help="only show what would be done",
                    action="store_true")
parser.add_argument('--path', help="path of the updated git checkout",
                    default="/etc/ansible")
parser.add_argument('--config', help="path of the config file",
                    default="/etc/ansible_bastion.yml")
parser.add_argument('--git', help="git repository path", required=True)
parser.add_argument('--old', help="git commit before the push", required=True)
parser.add_argument('--new', default="HEAD", help="git commit after the push")

args = parser.parse_args()

if 'SUDO_USER' in os.environ:
    syslog.syslog("Execution by {} with args: {}".format(
        os.environ['SUDO_USER'],
        ' '.join(sys.argv)))
else:
    syslog.syslog("Direct execution with args: {}".format(
        ' '.join(sys.argv)))


def load_config(config_file):
    config = None
    if os.path.isfile(config_file):
        config = yaml.safe_load(open(config_file, 'r'))
    # keep this conditional, since yaml.safe_load return None
    # for a empty file
    if config is None:
        config = {}

    if 'deploy_pattern' not in config:
        config['deploy_pattern'] = 'playbooks/deploy*.yml'
    if 'run_on_new_host' not in config:
        config['run_on_new_host'] = []

    return config


configuration = load_config(args.config)

cache_role_playbook = {}


def parse_roles_playbook(playbook_file):
    if playbook_file in cache_role_playbook:
        return cache_role_playbook[playbook_file]

    playbook = yaml.safe_load(open(playbook_file, 'r'))
    result = {}

    if playbook is None:
        return result

    for doc in playbook:
        host = doc['hosts']
        roles = Set()
        for r in doc.get('roles', []):
            if isinstance(r, str):
                roles.add(r)
            elif isinstance(r, dict):
                roles.add(r['role'])
        result[host] = roles
    cache_role_playbook[playbook_file] = result
    return result


cache_role_meta = {}


def parse_roles_meta(directory):
    roles = {}
    if directory in cache_role_meta:
        return cache_role_meta[directory]
    for r in os.listdir(directory):
        meta_file = "%s/%s/meta/main.yml" % (directory, r)
        if os.path.exists(meta_file):
            meta = yaml.safe_load(open(meta_file, 'r'))
            if meta and 'dependencies' in meta:
                roles[r] = Set()
                if meta['dependencies'] is not None:
                    for dep in meta['dependencies']:
                        roles[r].add(dep['role'])
    cache_role_meta[directory] = roles
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


# return the group
def get_hosts_for_role(role, playbook_file):
    """ Return the list of hosts where a role is applied in a specific
    playbook """
    result = []
    host_roles = get_host_roles_dict(playbook_file)
    for i in host_roles:
        if role in host_roles[i]:
            result.append(i)
    return result


def get_playbooks_to_run(checkout_path):
    # this list compriehension filter from potentially hostile filename
    # since the list is fed to a shell command, I filter to have only safe
    # chars.
    # do not authorize \s in filename, since this interact badly with shell
    # later
    return [g for g in glob.glob('%s/%s' % (checkout_path,
                                 configuration['deploy_pattern']))
            if re.search('^[\\w/.-]+$', g)]


changed_files = get_changed_files(args.git, args.old, args.new)

hosts_to_update = Set()
playbooks_to_run = Set()
local_playbooks_to_run = Set()
limits = Set()

commands_to_run = []
update_requirements = False
for p in get_playbooks_to_run(args.path):
    for path in changed_files:
        splitted_path = path.split('/')
        if path == 'requirements.yml':
            update_requirements = True
        elif splitted_path[0] == 'roles':
            if len(get_hosts_for_role(splitted_path[1], p)) > 0:
                playbooks_to_run.add(p)

for path in changed_files:
    if fnmatch.fnmatch(path, configuration['deploy_pattern']):
        playbooks_to_run.add("%s/%s" % (args.path, path))

    if path_match_local_playbook(path):
        local_playbooks_to_run.add("%s/%s" % (args.path, path))

if 'hosts' in changed_files:
    old = extract_list_hosts_git(args.old, args.git)
    new = extract_list_hosts_git(args.new, args.git)

    def get_hostname(x):
        return x.get('name', '')
    diff = Set(map(get_hostname, new)) - Set(map(get_hostname, old))
    if len(diff) > 0:
        for hostname in diff:
            # No need for a full fledged verification, just making
            # sure there is no funky chars for shell, and no space
            if re.search('^[\\w.-]+$', hostname):
                # avoid using the ssh stuff on salt bus host
                h = filter((lambda f: f['name'] == hostname), new)[0]
                if h['connection'] == 'ssh':
                    commands_to_run.append("ssh %s -o "
                                           "PreferredAuthentications=publickey"
                                           " -o StrictHostKeyChecking=no %s id"
                                           % (h['ssh_args'], hostname))

        for p in get_playbooks_to_run(args.path):
            if os.path.basename(p) in configuration['run_on_new_host']:
                playbooks_to_run.add(p)

if update_requirements:
    commands_to_run.append('sudo /usr/local/bin/update_galaxy.sh')

for p in playbooks_to_run:
    if os.path.exists(p):
        commands_to_run.append('ansible-playbook -D %s' % p)

for p in local_playbooks_to_run:
    commands_to_run.append('sudo /usr/local/bin/ansible_local.py %s' % p)

for c in commands_to_run:
    if args.dry_run:
        print c
    else:
        syslog.syslog("Running {}".format(c))
        subprocess.call(shlex.split(c), cwd=args.path)
