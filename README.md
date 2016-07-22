Ansible module used by OSAS to manage a set of servers using Ansible.

[![Build Status](https://travis-ci.org/OSAS/ansible-role-ansible_bastion.svg?branch=master)](https://travis-ci.org/OSAS/ansible-role-ansible_bastion)

Architecture
------------

This role permit to install a trusted server that will deploy configurations
and run playbooks safely without having to distribute ssh keys to every admin.
It use for that 2 git repositories where a authorized user can push,
triggering a automated deployment using a script to deploy only where it is
needed ( ie, if you modify a role, only systems where the role is used will be
targeted ).

The role use 2 git repositories, one named "public" and the other named
"private". As the name imply, the public repository is meant to be public and
usually will contain everything that is not deemed private such as passwords. The
private repository is used mostly for passwords, and should usually only
contains groups_vars/ or vars/ repository. A post commit hook will extract
the 2 repositories in /etc/ansible, and run ansible if needed.

For increased security, ansible is run as a non privileged user to reduce
potential attack vectors from the managed system ( see CVE-2014-3498 ).
Others ideas are planned to be implemented.

Variables
---------

A few variables have been added to configure the role, please look at
defaults/main.yml

Pushing to remote repo
----------------------

It is possible to push automatically the public repository to one or more
distant git repository. To do that, please use the "remotes" variable like this:

```
- hosts: bastion.example.org
  roles:
  - role: bastion
    remotes:
    - { name: 'gitlab', url: 'git@gitlab.com:user/repo.git' }
```

You can specify multiple remotes in the list. A separate '_git_pusher' user is created
for that task, and a ssh key is generated for it.

The playbook do not take care of setting the key on the other side, since that's typically
used for various web services such as Github or Bitbucket, and that requires admin credentials.

System users and groups
-----------------------

Several users will be created, depending on the settings used.

* ansible_admin, (variable: `ansible_username`). This user is the
one connecting to remote servers. A separate user is used for that to
properly separate the access and reduce the risk of stealing the ssh keys.

* _git_pusher, (variable `pusher_username`). This user is used to sync the public
repo to a external source.

* git, (variable `git_username`). When using the git-shell based set, this is the
shared user used by commiters to push modifications.

Directory layout
----------------

While everything should be configurable later, for now, the layout of the git
repository need to follow a few set of rules:

 - all roles are in roles/
 - requirement.yml can be safely used to update the roles
 - all playbooks are in playbooks/ and the one to be used for automated deployment
   are named with this pattern: deploy.\*.yml

Using git snapshot of Ansible
-----------------------------

The role can also be used to install ansible right from git, using the HEAD of the
devel branch by default.

To do that, you can use the `use_ansible_git` flag, along `ansible_git_version` if
you want a different branch and/or version of ansible than the default of 'devel'. This
variable is passed to the 'git' ansible module, so it accept everything the module
accept.

Groups based ACL
----------------

In order to ease collaboration and increase security, the repositories can be configured
to be writable by a specific group, with proper sudo configuration that avoid the need to use
root user.

To enable this mode, you need to define the `ansible_admin_group` variable like this:

```
- hosts: bastion.example.org
  roles:
  - role: bastion
    ansible_admin_group: admins
```

The group will be created if it doesn't already exist.

By default, admins can only push and trigger the hooks, but you can also enable them
to run various ansible command with the `allow_ansible_commands` variable. Be aware that
this is equivalent of giving them root access, since they can them do modification outside
of the git repository.

SSH Key type
------------

By default, a RSA key is generated. If you wish to use another type of key, you can pass
the option `ssh_key_type` to use a different type of key.

This however requires a bugfix on ansible for the automated size selection of the key,
sent as a PR on https://github.com/ansible/ansible-modules-core/pull/4074

Management of tor hidden services
---------------------------------

Since ansible is using ssh and ssh can be used with tor hidden services, you can
choose to enable the support for tor hidden services by using the `enable_onion_support`
option like this:

```
- hosts: bastion.example.org
  roles:
  - role: bastion
    enable_onion_support: True
```

It will configure tor and ssh to use tor for accessing a .onion hostname.

It can be used like this in hosts file, to connect to a server whose hidden service
is abcdefabcdef.onion:

```
[all]
server ansible_host=abcdefabcdef.onion

[web]
server
```

Using tor for outgoing connections
----------------------------------

Alternatively, a way to hide the location of the management server is to use tor
for all ssh outgoing connections. This can be done with the option `use_tor_proxy`.

This will install and start a tor client, and direct outgoing ssh connections in
the tor network.

Local deployment
----------------

When you have one single server to deploy, you can also use a alternate mode of operation.

If a playbook named local.yml, or matching the hostname or the fqdn (ie, server.yml or
server.example.org.yml), it will be executed locally with a custom wrapper as root, with
the local connection plugin.

The naming convention of the playbook mimic the one of ansible-pull.
