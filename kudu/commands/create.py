import os
import time
import click
import requests

from kudu.api import request
from kudu.commands.push import get_file_data, update_file_metadata

@click.command()
@click.option('--instance', '-i', type=int, required=True, help="instance id to upload file")
@click.option('--body', '-b', type=str, required=True, help="Body of the file")
@click.option('--filename', '-f', type=str, required=False, help="Name of the file in bucket")
@click.option('--path', '-p', type=click.Path(exists=True), default=None)
@click.option('--extension', '-e', type=str, required=False, default="zip", help="Extension of the file that's going to be uploaded, default 'zip'")
@click.pass_context
def create(ctx, instance, body, filename = None, path = None, extension = "zip"):
    file_data = get_file_data(path, filename or '%i%s' % (int(round(time.time() * 1000)), extension), category=extension)
    file_id = create_file(ctx.obj['token'], instance, body, extension, filename=filename)
    url = '/files/%d/upload-url/' % file_id
    response = request('get', url, token=ctx.obj['token'])
    # upload data
    requests.put(response.json(), data=file_data)

    # touch file
    update_file_metadata(ctx, file_id)


def create_file(token, app_id, file_body, category, filename):
    res = request(
        'post',
        '/files/',
        json={
            'app':
                app_id,
            'body':
                file_body,
            'downloadUrl':
                'https://admin.pitcher.com/downloads/Pitcher%20HTML5%20Folder.zip',
            'category': category,
            'filename': filename,
            'dont_convert': True
        },
        token=token
    )
    json = res.json()

    if res.status_code != 201 and res.status_code != 200:
        if json.get('app'):
            click.echo('Invalid instance', err=True)
        else:
            click.echo('Unknown error', err=True)
        print(json)
        exit(1)

    return json.get('id')
