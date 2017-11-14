# -*-coding:utf-8-*-
import os
from scrapy.cmdline import execute
import sys

main_path = os.path.dirname(os.path.abspath(__file__)) # 获取工程目录
sys.path.append(main_path)
# execute(['scrapy', 'crawl', 'jobbole'])
execute(['scrapy', 'crawl', 'lagou'])
# print(main_path)
