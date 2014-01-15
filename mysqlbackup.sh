#!/bin/bash

TIMESTAMP=`date +%Y-%m-%d-%H:%M:%S`
mkdir -p /root/mysqldumps/
cd /root/mysqldumps
/usr/bin/mysqldump -u root --add-drop-database --all-databases --events > /root/mysqldumps/${TIMESTAMP}.sql && ls -1t /root/mysqldumps | tail -n 1 | xargs rm
/usr/bin/rsync -avu --delete /root/mysqldumps/ root@topanga.massaveunix.com:/root/mysqldumps/ > /dev/null

