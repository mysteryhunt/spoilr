#!/bin/bash

####
#reset.sh
#
#This script totally wipes and re-creates the hunt database and all team directories
#It then republishes them all
#
#DO NOT RUN THIS UNLESS YOU WANT TO DESTROY/RESTART THE HUNT or are in dev/testing mode
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


echo ""
echo "This script COMPLETELY DESTROYS MYSTERY HUNT.  It will erase the database and reload and restart all teams from scratch.  DO NOT DO THIS AT ALL IF HUNT HAS STARTED!!"
echo "Also, this script probably ONLY WORKS ON THE MASTER SERVER -- if you're not on corey, you want to run the slave-reset.sh script"
echo "If you are absolutely sure you want to potentially ruin mystery hunt and are on the master server, type KILLMYSTERYHUNT (otherwise enter anything else)"

read KILLMYSTERYHUNT

if [ "$KILLMYSTERYHUNT" != "KILLMYSTERYHUNT" ]; then
	echo RESET SEQUENCE ABORTED. HAVE A NICE DAY
	exit 255
fi

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

#Wipe mysql db and re-init
echo "Wiping old spoilr mysql database and recreating empty one..." 
cat mysqlinit.sql | /usr/bin/mysql -u root 

# recreate database, this will ask for admin username/password
echo "Asking django to load schema into the spoilr mysql database..."
su -c "$MANAGE syncdb --traceback" $OWNER

# load hunt data
echo "Loading hunt data from /home/hunt into the spoilr mysql database..."
su -c "$MANAGE load_data --traceback" $OWNER

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

echo "In case you didn't mean to do this, backup database is stored at /home/hunt/spoilr.sql"

