#!/bin/bash
generate_ansible_command.py --old HEAD~1 --new HEAD --git "{{ git_repositories_dir }}/public/"
