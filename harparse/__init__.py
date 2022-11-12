""" HAR file parser """

import json
from json import JSONDecodeError
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
from  urllib.parse import urlparse

import click

def loadfile(fileobject: str) -> Optional[Dict[str, Any]]:
    """ loads a given filename into a dict """
    file_reader = Path(fileobject).expanduser().resolve()
    try:
        data = json.load(file_reader.open("r", encoding="utf-8"))
    except JSONDecodeError as jsonerror:
        print(f"Failed to load file: {jsonerror}")
        return None
    if "log" not in data:
        print("No log? Quitting")
        sys.exit(1)
    res: Optional[Dict[str, Any]]  = data.get("log")
    return res



def prompt_user_input(prompt_text: str) -> bool:
    """ prompts for user input"""
    # prompt for user input
    prompt = ""
    while prompt.strip().lower() not in ("y", "n",):
        prompt = input(prompt_text)
    if prompt.strip().lower() == "n":
        return False
    return True


def get_extract_directory(filename_object: str) -> Path:
    """ makes up the extraction directory """
    if "/" in filename_object:
        harfile_name = filename_object.split("/")[-1]
    return Path(f"~/Downloads/{harfile_name}/").expanduser().resolve()

def create_extract_directory(filename: str) -> bool:
    """ creates the file extraction directory in '~/Downloads/"""
    directory_name = get_extract_directory(filename)
    print(f"Extraction directory: {directory_name}")

    if directory_name.exists():
        if not directory_name.is_dir():
            raise ValueError()
        return True
    os.mkdir(directory_name)
    return os.path.exists(directory_name)

def get_filedata_filename(filedata: Dict[str, Any]) -> str:
    """ gets the filename from the filedata, typically just the last bit of the URL """
    url = filedata.get("request", {}).get("url", False)
    if not url:
        raise ValueError("Failed to pull url from filedata")
    parsed = urlparse(url)
    if not parsed.path:
        raise ValueError(f"Couldn't get a filename from {url}")
    path = str(parsed.path)
    return path.rsplit("/", maxsplit=1)[-1]
