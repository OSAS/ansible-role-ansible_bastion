#!/bin/bash
cd /etc/ansible
/usr/bin/ansible-galaxy install -f -r /etc/ansible/requirements.yml
