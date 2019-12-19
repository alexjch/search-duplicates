## Usage

```
duplicates/duplicates.py --path <path to directory or file> --extension <file extension> [--output <path to db file>]

```

```--path```: a path to a directory to execute a recursive search for files. This argument accepts
a path to a file as well.

```--extension```: hash files with provided extension. The default value is ```jpg```.

```--ouput```: a path to a sqlite3 file, if the file already contains a database the search will be
added to the database. If the file does not exists it will be created.
