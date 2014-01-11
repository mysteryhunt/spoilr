#!/bin/bash

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


#Inserting spoilr logrotate
cp -v spoilr.logrotate /etc/logrotate.d/spoilr

#Inserting spoilr rsyslog
cp -v spoilr.rsyslog /etc/rsyslog.d/10-spoilr.conf


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
su -c "$MANAGE republish --traceback" $OWNER

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

