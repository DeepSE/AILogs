import boto3
from datetime import datetime
import pytz
import validators
from urlextract import URLExtract


def put_ailog(url, comment, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
        dynamodb = boto3.resource('dynamodb')

    localtimezone = pytz.timezone('Asia/Seoul')
    today_str = datetime.now(localtimezone).strftime('%Y-%m-%d')

    table = dynamodb.Table('ailogTable5')
    response = table.put_item(
       Item={
            'comment': comment,
            'url': url,
            'date':  today_str
        }
    )
    return response

class MyURLExtractor(URLExtract):
    cache_dir = None 

    def set_cache_dir(self, dir):
        self.cache_dir = dir

    def _get_writable_cache_dir(self):
        if self.cache_dir:
            return self.cache_dir
        else:
            return "/tmp"

def put_db(text):

    extractor = MyURLExtractor(cache_dns=False, cache_dir='/tmp/')
    urls = extractor.find_urls(text)

    if len(urls) == 0:
        return "Give me 'url and memo` to record."
    
    # Remove URL from the text and make it to comment
    comment = text
    for url in urls:
        comment = comment.replace(url, "")

    res_text = ""
    for url in urls:
        valid=validators.url(url)
        if valid==False or not url.startswith('http'):
            res_text += 'Invalid url: ' + url + '\n'
            continue

        res = put_ailog(url, comment)
        res_text += 'Cool: ' + str(res['ResponseMetadata']['HTTPStatusCode']) + ' '  + url
    
    return res_text

if __name__ == '__main__':
    res = put_db("paperm htt?//www is very good")
    print(res)

    res = put_db("paperm okoko is very good")
    print(res)

    res = put_db("https://www.youtube.com/watch?v=1VdEw_mGjFk 이 비디오 너무 짱!")
    print(res)

    res = put_db("오오오 https://www.youtube.com/watch?v=1VdEw_mGjFk 이 비디오 너무 짱!")
    print(res)