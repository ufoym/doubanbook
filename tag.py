from common import request
from bs4 import BeautifulSoup


class TagPool:

    def __init__(self, baseURL = 'https://book.douban.com/tag'):
        self.baseURL = baseURL
        self.tags = self._crawlTags()

    def toDict(self):
        return self.tags

    def toList(self, simple=True):
        for ltag, stags in self.tags.items():
            for stag in stags:
                if simple:
                    yield stag
                else:
                    yield stag, ltag, stags[stag]

    def toURLs(self):
        for ltag, stags in self.tags.items():
            for stag in stags:
                yield '/'.join([self.baseURL, stag])

    def _crawlTags(self, tag_postfix = '/?view=type&icn=index-sorttags-all'):
        tags = {}
        tagURL = self.baseURL + tag_postfix
        r = request(tagURL)
        soup = BeautifulSoup(r.text, 'html.parser')
        ltags = soup.select('a.tag-title-wrapper')
        for ltag in ltags:
            lname = ltag['name']
            tags[lname] = {}
            stags = ltag.parent.find_all('td')
            for stag in stags:
                sname = stag.a.string
                hot = int(''.join(c for c in stag.b.string if c.isdigit()))
                tags[lname][sname] = hot
        return tags

if __name__ == '__main__':
    tagPool = TagPool()

    # print('\n\n'.join(['%s: %r' % (ltag, stags) for ltag, stags in tagPool.toDict().items()]))
    # print(', '.join(['%s@%s%d' % t for t in tagPool.toList()]))
    # print('\n'.join(['%s' % t for t in tagPool.toURLs()]))

    print(list(tagPool.toList()))
