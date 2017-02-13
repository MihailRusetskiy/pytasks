import urllib.request
import json
import itertools


class Bunch(object):
    def __init__(self, dictionary):
        for key in dictionary:
            setattr(self, key, dictionary[key])


def reddit(reddit):
    reddit_url = "http://www.reddit.com/r/{}.json".format(reddit)
    json_response = json.loads(urllib.request.urlopen(reddit_url).read().decode('utf8'))
    topics = json_response['data']['children']
    for topic in topics:
        yield Bunch(topic['data'])


python = reddit("python")
for topic in python:
    print(topic.title)
