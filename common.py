import os
import time
import json
import random
import requests
import subprocess
import collections

def load(path, mode = 'r'):
    if path.endswith('.json'):
        with open(path, mode, encoding='utf-8') as f:
            return json.load(f)
    else:
        with open(path, mode) as f:
            return f.read()

def save(obj, path, mode = 'w'):
    ppath = os.path.dirname(path)
    if not os.path.exists(ppath):
        os.makedirs(ppath)
    if path.endswith('.json'):
        if type(obj) is list:
            obj = sorted(obj)
        elif type(obj) is dict:
            obj = collections.OrderedDict(sorted(obj.items()))
        with open(path, mode, encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=4)
    else:
        with open(path, mode) as f:
            f.write(obj)

def request(url, maxDelay = 3.0, maxRetries = 20, headers = [
    {"User-Agent": "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60"},
    {"User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.3.4000 Chrome/30.0.1599.101 Safari/537.36"}
]):
    time.sleep(random.random() * maxDelay)
    print('>', url)
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=maxRetries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    r = session.get(
        url,
        headers=random.choice(headers)
    )
    if '有异常请求从你的 IP 发出' in r.text:
        raise Exception('BAN')
    return r

def sync(action, branch = 'main', msg = 'Auto-commit', firstTime=[True]):
    scriptPrepare = '''
        git config --global user.name 'bot'
        git config --global user.email 'bot@bot.bot'
    '''
    scriptCreate = '''
        git checkout -b %s
    ''' % branch
    scriptPush = '''
        git add .
        git diff-index --quiet HEAD || git commit -m "%s"
        git push origin %s
    ''' % (msg, branch)
    scriptMerge = '''
        git checkout main
        git pull --rebase origin main

        git checkout %s
        git merge -X theirs main
        git push origin %s

        git checkout main
        git merge -X ours %s
        git pull --rebase origin main
        git push origin main
    ''' % (branch, branch, branch)
    scriptClear = '''
        git branch -D %s
        git push origin --delete %s
    ''' % (branch, branch)

    raw = ''
    if (firstTime[0]):
        raw += scriptPrepare
        firstTime[0] = False
    if action == 'create':
        raw += scriptCreate
    elif action == 'push':
        raw += scriptPush
    elif action == 'merge':
        raw += scriptMerge
    elif action == 'clear':
        raw += scriptClear

    success = True
    for line in raw.splitlines():
        command = line.strip()
        if command:
            print('>>', command)
            result = subprocess.run(command, shell=True, capture_output=True)
            if result.returncode != 0:
                success = False
                stderr = result.stderr.decode('utf-8')
                print('-' * 36, 'stderr', '-' * 35)
                print(stderr)
    return success
