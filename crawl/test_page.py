import asyncio
import re
from urllib.parse import urljoin
from scrapy import Selector
from . import parse_context
from .R2 import Request
from .frame import Frame
from .frame import get_chinese, search_date_time, find_xpath_case, from_xpath_case_to_xpath, get_content
import operator
import copy
from pyppeteer import launch


async def init_browser():
    # 启动浏览器
    browser = await launch({
        # 'headless': False,  # 关闭无头模式
        'args': [
            '--log-level=3  ',
            '--disable-images',
            '--disable-extensions',
            '--hide-scrollbars',
            '--disable-bundled-ppapi-flash',
            '--mute-audio',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-gpu',
            '–single-process',  # 将Dom的解析和渲染放到一个进程，省去进程间切换的时间
            '--disable-infobars',  # 禁止信息提示栏
            '--disable-dev-shm-usage',  # 禁止使用/dev/shm，防止内存不够用,only for linux
            '--no-default-browser-check',  # 不检查默认浏览器
            '--disable-hang-monitor',  # 禁止页面无响应提示
            '--disable-translate',  # 禁止翻译
            '--disable-setuid-sandbox',
            '--no-first-run',
            '--no-zygote',
        ],
    })
    return browser


async def request_check(req):
    # 请求过滤
    if req.resourceType in ['image', 'media']:
        await req.abort()
    else:
        await req.continue_()


async def handle_dialog(dialog):
    await dialog.dismiss()


def find_xpath_case_in_frames(frame_list, index):
    if not frame_list:
        return 0
    else:
        for tmp_frame in [frame_list[index]] + frame_list:
            case = find_xpath_case(tmp_frame.selector)
            if case != 0:
                return case
    return 0


async def run_parser(parser_obj):
    await parser_obj.manager()


class Parser:
    def __init__(self, config):
        self.next_button = config['next_button']
        self.action_pattern = config['action']
        self.code = config['code']
        self.province = config['province']
        self.city = config['city']
        self.target_url = config['target_url']
        self.item_pattern = config['item_pattern']
        self.main_text_pattern = config['main_text_pattern']
        self.gov = config['gov']
        self.source_type = config['source']
        self.date_type = config['date_type']
        self.zupei_type = config['zupei_type']
        self.title_type = config['title']
        self.page = None
        self.xpath_case = 0  # 翻页规则
        self.sub_url_already_crawl = dict()
        self.data_list = list()
        self.status_list = [{"stage": "网页打开阶段", "status": 1, "info": "成功"},
                            {"stage": "子链接获取阶段", "status": 1, "info": "成功"},
                            {"stage": "文本解析方法检测阶段", "status": 2, "info": "使用Requests加速解析"},
                            {"stage": "文本解析方法检测阶段", "status": 1, "info": "成功"},
                            {"stage": "子链接解析阶段", "status": 1, "info": "成功"},
                            {"stage": "翻页爬取阶段", "status": 2, "info": "网页解析终止在第2页"}]
    
    async def wait_for_change(self, item_list, max_retries=0):
        retries_times = 0
        while True:
            retries_times += 1
            new_frames = await self.get_frame()
            new_sub_urls = await self.try_to_get_sub_url(new_frames)
            if not operator.eq(new_sub_urls, item_list):
                return
            else:
                if max_retries and retries_times > max_retries:
                    print('休息了很久还是没有翻页成功')
                    return
                else:
                    await asyncio.sleep(1)
    
    @staticmethod
    def remove_js_css(content):
        # remove the the javascript and the stylesheet and the comment content
        # (<script>....</script> and <style>....</style> <!-- xxx -->)
        r = re.compile(r'<script.*?</script>', re.I | re.M | re.S)
        s = r.sub('', content)
        r = re.compile(r'<style.*?</style>', re.I | re.M | re.S)
        s = r.sub('', s)
        r = re.compile(r'<link.*?>', re.I | re.M | re.S)
        s = r.sub('', s)
        r = re.compile(r'<meta.*?>', re.I | re.M | re.S)
        s = r.sub('', s)
        r = re.compile(r'<ins.*?</ins>', re.I | re.M | re.S)
        s = r.sub('', s)
        return s
    
    @staticmethod
    def find_img(url, domain):
        image_list = []
        img_li = domain.xpath('.//img[@src != ""]')
        for img in img_li:
            img_src = img.xpath('.//@src').extract_first()
            image_list.append(urljoin(url, img_src))
        return image_list
    
    @staticmethod
    def find_attachment(url, domain):
        attachment_list = []
        a_list = domain.xpath('.//a[@href != "" and text() != ""]')
        for a in a_list:
            a_text = ''.join(a.xpath('.//text()').extract())
            a_href = a.xpath('.//@href').extract_first().strip()
            pattern1 = re.compile('(.doc|\.docx|\.pdf|\.csv|\.xlsx|\.xls|\.txt)')  # 找到文件后缀
            result1 = pattern1.findall(a_text)
            pattern2 = re.compile('附件')  # 找到附件字样
            result2 = pattern2.findall(a_text)
            if result1 or result2:
                attachment_list.append(str(a_text) + '(' + str(urljoin(url, a_href)) + ')')
        return attachment_list
    
    def parse_struct_info(self, selector0):
        remove_list = ['稿源', '来源', '发布机构', '发布日期', '发文机关']
        if self.date_type:
            try:
                date_raw = selector0.xpath(self.date_type).extract_first()
            except Exception:
                date = ''
            else:
                if isinstance(date_raw, str):
                    date = search_date_time(date_raw)
                else:
                    date = ''
        else:
            date = ''
        if self.zupei_type and self.zupei_type[0] == '/':
            self.zupei_type = self.zupei_type.replace('tbody', '')
            if 'text()' not in self.zupei_type:
                self.zupei_type = self.zupei_type + '//text()'
            try:
                zupei = get_chinese(''.join(selector0.xpath(self.zupei_type).extract()))
            except Exception:
                zupei = ''
        else:
            zupei = self.zupei_type
        if self.source_type and self.source_type[0] == '/':
            self.source_type = self.source_type.replace('tbody', '')
            if 'text()' not in self.source_type:
                self.source_type = self.source_type + '//text()'
            try:
                source = get_chinese(''.join(selector0.xpath(self.source_type).extract()))
            except Exception:
                source = ''
            else:
                for item in remove_list:
                    source = source.replace(item, '')
        else:
            source = self.source_type
        if self.title_type:
            self.title_type = self.title_type.replace('tbody', '')
            if 'text()' not in self.title_type:
                self.title_type = self.title_type + '//text()'
            try:
                title = ''.join(selector0.xpath(self.title_type).extract()).strip()
            except Exception:
                title = ''
            else:
                if title[:2] == "名称" or title[:2] == "标题":
                    title = title[3:]
        else:
            title = ''
        return date, zupei, source, title
    
    def parse_main_text(self, url, text):
        main_text, img_text, attachment_text = '', '', ''
        selector = Selector(text=text)
        try:
            main_domain = selector.xpath(self.main_text_pattern)
            main_text_list = [item.strip() for item in main_domain.xpath('.//text()').extract()]
        except Exception:
            task = parse_context.MAIN_TEXT(url=url, text=text)
            try:
                result_dict = task.main()
            except Exception:
                return '', '', ''
            else:
                main_text = result_dict['content']
                img_text = ','.join(result_dict['img'])
                attachment_text = ','.join(result_dict['attachment'])
        else:
            main_text = ''.join(main_text_list)
            if len(main_text) < 100:
                img_list = self.find_img(url, main_domain)
                img_text = ','.join(img_list)
                attachment_list = self.find_attachment(url, main_domain)
                attachment_text = ','.join(attachment_list)
        if len(img_text) > 60000:
            img_text = ''
        if len(attachment_text) > 60000:
            attachment_text = ''
        return main_text, attachment_text, img_text
    
    async def parse_detail(self, sub_links, frame_list, index):
        for title in list(sub_links.keys()):
            self.sub_url_already_crawl[title] = sub_links[title]  # 无论结果如何都要存进去，避免僵死
            sub_url = sub_links[title][0]
            if sub_url[-4:] in {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv'}:
                self.data_list.append({'title': title, 'sub_url': sub_url, 'date': sub_links[title][1], 'main_text': '',
                                       'zupei_type': '', 'source': '', 'attachment': '', 'img': ''})
                continue
            elif not self.use_browser:
                request = Request(sub_links[title][0])
                request.get_page()
                if not request.text:  # 无法连接
                    self.data_list.append({'title': title, 'sub_url': sub_url, 'date': sub_links[title][1], 'main_text': '',
                                           'zupei_type': '', 'source': '', 'attachment': '', 'img': ''})
                    continue
                else:
                    request_text = self.remove_js_css(request.text)
                    selector = Selector(text=request_text)
            else:
                xpath = "//a[text()='{}' or @title='{}']".format(title, title)
                button_selector = frame_list[index].selector.xpath(xpath)
                button = await frame_list[index].raw_frame.xpath(xpath)
                if not button:
                    continue
                if button_selector.xpath('./@target').extract_first() == '_blank':
                    await button[0].click()
                    await asyncio.sleep(1)
                    while True:
                        pages = await self.browser.pages()
                        if len(pages) == 2:
                            break
                        else:
                            await asyncio.sleep(1)
                    content = await get_content(pages[-1])
                    sub_url = pages[-1].url
                    await pages[-1].close()
                else:
                    await asyncio.wait([button[0].click(), self.page.waitForNavigation(timeout=6 * 1000)])
                    content = await get_content(self.page)
                    sub_url = self.page.url
                    await asyncio.wait([self.page.goBack(), self.page.waitForXPath(xpath=xpath, timeout=6)])
                request_text = self.remove_js_css(content)
                selector = Selector(text=request_text)
                frame_list = await self.get_frame()
            date, zupei, source, title_in_page = self.parse_struct_info(selector)
            if not date:  # 为date上双保险
                date = sub_links[title][1]
            if title_in_page:  # 为title上双保险
                save_title = title_in_page
            else:
                save_title = title
            if self.main_text_pattern:
                main_text, attachment, img = self.parse_main_text(sub_url, selector)
                self.data_list.append({'title': save_title, 'sub_url': sub_url, 'date': date, 'main_text': main_text,
                                       'zupei_type': zupei, 'source': source, 'attachment': attachment, 'img': img})
            else:
                try:
                    task = parse_context.MAIN_TEXT(sub_url, request_text)
                    result_dict = task.main()
                    main_text = result_dict['content']
                    img = ','.join(result_dict['img'])
                    attachment = ','.join(result_dict['attachment'])
                except Exception:
                    main_text = ''
                    img = ''
                    attachment = ''
                self.data_list.append({'title': save_title, 'sub_url': sub_url, 'date': date, 'main_text': main_text,
                                       'zupei_type': zupei, 'source': source, 'attachment': attachment, 'img': img})
        return frame_list
    
    def test_request(self, sub_links):
        count_for_cant_request = 0  # 用来计数，只有出现所有子链接都无法识别的情况，才使用浏览器
        door = max(int(len(sub_links) / 2), 3)  # 退出的阈值
        for title in list(sub_links.keys()):
            if (count_for_cant_request >= door) or ('http' not in sub_links[title][0]):
                self.use_browser = True
                error_info = u'使用浏览器捕获数据'
                self.status_list[2]['status'], self.status_list[2]['info'] = 0, error_info
                return
            if sub_links[title][0][-4:] in {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv'}:  # 子链接即为pdf附件的
                self.use_browser = False
                return
            request = Request(sub_links[title][0])
            request.get_page()
            if not request.text:  # 无法连接
                count_for_cant_request += 1
                continue
            else:
                if self.main_text_pattern:
                    main_text, attachment, img = self.parse_main_text(sub_links[title][0], request.text)
                    if len(main_text) > 30:
                        self.use_browser = False
                        return
                    elif any([main_text, attachment, img]):
                        # 最起码要有一个捕获到数据算是认为页面请求有效
                        continue
                    else:
                        count_for_cant_request += 1
                else:
                    task = parse_context.MAIN_TEXT(url=sub_links[title][0], text=request.text)
                    try:
                        result_dict = task.main()
                    except Exception:
                        count_for_cant_request += 1
                    else:
                        if int(result_dict['state']) == 1:
                            # 　为1表示正常提取
                            self.use_browser = False
                            return  # 但凡出现能够完全正常识别的情况，直接返回
                        elif result_dict['attachment']:
                            continue
                        else:
                            count_for_cant_request += 1
    
    async def open_page(self):
        error_info = ''
        self.page = await self.browser.newPage()
        other_page = await self.browser.pages()
        for page in other_page:
            if page != self.page:
                await page.close()  # 关闭其他无关页面
        await self.page.evaluateOnNewDocument(
            '''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }''')
        await self.page.evaluateOnNewDocument('''() =>{ window.navigator.chrome = { runtime: {},  }; }''')
        await self.page.evaluateOnNewDocument(
            '''() =>{ Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] }); }''')
        await self.page.setUserAgent(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
        await self.page.setRequestInterception(True)
        self.page.on('request', request_check)  # 不加载图片和媒体等
        self.page.on('dialog', handle_dialog)  # 关闭弹窗
        if not self.action_pattern:
            await asyncio.wait([self.page.goto(self.target_url), self.page.waitForNavigation(timeout=10 * 1000)])
        else:  # 没有target_url的时候处理raw_url
            await asyncio.wait([self.page.goto(self.target_url), self.page.waitForNavigation(timeout=10 * 1000)])
            if not self.action_pattern:
                error_info = u'缺失path值'
                return False, error_info
            elif self.action_pattern[0] == u'/':
                button = await self.page.xpath(self.action_pattern)
            else:
                button = await self.page.xpath('//*[contains(text(),"{}")]'.format(self.action_pattern))
            if not button:
                return False, u'找不到button'
            try:
                await button[0].click()
                await asyncio.sleep(3)
            except Exception as e:
                error_info = u'打开网页过程中出现问题 ' + str(e)
                return False, error_info
        return True, error_info
    
    async def get_next_button(self, frame_list, index, page_num):
        if self.next_button:
            xpath = self.next_button
        else:
            xpath = from_xpath_case_to_xpath(self.xpath_case, page_num)
        for frame in [frame_list[index]] + frame_list:
            try:
                button_list = await frame.raw_frame.xpath(xpath)
                # button_list = await self.page.xpath(xpath)
                if not button_list:
                    continue
                else:
                    return button_list[0]
            except Exception:
                continue
        return None
    
    async def get_cookie(self):
        cookies_list = await self.page.cookies()
        cookies = ''
        for cookie in cookies_list:
            str_cookie = '{0}={1};'.format(cookie.get('name'), cookie.get('value'))
            cookies += str_cookie
        # 将cookie 放入 cookie 池 以便多次请求 封账号 利用cookie 对搜索内容进行爬取
        return cookies
    
    async def get_frame(self):  # frame切换查找
        frame_list = list()
        for frame in self.page.frames:
            my_frame = Frame(frame, self.item_pattern)
            await my_frame.init()
            frame_list.append(my_frame)
        return frame_list
    
    def find_final_sub_url_list(self, tmp_list):
        # 从各个frame返回的结果里寻找最终的子链接列表,index标识了存有数据表的frame标签
        max_len, index = 0, 0
        final_dict = {}
        if not tmp_list:
            return final_dict, index
        # 按子链接长度和筛选
        for i in range(len(tmp_list)):
            length = sum([len(item) for item in list(tmp_list[i].keys())])
            if length > max_len:
                max_len = length
                final_dict = tmp_list[i]
                index = i
        return {title: final_dict[title] for title in list(final_dict.keys()) if
                title not in self.sub_url_already_crawl}, index
    
    async def turn_page(self, frame_list, page_num, item_list):
        flag = False
        xpath = from_xpath_case_to_xpath(self.xpath_case, page_num)
        js_func = 'result = document.evaluate("{xpath}", document, null, XPathResult.ANY_TYPE, null);' \
                  'node = result.iterateNext();' \
                  'node.target = "";' \
                  'node.click();'.format(xpath=xpath)
        for frame in frame_list:
            try:
                await frame.raw_frame.evaluate(js_func)
            except Exception:
                continue
            else:
                flag = True
                await asyncio.sleep(3)
                break
        if flag:
            await self.wait_for_change(item_list, max_retries=6)
            return True
        else:
            return False
    
    async def try_to_get_sub_url(self, frame_list):
        tmp_item_list = []
        for frame in frame_list:
            tmp_item_list.append(frame.find_sub_url(bool(self.date_type)))
        # index 用来指示含有数据的frame的序号
        new_sub_url, index = self.find_final_sub_url_list(tmp_item_list)
        # if self.mode == 'debug':
        return new_sub_url, index
    
    async def manager(self):
        self.browser = await init_browser()
        state, error_info = await self.open_page()
        if not state:
            self.status_list[0]['status'], self.status_list[0]['info'] = 0, error_info
            await self.browser.close()
            return
        retry_times = 0  # 轮询计数
        i = 0  # 循环计数
        while i < 2:
            i += 1
            # 获取frame列表
            frame_list = await self.get_frame()
            # 寻找翻页和子链接
            try:
                new_sub_url, index = await self.try_to_get_sub_url(frame_list)
                sub_urls_copy = copy.deepcopy(new_sub_url)
            except Exception as e:
                error_info = u'获取子链接过程出错' + str(e)
                self.status_list[1]['status'], self.status_list[1]['info'] = 0, error_info
                await self.browser.close()
                return
            if not new_sub_url:
                # 翻页前后没变化
                i -= 1  # 避免页面重复增加
                if retry_times < 5:
                    retry_times += 1
                    await asyncio.sleep(1)
                    continue
                else:
                    self.status_list[5]['status'], self.status_list[5]['info'] = 2, '网页解析终止在第{}页'.format(i)
                    await self.browser.close()
                    return
            else:
                retry_times = 0
            if i == 1:  # 进入到测试环节
                # 只要还没找到xpath_case, 就寻找一遍，注意寻找的时候遵循原则先从数据框开始
                self.xpath_case = find_xpath_case_in_frames(frame_list, index)
                try:
                    self.test_request(new_sub_url)
                except Exception as e:
                    error_info = u'检测解析链接方法时出现问题 ' + str(e)
                    self.status_list[3]['status'], self.status_list[3]['info'] = 0, error_info
                    self.use_browser = False
            try:
                frame_list = await self.parse_detail(new_sub_url, frame_list, index)
            except Exception as e:
                error_info = u'子链接解析过程存在问题 ' + str(e)
                self.status_list[4]['status'], self.status_list[4]['info'] = 0, error_info
                await self.browser.close()
                return
            try:
                state = await self.turn_page(frame_list, i, sub_urls_copy)
                if not state:
                    await self.browser.close()
                    return
            except Exception:
                await self.browser.close()
                return
        await self.browser.close()