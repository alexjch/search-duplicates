#!/usr/bin/env python3
""" Walks a tree for files and saves hashes """

import os
import hashlib
import sqlite3
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


def output(db_conn, hashed_file):
    """ Handles output to db or stdout """
    _hash, path = hashed_file
    if db_conn is None:
        print("hash: {} path: {}".format(_hash, path))
    else:
        try:
            db_conn.execute(INSERT_HASH, (str(_hash), str(path)))
        except sqlite3.IntegrityError as _:
            print("hash: {} path: {} is a duplicate".format(_hash, path))


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
    args_p.add_argument('--output', help='sqlite file output',
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


def main():
    """ Main function """
    db_conn = None
    args = parse_args()
    # Path to search files
    if os.path.isdir(args.path):
        # Initialize database
        if args.output is not None:
            db_conn = DBConn(args.output)
        for hashed_file in find_files(args.path, args.extension):
            output(db_conn, hashed_file)
        if db_conn is not None:
            db_conn.commit()
    # Hash single file
    else:
        print(hash_file(args.path))


if __name__ == '__main__':
    main()
