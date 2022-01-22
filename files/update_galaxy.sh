#!/bin/bash
REQ_PATH=/etc/ansible/requirements.yml
ROLES_PATH=/etc/ansible/roles
INSTALL_ARGS="install -f -r $REQ_PATH"
INSTALL_ROLES_ARGS="$INSTALL_ARGS -p $ROLES_PATH"

[ -w $ROLES_PATH ] || (echo "Cannot write $ROLES_PATH, aborting"; exit 1)
cd /etc/ansible
NEW=0
if grep -q 'roles:' $REQ_PATH; then
	/usr/bin/ansible-galaxy role $INSTALL_ROLES_ARGS
	NEW=1
fi;

if grep -q 'collections:' $REQ_PATH; then
	/usr/bin/ansible-galaxy collection $INSTALL_ARGS
	NEW=1
fi;

if [ $NEW -ne 1 ]; then
	/usr/bin/ansible-galaxy $INSTALL_ROLES_ARGS >/dev/null
fi;
