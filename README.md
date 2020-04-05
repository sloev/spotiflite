<img src="https://github.com/sloev/spotiflite/raw/master/assets/logo.png" width="300"/>

# Spotiflite

[![Build Status](https://travis-ci.org/sloev/spotiflite.svg?branch=master)](https://travis-ci.org/sloev/spotiflite) [![Latest Version](https://img.shields.io/pypi/v/spotiflite.svg)](https://pypi.python.org/pypi/spotiflite)

Scrapes Spotify and dumps data to a sqlite3 database.

* Uses `requests` to make queries, with pythonic user-agent
* sleeps randomly between each HTTP call
* is *NOT* in a hurry to get anywhere
* has nice 80's cli interface

## Install

```bash
$ pip install spotiflite
```

then go somewhere and setup a database:

```bash
$ spotiflite setup
```

you can also specify the db filename:

```bash
$ spotiflite --spotifydb=this/awesome/db setup
```

## Usage

For example scrape **Frank ෴ Zappa** 

```bash
$ spotiflite scrape 6ra4GIOgCZQZMOaUECftGN 
got 44 artist ids
extracted data for Tom Waits
saved data for Tom Waits
got 8 artist ids
extracted data for Elmer Snowden
saved data for Elmer Snowden
got 6 artist ids
extracted data for Wesley Willis
saved data for Wesley Willis
...
```

while its running you can get stats in another window

```bash
$ spotiflite stats 
rows: 9882
completed: 1395
jobs to do: 8487
DB size: 48.04 MB
```

### Cli usage

```bash
Usage: spotiflite.py [OPTIONS] COMMAND [ARGS]...

Options:
  -db, --spotifydb TEXT  sqlite filename [default: spotify.db]
  --help                 Show this message and exit.

Commands:
  scrape    starts scraping from given artist id
  setup     creates tables
  stats     print out db stats
  teardown  deletes tables

```