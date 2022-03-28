#!/usr/bin/env python3

""" extracts files from .har archives """


from base64 import b64decode
import binascii

# import os
import json

import sys
from typing import Optional
from pathlib import Path


import click

from . import loadfile, prompt_user_input, get_extract_directory, get_filedata_filename, create_extract_directory

@click.group()
def cli():
    """ CLI interface """


@cli.command()
@click.option(
    "--match-method", "-m",
    type=str,
    multiple=True,
    help="Match the given method, eg GET/PUT/POST (can have multiples)",
    )
@click.argument("filename")
def list_urls(
    filename: str,
    match_method: tuple,
    ) -> None:
    """ Lists the URLS in the HAR file."""

    methods = [ method.lower() for method in match_method ]

    file_contents = loadfile(filename)
    if file_contents is None:
        print("Failed to load file")
        return

    if "entries" not in file_contents:
        print("No entries in file, bailing")
        return

    for entry in file_contents["entries"]:
        method = entry.get('request',{}).get("method")
        url = entry.get('request',{}).get('url')
        if not methods:
            print(f"[{method:8}]\t {url}")
        elif methods and method.lower() in methods:
            print(f"[{method:8}]\t {url}")



@cli.command()
@click.option("--noninteractive", "-n", is_flag=True, default=False)
@click.option("--filter", '-f', "filterstr", multiple=True)

@click.option(
    "--match-method", "-m",
    type=str,
    multiple=True,
    help="Match the given method, eg GET/PUT/POST (can have multiples)",
    )
@click.option("--output-dir", "-o", type=click.Path(exists=False))
@click.argument("filename")
# pylint: disable=too-many-branches,too-many-locals,too-many-statements
def extract(
    filename: str,
    filterstr: tuple,
    noninteractive: bool,
    output_dir: Optional[Path],
    match_method: tuple,
    ) -> None:
    """ does the file extraction bit """

    methods = [ method.lower() for method in match_method ]

    file_matches = []
    file_contents = loadfile(filename)
    if file_contents is None:
        return
    if "entries" not in file_contents:
        return
    for entry in file_contents["entries"]:
        url = entry.get('request',{}).get("url")
        method = entry.get('request',{}).get("method").lower()
        if not filterstr and not methods:
            # if we're just yeeting everything into the matches
            file_matches.append(entry)
            print(f"Adding {url}", file=sys.stderr)
            continue

        if methods and method not in methods:
            continue
        matches = False
        if filterstr:
            for filematch in filterstr:
                if filematch in url:
                    print(f"Found match for {filematch} in {url}", file=sys.stderr)
                    matches = True
        else:
            print(f"Adding {url}", file=sys.stderr)
            matches = True
        if matches:
            file_matches.append(entry)

    if not file_matches:
        print("Failed to find any files, quitting.", file=sys.stderr)
        sys.exit()

    if not noninteractive and not prompt_user_input(f"Found {len(file_matches)} matching files, continue? (y/n) "):
        print("Ok, quitting", file=sys.stderr)
        sys.exit()

    if output_dir is not None:

        output_dir_path = Path(output_dir)
        if not output_dir_path.exists():
            output_dir_path.mkdir()
        elif not output_dir_path.is_dir():
            print(f"You asked to output files to '{output_dir_path}' but it exists and is not a directory, quitting.")
            sys.exit(1)

    elif not create_extract_directory(filename):
        print("Failed to create extraction directory, quitting.")
        sys.exit(1)
    else:
        output_dir_path = get_extract_directory(filename)

    for file in file_matches:
        if file.get("response", {}).get("content", {}).get("text"):
            if file.get("response", {}).get("content", {}).get("encoding") == "base64":
                output_filename = Path(f"{output_dir_path}/{get_filedata_filename(file)}")
                if output_filename.exists():
                    print(f"Skipping {output_filename}, already exists!")
                    continue
                print(f"Saving to {output_filename}", file=sys.stderr)
                with output_filename.open('wb') as output_filehandle:
                    try:
                        file_content = b64decode(
                            file.get("response", {}).get("content", {}).get("text"),
                            validate=True,
                            )
                        print(f"Content length: {len(file_content)}")
                        output_filehandle.write(file_content)
                    except binascii.Error as error_message:
                        print(f"Failed to parse content, got encoding error: {error_message}", file=sys.stderr)
                        sys.exit(1)

            elif file.get("response", {}).get("content", {}).get("encoding"):
                encoding = file.get("response", {}).get("content", {}).get("encoding")
                raise NotImplementedError(f"Encoding is {encoding}, need to handle it")
            else:
                print("Not sure how you got here... ?", file=sys.stderr)
                print(json.dumps(file, indent=4, default=str))
                sys.exit(1)



if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
