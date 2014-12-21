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
