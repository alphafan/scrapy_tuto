import scrapy
from bs4 import BeautifulSoup
import re
from datetime import datetime
import traceback
from pathlib import Path
import os

from sina.items import SinaItem


class SinaNewsSpider(scrapy.Spider):

    name = 'sina_news'
    with open(os.path.join(Path(__file__).parent, 'urls.txt'), 'r') as f:
        start_urls = f.readlines()
    custom_settings = {
        'LOG_LEVEL': 'ERROR'
    }

    def parse(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')
        tags = soup.find_all('a', href=re.compile('(?=^http.*sina.*\d{4}-\d{2}-\d{2}.*html$)'   # doc pattern
                                                  '(?=^((?!video).)*$)'                         # ignore video
                                                  '(?=^((?!photo).)*$)'                         # ignore photo
                                                  '(?=^((?!slide).)*$)'                         # ignore photo
                                                  '(?=^((?!csj\/author).)*$)'                   # ignore csj/s=author
                                                  ))
        for tag in tags:
            url = tag.get('href')
            yield scrapy.Request(url, callback=self.parse_details_and_continue_crawling)

    def parse_details_and_continue_crawling(self, response):
        # 1. Parse Details
        soup = BeautifulSoup(response.body, 'html.parser')
        try:
            # ==> Extract Title
            title = self.extract_title(soup)
            if title is None:
                raise Exception('Skip ' + response.url + ' can not find title')
            # ==> Extract Content
            content = self.extract_content(soup)
            if content is None:
                raise Exception('Skip ' + response.url + ' can not find content')
            # ==> Extract Pub Date
            pub_date = self.extract_pub_date(soup, response.url)
            if pub_date is None:
                raise Exception('Skip ' + response.url + ' can not find pub date')
            # ==> Extract Source
            source = self.extract_source(soup, response.url)
            if source is None:
                raise Exception('Skip ' + response.url + ' can not find source')
            # ==> Extract Keywords
            keywords = self.extract_keywords(soup)
            if keywords is None:
                # Keyword is not mandatory
                self.logger.warning('Can not find keywords for ' + response.url)
                keywords = ''
            print(title)
            item = SinaItem(_id=response.url, title=title, content=content,
                            pub_date=pub_date, source=source, keywords=keywords)
            yield item
        except Exception as e:
            self.logger.error(str(e))
            self.logger.error(traceback.format_exc())

        # 2. Continue crawling
        tags = soup.find_all('a', href=re.compile('(?=^http.*sina.*\d{4}-\d{2}-\d{2}.*html$)'   # doc pattern
                                                  '(?=^((?!video).)*$)'                         # ignore video
                                                  '(?=^((?!photo).)*$)'                         # ignore photo
                                                  '(?=^((?!slide).)*$)'                         # ignore photo
                                                  '(?=^((?!csj\/author).)*$)'                   # ignore csj/s=author
                                                  ))
        for tag in tags:
            url = tag.get('href')
            yield scrapy.Request(url, callback=self.parse_details_and_continue_crawling)

    @staticmethod
    def extract_title(soup):
        selectors = ['h1.main-title', 'h1.l_tit', '#artibodyTitle',
                     'h1#main_title', 'h1.title', 'div.catuncle-title h1',
                     'div.article-header h1', 'div.titleArea h1',
                     'span.location h1', 'h4.title', 'div.crticalcontent h1 span',
                     'div.news_text h1', 'h1.art_tit_h1', 'div.conleft_h1 h1',
                     'h1.m-atc-title', 'div.b_txt h1 a']
        for selector in selectors:
            if len(soup.select(selector)) != 0:
                return soup.select(selector)[0].text.strip()
        # If none of the selection matched title, try to find from meta header info
        if soup.title is not None and soup.title.string.strip() != '':
            return soup.title.string.strip()

    @staticmethod
    def extract_content(soup):
        selectors = ['div.article p', 'div#artibody p', 'div.mainContent p',
                     'div.article-body p', 'div#editHTML p', 'div.article-content p',
                     'div.l_articleBody p', 'div.catuncle-p p',
                     'div#artibody div p', 'div#articleContent p',
                     'div#fonttext p', 'div.pingcetext p',
                     'div.s_infor p', 'div.fonttext p']
        for selector in selectors:
            if len(soup.select(selector)) != 0:
                return '\n'.join([p.text for p in soup.select(selector)])

    @staticmethod
    def extract_pub_date(soup, url):
        # ==> Extract pub time string
        selectors = ['p.source-time span', 'p.origin span strong',
                     'span.date', 'span#pub_date', 'span.time', 'p.origin span strong',
                     'div.l_infoBox span', 'span.titer', '.source-time span',
                     'div.txtdetail', 'div.article_tit span', 'span.time-source']
        pub_time = None
        for selector in selectors:
            if len(soup.select(selector)) != 0:
                pub_time = soup.select(selector)[0].text.\
                       split('来源')[0].\
                       split('时间：')[-1].\
                       strip()
                break

        # Parse pub time string to date time
        date_patterns = [r"(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2}) (?P<h>\d{2}):(?P<M>\d{2})",
                         r"(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2}) (?P<h>\d{2}):(?P<M>\d{2})",
                         r"(?P<y>\d{4})年(?P<m>\d{2})月(?P<d>\d{2})日 (?P<h>\d{2}):(?P<M>\d{2})",
                         r"(?P<y>\d{4})年(?P<m>\d{2})月(?P<d>\d{2})日(?P<h>\d{2}):(?P<M>\d{2})"]
        if pub_time is not None:
            for pattern in date_patterns:
                if len(re.findall(pattern, pub_time)) > 0:
                    match = re.findall(pattern, pub_time)[0]
                    return datetime(int(match[0]), int(match[1]), int(match[2]),
                                    int(match[3]), int(match[4]))
        match = re.findall(r"(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})", url)[0]
        return datetime(int(match[0]), int(match[1]), int(match[2]))

    @staticmethod
    def extract_source(soup, url):
        selectors = ['span.source', 'a.source', 'span#art_source',
                     'span#media_name a', 'p.origin span.linkRed02',
                     'span#media_name', 'span.time-source span a', 'a.ent-source',
                     'div.l_infoBox em', 'div.article_tit', 'span.time-source a',
                     'span#author_ename a', 'div#m_atc_original p',
                     'div.b_txt p', 'p.art_p']
        for selector in selectors:
            if len(soup.select(selector)) != 0:
                return soup.select(selector)[0].text.\
                       split('作者：')[-1].\
                       split('来源：')[-1].\
                       split('时间：')[0].strip()
        if url.startswith('http://games.sina.com.cn') or \
           url.startswith('http://vr.sina.com.cn/'):
            return '新浪游戏'
        if url.startswith('http://news.sina.com.cn/gaotan/'):
            return '新浪新闻-议事厅'
        if url.startswith('http://tech.sina.com.cn/'):
            return '新浪科技'

    @staticmethod
    def extract_keywords(soup):
        for meta in soup.find_all('meta'):
            if meta.get('name') == 'keywords' and meta.get('content') != '':
                return meta.get('content')
            if meta.get('name') == 'tags' and meta.get('content') != '':
                return meta.get('content')
        selectors = ['div.keywords a', 'p.art_keywords a']
        for selector in selectors:
            if len(soup.select(selector)) != 0:
                return ','.join([a.text.strip() for a in soup.select('div.keywords a')])

