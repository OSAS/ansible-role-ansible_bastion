#
# Copyright (c) 2014-2016 Michael Scherer <mscherer@redhat.com>
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
# List of function split from generate_ansible_command.py
# to be reused by others scripts

import subprocess
import tempfile
import socket
import shutil
import os

from ansible.parsing.dataloader import DataLoader

from ansible.inventory.manager import InventoryManager

from ansible.vars.manager import VariableManager


class VariableManagerWrapper:
    def __init__(self, vm):
        self.vm = vm

    def get_vars(self, loader, host):
        return self.vm.get_vars(host=host)


class InventoryWrapper:
    def __init__(self, host_list):
        self.loader = DataLoader()
        self.im = InventoryManager(loader=self.loader,
                                   sources=[host_list, ])
        self.vm = VariableManager(loader=self.loader, inventory=self.im)

    def get_loader(self):
        return self.loader

    def get_variable_manager(self):
        return VariableManagerWrapper(self.vm)

    def get_groups(self):
        return self.im.groups

    def get_hosts(self, group):
        return self.im.get_hosts(pattern=group)

    def get_host(self, host):
        return self.im.get_host(host)

    def refresh_inventory(self):
        return self.im.refresh_inventory()


def get_changed_files(git_repo, old, new):
    """ Return a list of files who changed in git_repo between
        old and new revision"""
    changed_files = set()
    if old == '0000000000000000000000000000000000000000':
        old = subprocess.check_output(['git',
                                       'rev-list',
                                       '--max-parents=0',
                                       'HEAD'], cwd=git_repo).strip()

    diff = subprocess.check_output(["git", '--no-pager', 'diff',
                                    "--name-status", "--diff-filter=ACDMR",
                                    "%s..%s" % (old, new)], cwd=git_repo)
    for line in diff.decode("utf-8").split('\n'):
        if len(line) > 0:
            splitted = line.split()
            if len(splitted) == 2:
                (t, filename) = splitted
                changed_files.add(filename)
            elif len(splitted) == 3:
                (t, old_filename, new_filename) = splitted
                changed_files.add(old_filename)
                changed_files.add(new_filename)
    return changed_files


def extract_list_hosts_git(revision, path):
    """ Extract the hosts list from git, after deduplciating it
        and resolving variables """
    result = []
    if revision == '0000000000000000000000000000000000000000':
        return result
    try:
        host_content = subprocess.check_output(['git', 'show',
                                                '%s:hosts' % revision],
                                               cwd=path).decode('utf-8')
    # usually, this is done when we can't check the list of hosts
    except subprocess.CalledProcessError:
        return result

    # beware, not portable on windows
    tmp_dir = tempfile.mkdtemp()
    tmp_file = tempfile.NamedTemporaryFile('w+', dir=tmp_dir)
    tmp_file.write(host_content)
    tmp_file.flush()
    os.fsync(tmp_file.fileno())

    inventory = InventoryWrapper(host_list=tmp_file.name)
    variable_manager = inventory.get_variable_manager()
    loader = inventory.get_loader()

    for group in inventory.get_groups():
        for host in inventory.get_hosts(group):
            vars_host = variable_manager.get_vars(loader, host=host)
            result.append(
                {'name': vars_host.get('ansible_ssh_host', host.name),
                 'ssh_args': vars_host.get('ansible_ssh_common_args', ''),
                 'connection': vars_host.get('ansible_connection', 'ssh')})

    # for some reason, there is some kind of global cache that need to be
    # cleaned
    inventory.refresh_inventory()
    # we need to del the temporary file before the directory, or a exception
    # is launched and ignored:
    #   Exception OSError: (2, 'No such file or directory',
    #   '/tmp/tmpw2IQjN/tmppHjNDO') #   in <bound method
    #   _TemporaryFileWrapper.__del__ of <closed file '<fdopen>',
    #   mode 'w+' at 0x2cfd6f0>> ignored
    #
    del tmp_file
    shutil.rmtree(tmp_dir)

    return result


def path_match_local_playbook(playbook_file):
    """ Return True if the playbook can be considered to be
    run locally (ie, if name match the fqdn, or local)"""

    fqdn = socket.getfqdn()
    local_path = ['playbooks/' + i for i in ['local.yml',
                                             fqdn + '.yml',
                                             fqdn.split('.')[0] + '.yml']]
    return playbook_file in local_path
