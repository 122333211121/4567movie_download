import requests
import time
import re
import os
from concurrent.futures import ThreadPoolExecutor
from Crypto.Cipher import AES

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'http://www.4567kp.com/',
}


def spider_id(keyword):
    url = 'http://www.4567kp.com/index.php/ajax/suggest'
    data = {
        'mid': '1',
        'wd': keyword,
        'limit': '10',
        'timestamp': time.time(),
    }

    response = requests.post(url, headers=headers, data=data)
    video_lists = response.json()['list']
    video_dict = dict()
    for video in video_lists:
        name = video['name']
        id = video['id']
        video_dict[name] = id
    return video_dict


def spider_video_ts(video_dict):
    print('查询到如下结果...')
    print(video_dict)
    name = input('请输入你想要下载的电影:')
    url = 'http://www.4567kp.com/ckplayer/index{}-1-1.html'.format(video_dict[name])

    response = requests.get(url, headers=headers).text
    pattern = re.compile('player_data=(.*?)}', re.S)
    result = re.findall(pattern, response)
    result = eval(result[0] + '}')
    result['url'] = result['url'].replace('\\', '')
    # result['url'] = result['url'].replace('/index.m3u8', '/hls/index.m3u8')
    return result['url']


def spider_video(url):
    response_1 = requests.get(url, headers=headers).text
    fake_url = response_1.split('\n')[-2]
    index_p = url.find('/', url.find('/', url.find('/')+1)+1)
    real_url = url[:index_p] + fake_url
    response = requests.get(real_url, headers=headers).text
    pattern = re.compile('URI="(.*?)"', re.S)
    key_url = re.findall(pattern, response)[0]
    response = response.replace(key_url, 'key.key')
    with open('./ts文件/index.m3u8', 'w+') as f:
        f.write(response)
    result = re.sub('#.*?\n', '', response)
    with open('./ts.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    results = result.split('\n')
    results.append(key_url)
    return results


def download_ts(key, i, results):
    for j in range(10):
        try:
            ts_content = requests.get(url=results[i], headers=headers, timeout=15).content
            with open('./ts文件/{}.ts'.format(i), 'wb+') as f:
                cryptor = AES.new(key, AES.MODE_CBC, key)
                f.write(cryptor.decrypt(ts_content))
            print(f'第{i}个文件下载完成')
            time.sleep(1)
            break
        except:
            print(f'第{i}个文件下载失败')
            time.sleep(1)
            continue


if __name__ == '__main__':
    keyword = input('请输入你想搜索的电影:')
    video_dict = spider_id(keyword)
    url = spider_video_ts(video_dict)
    result = spider_video(url)
    key = requests.get(url=result[-1], headers=headers).content
    try:
        with ThreadPoolExecutor(100) as t:
            for i in range(len(result)-1):
                t.submit(download_ts, key, i, result)
        t.shutdown()
        with ThreadPoolExecutor(50) as f:
            for i in range(len(result)-1):
                with open('./ts文件/{}.ts'.format(i), 'rb+') as file:
                    if file.read():
                        continue
                    else:
                        f.submit(download_ts, key, i, result)
        f.shutdown()
    except:
        list_dir = os.listdir('./ts文件')
        if len(list_dir) == len(result):
            print('下载完成')
            with open('./new.mp4', 'wb') as file:
                for i in range(len(list_dir)-1):
                    with open(f'./ts文件/{i}.ts', 'rb') as f:
                        f_view = f.read()
                        file.write(f_view)
        else:
            for i in range(len(result)):
                if f'{i}.ts' not in list_dir:
                    print(f'第{i}个文件未下载')
                    print('正在重新下载')
                    download_ts(key, i, result)
