#!/bin/bash

OWNER="www-data"

cd /home/djangoapps/spoilr

MANAGE=python\ manage.py

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


