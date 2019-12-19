#!/usr/bin/env python3

import os
import imagehash
import sqlite3
from argparse import ArgumentParser
from PIL import Image


CREATE_TABLE = """
CREATE TABLE file_hash (hash TEXT NOT NULL PRIMARY KEY, path TEXT)
"""

INSERT_HASH = """
INSERT INTO file_hash VALUES (?, ?)
"""


class DBConn(object):

    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()
        self.execute = self.cursor.execute
        self.commit = self.conn.commit
        try:
            self.execute(CREATE_TABLE)
        except sqlite3.OperationalError as oe:
            print("Table creation failed with error: {}".format(oe))

    def __enter__(self):
        return self

    def __exit__(self):
        self.cursor.close()
        self.conn.close()


def output(db, hashed_file):
    _hash, path = hashed_file
    if db is None:
        print("hash: {} path: {}".format(_hash, path))
    else:
        try:
            db.execute(INSERT_HASH, (str(_hash), str(path)))
        except sqlite3.IntegrityError as ie:
            print("hash: {} path: {} is a duplicate".format(_hash, path))


def hash_file(filename):
    return imagehash.average_hash(Image.open(filename))


def parse_args():
    ap = ArgumentParser(description='Hash images')
    ap.add_argument('--path', help='Path to file or directory to calculate hash',
                    default=os.getcwd())
    ap.add_argument('--extension', help='Filename extension',
                    default='jpg')
    ap.add_argument('--output', help='sqlite file output',
                    default=None)
    return ap.parse_args()


def find_files(path, extension):
    for root, dirs, files in os.walk(path):
        for filename in files:
            if filename.lower().endswith(extension.lower()):
                full_path = os.path.join(root, filename)
                yield (hash_file(full_path), full_path,)


def main():
    db = None
    args = parse_args()
    # Path to search files
    if os.path.isdir(args.path):
        # Initialize database
        if args.output is not None:
            db = DBConn(args.output)
        for hashed_file in find_files(args.path, args.extension):
            output(db, hashed_file)
        if db is not None:
            db.commit()
    # Hash single file
    else:
        hash_file(args.path)


if __name__ == '__main__':
    main()
