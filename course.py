import json

import re
from requests import Session
from config import *
from pyquery import PyQuery as pq


class Course():
    def __init__(self):
        self.session = Session()
        self.username = USERNAME
        self.password = PASSWORD
        self.courses = COURSES
        self.ids = []
    
    def login(self):
        print('正在登录')
        url = {
            'base_url': 'http://onestop.ucas.ac.cn/home/index',
            'login_url': 'http://onestop.ucas.ac.cn/Ajax/Login/0'
        }
        self.headers = {
            'Host': 'onestop.ucas.ac.cn',
            'Connection': 'keep-alive',
            'Referer': 'http://onestop.ucas.ac.cn/home/index',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        data = {
            'username': self.username,
            'password': self.password,
            'remember': 'checked',
        }
        
        html = self.session.post(
            url['login_url'], data=data, headers=self.headers).text
        res = json.loads(html)
        if not res['f']:
            print('用户名或密码不正确')
        else:
            self.session.get(res['msg'])
            url = 'http://sep.ucas.ac.cn/portal/site/226/821'
            r = self.session.get(url, headers=self.headers)
            try:
                code = re.findall(r'"http://jwxk.ucas.ac.cn/login\?Identity=(.*)"', r.text)[0]
            except IndexError:
                print('登录有问题')
            
            url = "http://jwxk.ucas.ac.cn/login?Identity=" + code
            self.headers['Host'] = "jwxk.ucas.ac.cn"
            self.session.get(url, headers=self.headers)
    
    def enter(self):
        url = 'http://jwxk.ucas.ac.cn/courseManage/main'
        r = self.session.get(url, headers=self.headers)
        html = r.text
        if '查看个人课表' in html:
            print('登录成功')
        else:
            print('登录失败')
        doc = pq(html)
        labels = doc('#regfrm2 label')
        for label in labels.items():
            self.ids.append('deptIds=' + label.attr('for').replace('id_', ''))
        data = '&'.join(self.ids)
        data += '&sb=0'
        action = 'http://jwxk.ucas.ac.cn/' + doc('#regfrm2').attr('action')
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'http://jwxk.ucas.ac.cn',
            'Referer': 'http://jwxk.ucas.ac.cn/courseManage/main',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        }
        print('正在查询所有可选的课')
        r = self.session.post(action, data=bytes(data, 'utf-8'), headers=headers)
        return r.text
    
    def select(self, html, course):
        
        doc = pq(html)
        action = 'http://jwxk.ucas.ac.cn/' + doc('#regfrm').attr('action')
        course_id = course.get('id')
        course_tag = course.get('tag')
        sid = re.search(r'<span id="courseCode_(.*?)">' + course_id + '</span>', html)
        if sid:
            sid = sid.group(1)
            post_data = '&'.join(self.ids)
            post_data += '&sids=' + sid
            if course_tag:
                post_data += '&did_' + sid + '=' + sid
            print('选课中', sid, course_id)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'http://jwxk.ucas.ac.cn',
                'Referer': 'http://jwxk.ucas.ac.cn/courseManage/main',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
            }
            try:
                html = self.session.post(action, data=bytes(post_data, 'utf-8'), headers=headers, timeout=20).text
                if html.find('选课成功') != -1:
                    print('选课成功')
                else:  # 一般是课程已满
                    doc = pq(html)
                    result = doc('#loginError').text()
                    print(result)
                    if '重新登录' in result:
                        self.main()
            except:
                print('出现异常')
    
    def main(self):
        self.login()
        html = self.enter()
        count = 1
        while True:
            print('正在进行第', count, '轮刷课')
            for course in self.courses:
                self.select(html, course)
            count += 1


if __name__ == '__main__':
    course = Course()
    course.main()
