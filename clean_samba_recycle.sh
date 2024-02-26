#!/bin/bash

# cleanup recycle dir:
# delete all files with last access time
# older than a specific number of days and
# remove all empty subdirs afterwards.
#
# in your smb.conf:
# make sure you set recycle:touch = yes
# in order to periodically delete old files, you can
# cron the script with something like 00 01 * * * clean_samba_recycle.sh

# set vars
recycle_dir1='/dir1'
recycle_dir2='/dir2'
recycle_dir3='/dir3'
recycle_dir4='/dir4'
recycle_dir5='/dir5'
recycle_dir6='/dir6'
lastaccess_50_maxdays=50
lastaccess_10_maxdays=10
lastaccess_5_maxdays=5

# execute commands for recycle_dir1
find $recycle_dir1 -atime +$lastaccess_10_maxdays -type f -delete
find $recycle_dir1 -type d ! -path $recycle_dir1 -empty -delete

# execute commands for recycle_dir2
find $recycle_dir2 -atime +$lastaccess_50_maxdays -type f -delete
find $recycle_dir2 -type d ! -path $recycle_dir2 -empty -delete

# execute commands for recycle_dir3
find $recycle_dir3 -atime +$lastaccess_50_maxdays -type f -delete
find $recycle_dir3 -type d ! -path $recycle_dir3 -empty -delete

# execute commands for recycle_dir4
find $recycle_dir4 -atime +$lastaccess_5_maxdays -type f -delete
find $recycle_dir4 -type d ! -path $recycle_dir4 -empty -delete

# execute commands for recycle_dir5
find $recycle_dir5 -atime +$lastaccess_10_maxdays -type f -delete
find $recycle_dir5 -type d ! -path $recycle_dir5 -empty -delete

# execute commands for recycle_dir6
find $recycle_dir6 -atime +$lastaccess_10_maxdays -type f -delete
find $recycle_dir6 -type d ! -path $recycle_dir6 -empty -delete
