#!/usr/bin/env python3
""" Walks a tree for files and saves hashes """

import os
import hashlib
import sqlite3
import shutil
from argparse import ArgumentParser


CREATE_TABLE = """
CREATE TABLE file_hash (hash TEXT NOT NULL PRIMARY KEY, path TEXT)
"""

INSERT_HASH = """
INSERT INTO file_hash VALUES (?, ?)
"""

BLOCKSIZE = 65536


class DBConn():
    """ Abstraction for db connection """

    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()
        self.execute = self.cursor.execute
        self.commit = self.conn.commit
        try:
            self.execute(CREATE_TABLE)
        except sqlite3.OperationalError as oerr:
            print("Table creation failed with error: {}".format(oerr))

    def __enter__(self):
        return self

    def __exit__(self, _type, value, traceback):
        self.cursor.close()
        self.conn.close()


def new_hash(db_conn, hashed_file):
    """ Handles output to db or stdout """
    _hash, path = hashed_file
    if db_conn is None:
        print("hash: {} path: {}".format(_hash, path))
    else:
        try:
            db_conn.execute(INSERT_HASH, (str(_hash), str(path)))
            return True
        except sqlite3.IntegrityError as _:
            return False
    return None


def hash_file(filename):
    """ generate hash from file """
    hasher = hashlib.md5()
    with open(filename, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()


def parse_args():
    """ CLI arguments """
    args_p = ArgumentParser(description='Hash images')
    args_p.add_argument('--path', help='Path to file or directory to calculate hash',
                        default=os.getcwd())
    args_p.add_argument('--extension', help='Filename extension',
                        default='jpg')
    args_p.add_argument('--destination', help='Destination root directory',
                        default=None)
    return args_p.parse_args()


def find_files(path, extension):
    """ Walks directory and checks for file with provided extension """
    for root, _, files in os.walk(path):
        for filename in files:
            if filename.startswith('.'):
                continue
            if filename.lower().endswith(extension.lower()):
                full_path = os.path.join(root, filename)
                yield (hash_file(full_path), full_path,)


def build_destination(root_dst, src_path):
    """ takes filename and directory """
    return os.path.join(root_dst, src_path[1:])


def main():
    """ Main function """
    db_conn = None
    args = parse_args()
    # Path to search files
    db_conn = DBConn('.hashed_file.db')
    for hashed_file in find_files(args.path, args.extension):
        if new_hash(db_conn, hashed_file) is True:
            _, fullpath = hashed_file
            # Copy to destination
            dst = build_destination(args.destination, fullpath)
            dst_path, _ = os.path.split(dst)
            if os.path.exists(dst_path) is False:
                os.makedirs(dst_path)
            shutil.copyfile(fullpath, dst)
        db_conn.commit()


if __name__ == '__main__':
    main()
