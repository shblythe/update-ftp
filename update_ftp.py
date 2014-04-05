#!/usr/bin/env python

import os,ftputil
from ftputil import FTPHost
import posixpath
import time
import re

def clear_remote(ftp_host,destination):
    # Cut off excess slashes.
    destination = destination.rstrip("/")

    for current_dir, subdirs, files in ftp_host.walk(source):
	# remove . and ..
	for subdir in subdirs[:]:
	    if subdir in ['.','..']:
		subdirs.remove(subdir)

def mirror_to_remote(ftp_host,local,remote):
    """Upload remote directory found by local to remote."""
    # Cut off excess slashes.
    local = local.rstrip("/")
    remote = remote.rstrip("/")

    print local+" to "+remote
    for current_dir, subdirs, files in os.walk(local):
	if local:
	    current_destination = posixpath.join(remote,
		current_dir[len(local) + 1:])
	else:
	    current_destination = posixpath.join(remote, current_dir)
	# remove . and ..
	for subdir in subdirs[:]:
	    if subdir in ['.','..']:
		subdirs.remove(subdir)
	
	for subdir in subdirs:
	    # ignore ftp exception because if fatal, we'll get them during
	    # upload.
	    try:
		ftp_host.mkdir(posixpath.join(remote,subdir))
	    except ftplib.Error, e:
		pass

	# Upload all files
	pattern=re.compile("\.cgi$")
	for filename in files:
	    print filename
	    local_source_file=os.path.join(local,filename)
	    remote_dest_file=posixpath.join(remote,filename)
	    ftp_host.upload(local_source_file,remote_dest_file)
	    # Make cgi files executable
	    if pattern.search(remote_dest_file):
		ftp_host.chmod(remote_dest_file,0o755)

def mirror_to_local(ftp_host,source,destination):
    """Download remote directory found by source to destination."""
    # Cut off excess slashes.
    source = source.rstrip("/")
    destination = destination.rstrip("/")

    for current_dir, subdirs, files in ftp_host.walk(source):
	# remove . and ..
	for subdir in subdirs[:]:
	    if subdir in ['.','..']:
		subdirs.remove(subdir)

	# current_destination will be the destination directory, plus the
	# current subdirectory. Have to treat the empty string separately,
	# because otherwise we'd be skipping a byte of current_dir,
	# because of the +1, which is there to remove a slash.
	if source:
	    current_destination = os.path.join(destination,
		current_dir[len(source) + 1:])
	else:
	    current_destination = os.path.join(destination, current_dir)
	# Create all subdirectories lest they exist.
	for subdir in subdirs:
	    subdir_full = os.path.join(current_destination, subdir)
	    print subdir_full
	    if not os.path.exists(subdir_full):
		os.mkdir(subdir_full)
	# Download all files in current directory.
	for filename in files:
	    target_file = os.path.join(current_destination, filename)
	    remote_file = posixpath.join(source, current_dir, filename)
	    ftp_host.download(remote_file,target_file)


def update(ftp_host,folders,ftp_root_folder):
    backup_folder='backup'+time.strftime("%Y%m%d%H%M")+'/'
    os.mkdir(backup_folder)
    for folder in folders:
	remote=ftp_root_folder+folder
	local=os.path.join(backup_folder,folder)
	print remote+" to "+local
	if not os.path.exists(local):
	    os.mkdir(local)
	mirror_to_local(ftp_host,remote,local)
	ftp_host.rmtree(remote)
	ftp_host.mkdir(remote)
	mirror_to_remote(ftp_host,folder,remote)
    return backup_folder

