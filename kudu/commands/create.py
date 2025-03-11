import os
import time

import click
import requests

from kudu.api import request
from kudu.commands.push import get_file_data, update_file_metadata


@click.command()
@click.option(
    "--instance", "-i", type=int, required=True, help="instance id to upload file"
)
@click.option("--body", "-b", type=str, required=True, help="Body of the file")
@click.option(
    "--filename", "-f", type=str, required=False, help="Name of the file in bucket"
)
@click.option("--path", "-p", type=click.Path(exists=True), default=None)
@click.option(
    "--extension",
    "-e",
    type=str,
    required=False,
    default="zip",
    help="Extension of the file that's going to be uploaded, default 'zip'",
)
@click.option("--skip_conversion", "-s", is_flag=True, default=False, required=False, help="Skip Conversion Engine")
@click.pass_context
def create(ctx, instance, body, filename=None, path=None, extension="zip",skip_conversion=False):
    base_name = (
        os.path.splitext(filename)[0]
        if filename
        else str(int(round(time.time() * 1000)))
    )

    file_data = get_file_data(path, base_name, category=extension)
    file_id = create_file(
        ctx.obj["token"], instance, body, extension, filename=filename, skip_conversion=skip_conversion
    )
    url = "/files/%d/upload-url/" % file_id
    response = request("get", url, token=ctx.obj["token"])
    # upload data
    requests.put(response.json(), data=file_data)

    # touch file
    update_file_metadata(ctx, file_id)


def create_file(token, app_id, file_body, category, filename=None, skip_conversion=False):
    payload = {
        "app": app_id,
        "body": file_body,
        "downloadUrl": "https://admin.pitcher.com/downloads/Pitcher%20HTML5%20Folder.zip",
        "category": category,
        "dont_convert": True,
        "skip_conversion": skip_conversion,
    }

    if filename:
        payload["filename"] = filename

    res = request("post", "/files/", json=payload, token=token)
    json = res.json()

    if res.status_code != 201 and res.status_code != 200:
        if json.get("app"):
            click.echo("Invalid instance", err=True)
        else:
            click.echo("Unknown error", err=True)
        print(json)
        exit(1)

    return json.get("id")
