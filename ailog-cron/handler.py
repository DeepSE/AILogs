import boto3
from boto3.dynamodb.conditions import Attr
from linkpreview import link_preview

from datetime import datetime
from github import Github
import os
import pytz
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Define the category with JSON
with open('category.json') as json_file:
    category_dict = json.load(json_file)


def link2md(url):
    body = ""
    try:
        preview = link_preview(url)
        body += '> **' + preview.title + '**' + '\n'
        body += '> <img src="' + preview.image + '" height="64" style="float:left"/>'
        body += ' ' + preview.description + '\n' 
    except Exception:
        pass

    body += '> ' + url  + '\n'   

    return body

def get_type(url):
    assert category_dict is not None
    cat_txt = "article" # Default category
    for key in category_dict:
        for url_prefix in category_dict[key]:
            if url.startswith(url_prefix):
                cat_txt = key
                break

    return cat_txt

def read_db_write_issue():
    git_token = os.getenv('GITHUB_TOKEN', None)
    repo_name = os.getenv('GITHUB_REPOSITORY', None)

    if git_token is None:
        logger.error('Specify GITHUB_TOKEN as an environment variable.')
        exit(-1)
    
    if repo_name is None:
        logger.error('Specify GITHUB_REPOSITORY as an environment variable.')
        exit(-1)

    # Get the service resource.
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ailogTable5')

    localtimezone = pytz.timezone('Asia/Seoul')
    today_str = datetime.now(localtimezone).strftime('%Y-%m-%d')

    response  = table.scan(
        FilterExpression=Attr('date').eq(today_str)
    )

    items = response['Items']
    if len(items) == 0:
        logger.info("No items to write on " + today_str + ".")
        return

    # Fill the type
    for item in items:
        item['type'] = get_type(item['url'])
        print(item['type'], item['url'])

    # Sort by type
    items.sort(key=lambda x:x['type'])

    gh = Github(git_token)
    repo = gh.get_repo(repo_name)

    body = ""
    prev_type = None
    for item in items:
        if item['type'] != prev_type:
            prev_type = item['type']
            body += '\n# ' + item['type'] + '\n'

        body += '### ' + item['comment'] + '\n'
        body += link2md(item['url'])

    logger.info("Issue body " + body)

    res = repo.create_issue(title="AI LOG from " + today_str, body=body)
    logger.info("Issue on " + str(res))


def run(event, context):
    read_db_write_issue()
    current_time = datetime.now().time()
    name = context.function_name

    logger.info("Your cron function " + name + " ran at " + str(current_time))

if __name__ == '__main__':
    jconfig = json.load(open('../config.json'))
    os.environ["GITHUB_TOKEN"] = str(jconfig['GITHUB_TOKEN'])
    os.environ["GITHUB_REPOSITORY"] = str(jconfig['GITHUB_REPOSITORY'])

    read_db_write_issue()