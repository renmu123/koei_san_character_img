import os
from hashlib import md5
from pathlib import Path

import requests
from requests_html import HTMLSession
from zhconv import convert
from collections import defaultdict
import types

session = HTMLSession()


def download_pic(url, path, name):
    """下载图片

    :param url: 图片url
    :param path: 路径
    :param name: 图片名
    :return:
    """
    p = Path(path) / name
    if p.is_file():
        print('该文件已存在')
        return p
    try:
        r = requests.get(url)
        if not Path(path).exists():
            os.makedirs(path)
        with open(p, 'wb') as f:
            print('正在写入文件-{}'.format(name))
            f.write(r.content)
    except requests.exceptions.ConnectionError:
        raise KeyError('文件下载失败')
    return p


def group_by(data: list, key):
    """聚合函数
    for example:
        data: [{"name": "Tom", "age":15}, {"name": "Peter", "age":17}, {"name": "Alice", "age":15}]
        return {15:[{"name": "Tom", "age":15}, {"name": "Alice", "age":15}], 17:[{"name": "Peter", "age":17}]}

    :param data: [{},{}]
    :param key: 可以用 str 也可以用lambda
    :return:
    """
    group_data = defaultdict(list)
    if isinstance(key, types.FunctionType):
        for r in data:
            k = key(r)
            group_data[k].append(dict(r.items()))
    elif isinstance(key, (int, str, tuple)):
        for r in data:
            group_data[r[key]].append(dict(r.items()))
    else:
        raise KeyError('key既不是 str, int, tuple 也不是 function')
    return group_data


def parse_pic_url(url):
    """解析页面（http://san.nobuwiki.org/sancg/san12）获得内部的超链接， 然后又再用这个函数进行解析 parse_html()
    仅仅支持9-13
    ["http://san.nobuwiki.org/sancg/san09", "http://san.nobuwiki.org/sancg/san10", "http://san.nobuwiki.org/sancg/san11"
    , "http://san.nobuwiki.org/sancg/san12", "http://san.nobuwiki.org/sancg/san13"]

    :param url:
    :return:
    """
    r = session.get(url)
    for ele in r.html.find(".excerpt"):
        url = list(ele.find("header", first=True).absolute_links)[0]
        yield url


def parse_main_html(url):
    """解析网页

    :param url:
    :param v: 版本号，例如311， 312
    :return:
    """
    r = session.get(url)
    for ele in r.html.find('.nb_14pk_240'):
        data = ele.find('a')
        url = list(data[0].absolute_links)[0]
        desc = ele.text

        try:
            name = data[1].text
        except IndexError:
            name = ele.text
        yield {
            "name": convert(name, "zh-cn"),
            "desc": convert(desc, "zh-cn"),
            "url": url
        }


def parse_all_pic(url, v):
    """

    :param url: 图片上一级的页面 like("http://san.nobuwiki.org/sancg/san09")
    :param v: 版本
    :return:
    """
    array = []
    for url in parse_pic_url(url):
        for data in parse_main_html(url):
            array.append(data)

    for desc, data in group_by(array, "desc").items():
        desc = desc.replace("\n", " ")
        for index, n_data in enumerate(data):
            if index == 0:
                name = desc
            else:
                name = f"{desc}_{index}"
            md5_name = md5(f"{name}_{v}".encode('utf-8')).hexdigest()

            yield n_data["url"], name, md5_name


def download_pic_with_md5(url, v):
    """用md5来当文件名

    :param url: 图片url
    :param v: 版本（like 311）
    :return: path
    """
    for img_url, name, md5_name in parse_all_pic(url, v):
        path = download_pic(img_url, v, f"{md5_name}.jpg")
        yield path


def main():
    """下载 309， 310， 311， 312， 313 的人物照片

    :return:
    """
    url_array = [("39", "http://san.nobuwiki.org/sancg/san09"), ("310", "http://san.nobuwiki.org/sancg/san10"),
                 ("311", "http://san.nobuwiki.org/sancg/san11"), ("312", "http://san.nobuwiki.org/sancg/san12"),
                 ("313", "http://san.nobuwiki.org/sancg/san13")]

    for v, url in url_array:
        for img_url, name, md5_name in parse_all_pic(url, v):
            download_pic(img_url, f".\\{v}_s\\", f"{name}.jpg")


if __name__ == '__main__':
    main()
