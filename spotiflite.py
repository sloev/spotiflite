import sqlite3
from contextlib import contextmanager
import re
import os
import time
import random
import json

from bs4 import BeautifulSoup as Soup
import requests
import click
from colorama.ansi import Fore, Back, Style, clear_line, Cursor, clear_screen, set_title


URL_TEMPLATE = "https://open.spotify.com/artist/{}/about"
SPOTIFY_ENTITY_PATTERN = r".*?\Spotify.Entity = (.*);.*"
GREEN = Style.BRIGHT + Fore.GREEN
MAGENTA = Style.BRIGHT + Fore.MAGENTA

SPLASH = (
    "\n\n"
    f"{MAGENTA}███████╗██████╗  ██████╗ ████████╗██╗███████╗{GREEN}██╗     ██╗████████╗███████╗\n"
    f"{MAGENTA}██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝██║██╔════╝{GREEN}██║     ██║╚══██╔══╝██╔════╝\n"
    f"{MAGENTA}███████╗██████╔╝██║   ██║   ██║   ██║█████╗  {GREEN}██║     ██║   ██║   █████╗\n"
    f"{MAGENTA}╚════██║██╔═══╝ ██║   ██║   ██║   ██║██╔══╝  {GREEN}██║     ██║   ██║   ██╔══╝\n"
    f"{MAGENTA}███████║██║     ╚██████╔╝   ██║   ██║██║     {GREEN}███████╗██║   ██║   ███████╗\n"
    f"{MAGENTA}╚══════╝╚═╝      ╚═════╝    ╚═╝   ╚═╝╚═╝     {GREEN}╚══════╝╚═╝   ╚═╝   ╚══════╝\n"
    f"                                                       {MAGENTA}with 🌮 from sloev{GREEN}\n"
)


class singleton:
    sqlite_connection = None


singleton = singleton


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    "--spotifydb",
    "-db",
    type=str,
    default="spotify.db",
    help="sqlite filename [default: spotify.db]",
    envvar="SPOTIFY_DB",
)
def cli(ctx, spotifydb):
    if ctx.invoked_subcommand is None:
        click.echo("\n".join([SPLASH, ctx.get_help(), ""]))
        return
    else:
        ctx.meta["spotifydb"] = spotifydb
        connect(spotifydb)


cli_command = cli.command(
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True)
)


def connect(filename):
    singleton.sqlite_connection = sqlite3.connect(filename)


@contextmanager
def commiting_cursor():
    c = singleton.sqlite_connection.cursor()
    yield c
    singleton.sqlite_connection.commit()


@cli_command
def setup():
    """creates tables"""

    if not click.prompt("Are you sure you wanna create table?", type=bool):
        return

    with commiting_cursor() as cur:
        cur.execute(
            """CREATE TABLE spotify_data
                (referer_id text, id text, data text)"""
        )
        cur.execute(
            """
        create unique index spotify_data_id_index on spotify_data ( id )
        """
        )


@cli_command
def teardown():
    """deletes tables"""

    if not click.prompt("Are you sure you wanna drop tables?", type=bool):
        return

    with commiting_cursor() as cur:
        cur.execute("drop table spotify_data")


@cli_command
@click.argument("artist_id")
def scrape(artist_id):
    """starts scraping from given artist id"""
    visit_id(artist_id)
    while True:
        artist_ids = get_jobs()
        info(f"Got {len(artist_ids)} jobs from db to do")
        if not artist_ids:
            info("No more jobs")
            break
        for artist_id in artist_ids:
            visit_id(artist_id)

    info("exiting")


@cli_command
@click.pass_context
def stats(ctx):
    """print out db stats"""

    byte_size = os.stat(ctx.meta["spotifydb"]).st_size
    human_readable_byte_size = byte_size_to_human_readable(byte_size)

    with commiting_cursor() as cur:

        jobs = cur.execute(
            "select count(*) from spotify_data where length(data) = 0"
        ).fetchone()[0]
        completed_jobs = cur.execute(
            "select count(*) from spotify_data where length(data) != 0"
        ).fetchone()[0]
        info(
            (
                f"rows: {jobs+completed_jobs}\n"
                f"completed: {completed_jobs}\n"
                f"jobs to do: {jobs}\n"
                f"DB size: {human_readable_byte_size}"
            )
        )


def byte_size_to_human_readable(byte_size):
    for count in ["Bytes", "KB", "MB", "GB"]:
        if byte_size > -1024.0 and byte_size < 1024.0:
            return "{:.2f} {}".format(byte_size, count)
        byte_size /= 1024.0
    return "{:.2f} TB".format(byte_size)


def info(message):
    click.echo(GREEN + message + Style.RESET_ALL)


def create_job(referrer_id, id):
    with commiting_cursor() as cur:
        cur.execute(
            """
        INSERT or ignore INTO spotify_data VALUES (?,?,'')""",
            (referrer_id, id),
        )


def complete_job(id, data):
    with commiting_cursor() as cur:
        cur.execute("UPDATE spotify_data SET data=? WHERE id=?", (data, id))


def get_jobs():
    with commiting_cursor() as cur:
        results = cur.execute(
            "SELECT id from spotify_data where LENGTH(data) = 0"
        ).fetchall()
        return [result[0] for result in results]


def visit_id(id):
    info(f"visiting {id}")
    resp = requests.get(URL_TEMPLATE.format(id))
    if resp.status_code != 200:
        raise RuntimeError("spotify gave ", resp.status_code, resp.text)

    text = resp.text

    html = Soup(text, "html.parser")
    artist_ids = {
        a.split("artist/", 1)[1]
        for a in (link["href"] for link in html.find_all("a"))
        if "artist/" in a
    }
    artist_ids = artist_ids - {id}
    info(f"got {len(artist_ids)} artist ids")
    for artist_id in artist_ids:
        create_job(id, artist_id)

    data = re.search(SPOTIFY_ENTITY_PATTERN, text).group(1)
    json_data = json.loads(data)
    artist_name = json_data["name"]
    info(f"extracted data for {artist_name}")

    complete_job(id, data)
    info(f"saved data for {artist_name}\n")

    period = random.randint(1, 5) * 0.5
    time.sleep(period)


if __name__ == "__main__":
    cli()
