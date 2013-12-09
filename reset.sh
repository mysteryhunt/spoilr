#!/bin/bash

cd /home/djangoapps/spoilr
MANAGE=../spoilr-env/bin/python\ manage.py

#Backup database just in case
#mv /var/sqlitedb/hunt.db /var/sqlitedb/hunt.db.bak
/usr/bin/mysqldump --events --all-databases > /home/hunt/spoilr.sql

#Wipe mysql db and re-init
cat mysqlinit.sql | /usr/bin/mysql -u root 


# recreate database, this will ask for admin username/password
$MANAGE syncdb --traceback

# until I figure out who apache is running as, let everyone write the hunt db
chmod a+w /var/sqlitedb/hunt.db

# load hunt data
$MANAGE load_data --traceback

# publish team files
$MANAGE republish --traceback
