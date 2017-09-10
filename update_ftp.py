#!/usr/bin/env python
# vim: sts=4 et shiftwidth=4:

import os
import posixpath
import time
import re
from stat import *

def mirror_to_remote(ftp_host,local,remote,regex=None):
    """
    Upload remote directory found by local to remote.
    Limited to files which match regex if passed.
    """
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
            ftp_host.mkdir(posixpath.join(remote,os.path.join(subdir)))

    # Upload all files
    cgiPattern=re.compile("\.cgi$")
    cwd=os.getcwd()
    if local:
        os.chdir(local)
    for current_dir, subdirs, files in os.walk('.'):
        if regex:
            filePattern=re.compile(regex)
        for filename in files:
            if (not regex) or filePattern.search(filename):
                filepath=os.path.join(current_dir,filename)
                local_source_file=filepath
                remote_dest_file=posixpath.join(remote,filepath)
                print local_source_file," to ",remote_dest_file
                try:
                    ftp_host.upload(local_source_file,remote_dest_file)
                except AttributeError:
                    ftp_host.put(local_source_file,remote_dest_file)
                # Make cgi files executable
                if cgiPattern.search(remote_dest_file):
                    ftp_host.chmod(remote_dest_file,0o755)
    os.chdir(cwd)

def sftp_walk(sftp_host,remotepath):
    # From https://gist.github.com/johnfink8/2190472
    path=remotepath
    files=[]
    folders=[]
    for f in sftp_host.listdir_attr(remotepath):
        if S_ISDIR(f.st_mode):
            folders.append(f.filename)
        else:
            files.append(f.filename)
    print (path,folders,files)
    yield path,folders,files
    for folder in folders:
        new_path=os.path.join(remotepath,folder)
        for x in self.sftp_walk(new_path):
            yield x
    
def sftp_rmtree(sftp_host,remotepath):
    path=remotepath
    for f in sftp_host.listdir_attr(remotepath):
        new_path=os.path.join(remotepath,f.filename)
        if S_ISDIR(f.st_mode):
            sftp_rmtree(sftp_host,new_path)
        else:
            sftp_host.unlink(new_path)
    sftp_host.rmdir(remotepath)

def mirror_to_local(ftp_host,source,destination,regex=None):
    """
    Download remote directory found by source to destination.
    Limited to files which match regex if passed.
    """
    # Cut off excess slashes.
    source = source.rstrip("/")
    destination = destination.rstrip("/")

    for current_dir, subdirs, files in \
                    (ftp_host.walk(source) if hasattr(ftp_host,"walk") \
                     else sftp_walk(ftp_host,source)):
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
        if regex:
            filePattern=re.compile(regex)
        for filename in files:
            if (not regex) or filePattern.search(filename):
                target_file = os.path.join(current_destination, filename)
                remote_file = posixpath.join(source, current_dir, filename)
                try:
                    ftp_host.download(remote_file,target_file)
                except AttributeError:
                    ftp_host.get(remote_file,target_file)


def update(ftp_host,folders,ftp_root_folder,regex=None):
    if not regex:
        backup_folder='backup'+time.strftime("%Y%m%d%H%M")+'/'
        os.mkdir(backup_folder)
    else:
        backup_folder=None
    for folder in folders:
        remote=ftp_root_folder+folder
        if not regex:
            local=os.path.join(backup_folder,folder)
            print remote+" to "+local
            if not os.path.exists(local):
                os.mkdir(local)
            mirror_to_local(ftp_host,remote,local,regex)
            try:
                ftp_host.rmtree(remote)
            except AttributeError:
                sftp_rmtree(ftp_host,remote)
            ftp_host.mkdir(remote)
        mirror_to_remote(ftp_host,folder,remote,regex)
    return backup_folder

