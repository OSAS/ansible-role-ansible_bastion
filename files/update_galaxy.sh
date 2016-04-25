#!/bin/bash
[ -w /etc/ansible/roles ] || (echo "Cannot write /etc/ansible/roles, aborting"; exit 1)
cd /etc/ansible
/usr/bin/ansible-galaxy install -f -r /etc/ansible/requirements.yml
