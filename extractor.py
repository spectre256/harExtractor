#!/usr/bin/env python3

from base64 import decodebytes
from json import load
from mimetypes import guess_extension
import os
import sys
from urllib.parse import urlparse, unquote


def fileNameFromURL(url):
    return unquote(os.path.basename(urlparse(url).path))


def truncateFileName(fileName):
    maxLen = os.pathconf("/", "PC_NAME_MAX") - 1
    base, ext = os.path.splitext(fileName)

    if len(fileName.encode("utf-8")) > maxLen:
        baseLen = maxLen - len(ext.encode("utf-8"))
        return base.encode("utf-8")[:baseLen].decode("utf-8", "ignore") + ext

    return fileName


def extractHAR(harFile):
    # Parse JSON
    obj = load(harFile)

    # Create folders for each page
    for page in obj["log"]["pages"]:
        title = page["id"]

        if not os.path.exists(title):
            os.mkdir(title)

    # Iterate over all entries
    files = set()
    for entry in obj["log"]["entries"]:

        # Skip any entries that aren't getting a file
        if entry["request"]["method"] != "GET":
            continue

        resp = entry["response"]
        status = resp["status"]
        content = resp["content"]

        # Skip if request was not successful
        if status != 200 and status != 206:
            continue

        # Create file if it doesn't already exist
        fileName = fileNameFromURL(entry["request"]["url"])

        # Add extension if there isn't one already
        mimeType = resp["content"]["mimeType"].partition(";")[0]
        ext = guess_extension(mimeType) or ""
        if ext != os.path.splitext(fileName)[1]:
            fileName += ext

        # Truncate file name if too long
        fileName = truncateFileName(fileName)

        fileName = os.path.join(entry["pageref"], fileName)

        # If the response is not partial content, add a unique suffix if a file
        # with the same name already exists
        if status != 206:
            i = 1
            base, ext = os.path.splitext(fileName)
            while os.path.exists(fileName):
                fileName = base + "_" + str(i) + ext
                i += 1

        # Create a new file if it doesn't already exist
        open(fileName, "a")

        # Open with right options
        newFile = open(fileName, "r+b")
        files.add(newFile)

        # Decode content
        data = content["text"].encode("utf-8")
        if "encoding" in content and content["encoding"] == "base64":
            data = decodebytes(data)

        # For partial content, first go to the correct offset
        if status == 206:
            content_range = [header["value"] for header in resp["headers"] if header["name"] == "content-range"][0]
            content_length = int(content["size"])

            if content_length != len(data):
                print(f"Expected data of length {content_length}, extracted data with length {len(data)}")

            offset = int(content_range.partition(" ")[2].partition("-")[0])
            newFile.seek(offset)

        # Add content to file
        newFile.write(data)

    # Close all files
    for file in files:
        file.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"Expected 1 argument, got {len(sys.argv) - 1}")

    fileName = sys.argv[1]

    with open(fileName, "r") as file:
        extractHAR(file)
