# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import re
import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from scrapy.loader import ItemLoader
import datetime
from ArticleSpider.utils.common import get_nums
from ArticleSpider.settings import SQL_DATE_FORMAT,SQL_DATETIME_FORMAT

class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass




class ArticleItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


def date_convert(value):
    try:
        date = datetime.datetime.strftime(value, "%Y/%m/%d").date()
    except Exception as e:
        date = datetime.datetime.now().date()
    return date


def remove_comment_from_tags(value):
    if "评论" in value:
        return ""
    else:
        return value


def just_return(value):
    return value


class JobBoleArticleItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    create_date = scrapy.Field(
        input_processor=MapCompose(date_convert)
    )
    front_image_url = scrapy.Field(
        output_processor=MapCompose(just_return)

    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    comment_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_from_tags),
        output_processor=Join(",")

    )
    content = scrapy.Field()

class ZhihuQuestionItem(scrapy.Item):
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comment_num = scrapy.Field()
    watch_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_aql(self):
        insert_sql = """
            insert into zhihu_question_table(zhihu_id,topics,url,title,answer_num,comment_num,watch_num,click_num,crawl_time)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE answer_num=VALUES(answer_num),watch_num=VALUES(watch_num),
            comment_num=VALUES(comment_num),click_num=VALUES(click_num)
        """
        # item["key"]获取到的值都是list，要做处理
        zhihu_id = self["zhihu_id"][0]
        topics = ",".join(self["topics"])
        url = self["url"][0]
        title = self["title"][0]
        content = self["content"][0]
        ans_num = get_nums(self["answer_num"][0])
        comment_num = get_nums(self["comment_num"][0])
        watch_num = get_nums(self["watch_num"][0])
        click_num = get_nums(self["click_num"][0])
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)
        params = (zhihu_id, topics, url, title, content, ans_num, comment_num, watch_num, click_num, crawl_time)
        return insert_sql, params

class ZhihuAnswerItem(scrapy.Item):
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comment_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_aql(self):
        insert_sql = """
            insert into zhihu_answer_table(zhihu_id, url, question_id, author_id, content,
            praise_num, comment_num, create_time, update_time, crawl_time)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE content=VALUES(content),praise_num=VALUES(praise_num),
            comment_num=VALUES(comment_num),update_time=VALUES(update_time)
        """
        # item["key"]获取到的值都是list，要做处理

        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        params = (
            self["zhihu_id"], self["url"], self["question_id"],
            self["author_id"], self["content"], self["praise_num"],
            self["comment_num"], create_time, update_time,
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )
        return insert_sql, params