import os
import sys
import time
import random
import argparse
from bs4 import BeautifulSoup
from common import request, load, save, sync


class BookPool:

    def __init__(self, tag, start, end, maxlen, baseURL):
        self.tag = tag
        self.start = start
        self.end = end
        self.maxlen = maxlen
        self.tagURL = '%s/%s?start=' % (baseURL, tag)

    def crawl(self, step, resultPath, mergeMaxDelay=30, mergeMaxRetries=5):
        '''
        Steps:
        1. clear  (necessary due to possible previous failure)
           (1) clear local / remote branch
        2. fill a branch  (but not main, to reduce conflicts)
           (1) (re)create & switch to local branch
           (2) download
           (3) add, commit: content -> local branch
           (4) push: local branch -> remote branch
        3. merge to main
           (1) merge: branch -> local (latest) main  (probably takes a while)
           (2) merge: branch -> local (latest) main  (for case: main updated during 3.1)
           (3) push: local main -> remote main
        4. clear
           (1) clear remote branch
        '''
        branch = 'tag/' + self.tag
        bookPath = os.path.join(resultPath, 'books')
        flagPath = os.path.join(resultPath, 'flags', self.tag + '.json')
        visited = set(load(flagPath)) if os.path.exists(flagPath) else set()

        hit = 0
        for current in range(self.start, self.end, step):
            url = '%s%d' % (self.tagURL, current)
            if url in visited:
                continue
            r = request(url)
            if '没有找到符合条件的图书' in r.text:
                break
            hit += 1
            if (hit == 1):
                sync('clear', branch)
                sync('create', branch)
            for imgURL, desc in self._parse(r.text):
                self._download(imgURL, bookPath, desc)
            visited.add(url)
        else:
            print('尚未触达末页，后面可能还有内容')

        if hit > 0:
            save(list(visited), flagPath)
            sync('push', branch, 'Auto-commit: ' + self.tag)
            for _ in range(mergeMaxRetries):
                if (sync('merge', branch)):
                    break
                else:
                    time.sleep(random.random() * mergeMaxDelay)
            else:
                raise Exception('Reached the maximum attempts without success.')
            sync('clear', branch)

    def _sync(self, condition, *args, **kwargs):
        return sync(*args, **kwargs) if condition else True

    def _parse(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        items = soup.select('li.subject-item')
        for item in items:
            anchor = item.select('.info > h2 > a')[0]
            detailURL = anchor['href'].strip()
            bookID = detailURL.split('/subject/')[-1].replace('/', '').strip()
            title = anchor['title'].strip()
            if len(title) > args.maxlen:
                title = title[:args.maxlen] + '…'
            fullTitle = anchor.text.replace(' ', '').replace('\n', '').strip()

            pubDesc = item.select('.info > .pub')[0].text.strip()
            try:
                pub, date, price = pubDesc.split(' / ')[-3:]
                pub, date, price = pub.strip(), date.strip(), price.strip()
                if (
                    len(pub) > args.maxlen
                ) or (
                    not self._hasNum(date)
                ) or (
                    not self._hasNum(price)
                ):
                    raise ValueError('Invalid pub / date / price.')
            except:
                pub, date, price = '', '', ''

            try:
                rate = float(item.select('.rating_nums')[0].text.strip())
                numRates = int(''.join([c for c in item.select('.pl')[0].text if c.isdigit()]))
            except:
                rate, numRates = '', ''

            img = item.select('.pic > a > img')[0]
            imgURL = img['src']

            desc = '~~'.join([str(s) for s in [
                rate,
                title,
                numRates,
                pub,
                date,
                price,
                bookID,
                # pubDesc,      # file name too long
                # fullTitle,    # file name too long
            ]])
            yield imgURL, desc

    def _download(self, url, bookPath, desc):
        path = os.path.join(bookPath, self._rename(desc) + '.jpg')
        r = request(url)
        save(r.content, path, 'wb')

    def _rename(self, filename):
        for k, v in {
            '] ': ']',
            ' / ': '##',
            '"': '”',
            '*': '_',
            '/': '_',
            ':': '：',
            '<': '《',
            '>': '》',
            '?': '？',
            '\\': '_',
            '|': '》',
        }.items():
            filename = filename.replace(k, v)
        return filename

    def _hasNum(self, s):
        return any(c.isdigit() for c in s)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Basic book information extraction.')
    parser.add_argument('tag')
    parser.add_argument('--start', default=0, type=int)
    parser.add_argument('--end', default=sys.maxsize, type=int)
    parser.add_argument('--step', default=20, type=int)
    parser.add_argument('--maxlen', default=48, type=int)
    parser.add_argument('--result', default='results')
    parser.add_argument('--baseURL', default='https://book.douban.com/tag')
    args = parser.parse_args()

    bookPool = BookPool(args.tag, args.start, args.end, args.maxlen, args.baseURL)
    bookPool.crawl(args.step, args.result)
