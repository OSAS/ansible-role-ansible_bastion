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

* ansible_admin, (variable: ansible_username). This user is the
one connecting to remote servers. A separate user is used for that to
properly separate the access and reduce the risk of stealing the ssh keys.

* _git_pusher, (variable pusher_username). This user is used to sync the public
repo to a external source.

* git, (variable git_username). When using the git-shell based set, this is the
shared user used by commiters to push modifications.

Directory layout
----------------

While everything should be configurable later, for now, the layout of the git
repository need to follow a few set of rules:

 - all roles are in roles/
 - requirement.yml can be safely used to update the roles
 - all playbooks are in playbooks/ and the one to be used for automated deployment
   are named with this pattern: deploy.\*.yml
