# -*- coding: utf-8 -*-
import json
import re

import datetime
import scrapy
from urllib import parse
from scrapy.loader import ItemLoader
from ArticleSpider.items import ZhihuQuestionItem, ZhihuAnswerItem

password = "w707194"


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    answer_start_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}"
    agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36"
    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        "User-Agent": agent
    }

    def parse(self, response):
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x: True if x.startswith("https") else False)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                # 是一个问题的连接，开始分析
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(request_url, headers=self.headers, meta={"id", int(question_id)},
                                     callback=self.parse_question)
            else:
                # 不是一个问题的连接，深度搜索
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    def parse_question(self, response):
        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)

        if "QuestionHeader-title" in response.text:
            # new version html
            item_loader.add_css("title", ".QuestionHeader-title::text")
            item_loader.add_css("content", ".QuestionHeader-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", response.meta.get("id", 0))
            item_loader.add_css("answer_num", ".List-headerText span::text")
            item_loader.add_css("comment_num", ".QuestionHeaderActions button::text")
            item_loader.add_css("watch_num", ".NumberBoard-value::text")
            item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")
        else:
            # old version html
            item_loader.add_xpath("title",
                                  "//*[@id='zh-question-title']/h2/a/text()|//*[@id='zh-question-title']/h2/span/text()")
            item_loader.add_css("content", "#zh-question-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", response.meta.get("id", 0))
            item_loader.add_css("answer_num", "#zh-question-answer-num::text")
            item_loader.add_css("comment_num", "#zh-question-meta-wrap a[name='addcomment']::text")
            item_loader.add_xpath("watch_num",
                                  "//*[@id='zh-question-side-header-wrap']/text()|//*[@class='zh-question-followers-sidebar']/div/a/strong/text()")
            item_loader.add_css("topics", ".zm-tag-editor-labels a::text")

        question_item = item_loader.load_item()
        yield scrapy.Request(self.answer_start_url.format(response.meta.get("id", 0), 20, 0), headers=self.headers,
                             callback=self.parse_answer)
        yield question_item

    def parse_answer(self, response):

        ans_json = json.load(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comment_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    def start_requests(self):
        return [scrapy.Request('https://www.zhihu.com/#signin', callback=self.login, headers=self.headers)]

    def login(self, response):
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text, re.DOTALL)
        xsrf = ""
        if match_obj:
            xsrf = match_obj.group(1)
        if xsrf:
            post_data = {
                "_xsrf": xsrf,
                "phone_num": "15754302311",
                "password": password,
                "captcha": ""
            }
            import time
            t = str(int(time.time() * 1000))
            captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)

            yield scrapy.Request(captcha_url, headers=self.headers, meta={"post_data": post_data},
                                 callback=self.login_after_captcha)

    def login_after_captcha(self, response):
        with open("captcha.jpg", "wb") as f:
            f.write(response.body)
            f.close()
        from PIL import Image
        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except:
            pass
        captcha = input("输入验证码\n>")
        post_data = response.meta.get("post_data", {})
        post_data["captcha"] = captcha

        return [scrapy.FormRequest(
            url="https://www.zhihu.com/login/phone_num",
            formdata=post_data,
            headers=self.headers,
            callback=self.check_login
        )]

    def check_login(self, response):
        text_json = json.load(response.text)
        if "msg" in text_json and text_json["msg"] == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.headers)
