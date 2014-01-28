#!/bin/bash

#####
# reset-slave.sh
#
# this script just sets up what needs to be set up on a slave / read-only hunt server
#
#####

OWNER="www-data"

cd /home/djangoapps/spoilr

#Inserting spoilr logrotate
cp -v spoilr.logrotate /etc/logrotate.d/spoilr

#Inserting spoilr rsyslog
cp -v spoilr.rsyslog /etc/rsyslog.d/10-spoilr.conf

#Copying in apache conf
cp -v spoilr.apacheconf /etc/apache2/conf.d/hunt.conf

/etc/init.d/apache2 restart
/etc/init.d/rsyslog restart



