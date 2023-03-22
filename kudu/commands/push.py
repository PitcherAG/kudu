import os
from collections import namedtuple
from datetime import datetime

import click
import requests

from kudu.api import request as api_request
from kudu.config import ConfigOption
from kudu.mkztemp import NameRule, mkztemp
from kudu.types import PitcherFileType

CategoryRule = namedtuple('crule', ('category', 'rule'))


CATEGORY_RULES = (
    CategoryRule('',
                 NameRule((r'^interface', r'(.+)'), ('{base_name}', '{0}'))),
    CategoryRule(('presentation', 'zip'),
                 NameRule(r'^thumbnail.png', '{base_name}.png')),
    CategoryRule(('presentation', 'zip'),
                 NameRule(r'(.+)', ('{base_name}', '{0}'))),
) # yapf: disable


@click.command()
@click.option(
    '--file',
    '-f',
    'pf',
    cls=ConfigOption,
    config_name='file_id',
    prompt=True,
    type=PitcherFileType(category=('zip', 'presentation', 'json', ''))
)
@click.option('--path', '-p', type=click.Path(exists=True), default=None)
@click.pass_context
def push(ctx, pf, path):
    name = pf['filename']
    base_name, _ = os.path.splitext(name)

    url = '/files/%d/upload-url/' % pf['id']
    response = api_request('get', url, token=ctx.obj['token'])

    if path is None or os.path.isdir(path):
        rules = [c.rule for c in CATEGORY_RULES if pf['category'] in c.category]
        fp, _ = mkztemp(base_name, root_dir=path, name_rules=rules)
        data = os.fdopen(fp, 'r+b')
    else:
        data = open(path, 'r+b')

    # upload data
    requests.put(response.json(), data=data)

    # touch file
    url = '/files/%d/' % pf['id']
    json = {
        'creationTime': datetime.utcnow().isoformat(),
        'metadata': get_metadata_with_github_info(ctx, pf)
    }
    api_request('patch', url, json=json, token=ctx.obj['token'])


def get_metadata_with_github_info(ctx, pf):
    # first get existing metadata then modify it
    url = '/files/%d/' % pf['id']
    response = api_request('get', url, token=ctx.obj['token']).json()
    metadata = response.get('metadata', {})

    # NOT losing repo info for non-github deployments
    current_repo_info = metadata.get('GITHUB_REPOSITORY', 'not_available') 
    metadata['GITHUB_REPOSITORY'] = os.environ.get('GITHUB_REPOSITORY', current_repo_info)

    # losing commit SHA and run id info for non-github deployments
    metadata['GITHUB_SHA'] = os.environ.get('GITHUB_SHA', 'not_available')
    metadata['GITHUB_RUN_ID'] = os.environ.get('GITHUB_RUN_ID', 'not_available')

    return metadata