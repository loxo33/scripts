#!/bin/bash
# This script performs an xtrabackup (byte-level backup) then a mysqldump (logical backup) on a mysql server. 
# Requires rsa key to rsync from server to target. Alternatively rsync TO server, obviating the key. 

TMPDIR=/var/tmp/backups
BACKUPFILE=xtradb_daily_$(date +%F).tar.gz
USERNAME= <mysql user; usually root.>
PASSWORD= <mysql password>
DATABASES= "<array of databases (as a string)>"
TARGETSERVER= <server storing backups>
TARGETSERVER= <where backups are stored>

# xtrabackup
/usr/bin/innobackupex --user=root --password=$ROOTPASS $TMPDIR/raw --no-timestamp
/usr/bin/innobackupex --defaults-file=/etc/mysql/my.cnf --apply-log --user=root --password=$ROOTPASS $TMPDIR/raw
/usr/bin/logger "xtrabackup of completed at `date +%H:%M:%S`"
# mysql dump
mysqldump --defaults-extra-file=/root/.my.cnf --routines --triggers --single-transaction --databases $DATABASES > $TMPDIR/xtradb_sqldump_`date +\%F-%H`.sql
mysqldump --defaults-extra-file=/root/.my.cnf $DATABASE > $TMPDIR/$DATABASE_sqldump_`date +\%F-%H`.sql
/usr/bin/logger "MySQLdump of $DATABASE completed at `date +%H:%M:%S`"
/bin/tar czfP /tmp/$BACKUPFILE $TMPDIR/*
/usr/bin/logger "tarball of backups completed at `date +%H:%M:%S`"
/usr/bin/rsync -az -e "ssh -i /home/backups/.ssh/backups.rsa" /tmp/$BACKUPFILE backups@$TARGETSERVER:$TARGETDIR
/usr/bin/logger "Rsync of tarball to Backups Server completed at `date +%H:%M:%S`"
/bin/rm -f /tmp/$BACKUPFILE
/bin/rm -rf $TMPDIR/*
exit
