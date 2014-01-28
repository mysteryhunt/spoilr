#!/bin/bash

######
# reset-failover.sh
#
# this script will re-initialize and republish all hunt team info and team directories
# but will preserve the database
# use this if you're failing over to a new server with an existing hunt database 
# or if you otherwise just want to rebuild the system-side of the config but not destroy hunt
######

OWNER="www-data"

cd /home/djangoapps/spoilr

MANAGE=python\ manage.py

if (( "$UID" != "0" )); then
	echo YOU NEED TO BE ROOT TO RUN THIS SCRIPT!
	echo go away.
	echo
	exit 255
fi

echo "This script recreates the /var/www/spoilr docroot and prepares for a republish_all in case we are failing over to a slave.  You want to run this on a slave after corey is shut down and DNS has been failed over. Press ENTER to continue."
read WAIT

umount -f /var/www/spoilr
umount -f /home/hunt/htpasswd
umount -f /var/cache/spoilr


echo "Creating /var/www/spoilr docroot..."
mkdir -pv /var/www/spoilr
chown www-data /var/www/spoilr
chmod 755 /var/www/spoilr

echo "Creating /var/www/spoilr symlinks into /home/hunt..."
ln -s /home/hunt/spoilrdocroot/hq /var/www/spoilr/hq
ln -s /home/hunt/spoilrdocroot/logout /var/www/spoilr/logout
ln -s /home/hunt/spoilrdocroot/static /var/www/spoilr/static
chown -R www-data /var/www/spoilr/hq
chown -R www-data /var/www/spoilr/logout
chown -R www-data /var/www/spoilr/static
chmod -R 755 /var/www/spoilr/hq
chmod -R 755 /var/www/spoilr/logout
chmod -R 755 /var/www/spoilr/static

echo "Creating /var/www/spoilr/teams and /var/www/spoilr/users"
mkdir -p /var/www/spoilr/teams
mkdir -p /var/www/spoilr/users
chown www-data.www-data /var/www/spoilr/teams
chown www-data.www-data /var/www/spoilr/users
chmod 755 /var/www/spoilr/teams
chmod 755 /var/www/spoilr/users

echo "Creating other symlinks in /var/www/spoilr"
ln -s /usr/lib/python2.7/dist-packages/django/contrib/admin/static/admin /var/www/spoilr/admin
ln -s /usr/share/php-htmlpurifier /var/www/spoilr/htmlpurifier

echo "Inserting /var/www/spoilr/.htaccess"
cp -v /home/hunt/spoilrdocroot/.htaccess /var/www/spoilr/.htaccess

#Inserting spoilr logrotate
cp -v spoilr.logrotate /etc/logrotate.d/spoilr

#Inserting spoilr rsyslog
cp -v spoilr.rsyslog /etc/rsyslog.d/10-spoilr.conf

#Copying in apache conf
cp -v spoilr.apacheconf /etc/apache2/conf.d/hunt.conf

echo "Creating Django Cache Directory..."
mkdir -p /var/cache/spoilr
chown -R $OWNER /var/cache/spoilr

#Backup database just in case
echo "Backing old spoilr mysql database into /home/hunt/spoilr.sql..."
/usr/bin/mysqldump --events --all-databases > /home/hunt/spoilr.sql

# publish team files
echo "Publishing hunt for teams..."
su -c "$MANAGE republish_all --traceback" $OWNER

# Install cron jobs
echo "Installing Cron Jobs..."
cp -v spoilrcron /etc/cron.d/spoilrcron

#Inserting spoilr logrotate
cp -v spoilr.logrotate /etc/logrotate.d/spoilr

#Inserting spoilr rsyslog
cp -v spoilr.rsyslog /etc/rsyslog.d/10-spoilr.conf

/etc/init.d/apache2 restart
/etc/init.d/rsyslog restart

echo "backup database is stored at /home/hunt/spoilr.sql"

