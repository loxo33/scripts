#!/bin/bash
# Find static files in docroot and back them up. Don't backup dynamically created content. 
# Originally used for Drupal 6 webservers. Also good stub code for backing up other single LAMP servers.

DOCROOT=< one or more directories to back up >
BACKUPDIR= < where to back the files up >

/usr/bin/find $DOCROOT regextype posix-awk -iregex ".*\.(css|doc|pdf|txt|jpg|jpeg|tiff|gif|png|php|Z)" -not -iregex '.*/(imagecache|_imagecache|_imagecache2|_imagecache3)/.*' > /tmp/webFiles.list
/bin/tar czPf $BACKUPDIR webfiles-`date +\%F`.tar.gz -T /tmp/webFiles.list
rm /tmp/webFiles.list
exit
