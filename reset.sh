#!/bin/bash

OWNER="www-data"

cd /home/djangoapps/spoilr

MANAGE=python\ manage.py

#Backup database just in case
#mv /var/sqlitedb/hunt.db /var/sqlitedb/hunt.db.bak
/usr/bin/mysqldump --events --all-databases > /home/hunt/spoilr.sql

#Wipe mysql db and re-init
cat mysqlinit.sql | /usr/bin/mysql -u root 

# recreate database, this will ask for admin username/password
su -c "$MANAGE syncdb --traceback" $OWNER

chown www-data /var/sqlitedb/hunt.db

# load hunt data
su -c "$MANAGE load_data --traceback" $OWNER

# publish team files
su -c "$MANAGE republish --traceback" $OWNER
