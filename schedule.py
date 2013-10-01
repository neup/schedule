# -*-coding: utf-8 -*-
import os
import re
import MySQLdb
from datetime import date, time, datetime

if 'SERVER_SOFTWARE' in os.environ:
    onBAE = True
    from bae.core import const
else:
    onBAE = False

class Schedule(object):
    """docstring for Schedule
    TODO:
        1. 节假日串休时候要有特殊的逻辑来转换日期
        2. 查找教室名字的时候不能只用第一个字符来查，有更好的办法
    """

    dbUser = "root"
    dbHost = "127.0.0.1"
    dbPasswd = "654321"
    dbCharset = "utf8"
    dbName = "schedule_neu"
    dbPort = 3306
    startWeek = 34
    timeline = [time(8, 0), time(9,50), time(12, 0), time(15, 50),\
                time(17, 50), time(20, 20)]

    def __init__(self):
        super(Schedule, self).__init__()
        if onBAE:
            self.dbHost = const.MYSQL_HOST
            self.dbPort = int(const.MYSQL_PORT)
            self.dbUser = const.MYSQL_USER
            self.dbPasswd = const.MYSQL_PASS
        self.conn = MySQLdb.connect(
            host=self.dbHost,
            port=self.dbPort,
            charset=self.dbCharset,
            db=self.dbName,
            user=self.dbUser,
            passwd=self.dbPasswd)
        self.cur = self.conn.cursor()

    def _secureString(self, s):
        return MySQLdb.escape_string(s.encode('utf-8')).decode('utf-8')

    def _getBuildingName(self, s):
        return s[0]

    def _getRoomidFromName(self, queryString):
        '''get roomid from database by classroom's name'''
        queryString = self._secureString(queryString)
        feelLucky = self.cur.execute("select roomid from room where name \
            like '%%%s%%'" % queryString)
        if feelLucky > 0:
            # 直接能找到这个教室记录的话，直接返回roomid
            return self.cur.fetchone()[0]
        roomPattern = re.compile(r'^(?P<buildingName>.*?)(?P<roomNo>\d*)\D*$')
        result = roomPattern.search(queryString)
        roomDetail = result.groupdict()
        buildingName = self._getBuildingName(roomDetail['buildingName'])
        resultCount = self.cur.execute("select roomid, building, name from \
            room where name like '%%%s%%' and building like '%%%s%%'" % \
                                       (roomDetail['roomNo'], buildingName))
        if resultCount > 0:
            queryRoomNoSet = self.cur.fetchone()
            return queryRoomNoSet[0]

        return ''

    def _addDay(self, week, day):
        day += 1
        if day > 7:
            day = 1
            week += 1
        return (week, day)

    def _transTime(self, defaultDays=2):
        no = 0
        courses = []
        now = datetime.time(datetime.now())
        today = date.today()
        day = today.isoweekday()
        # 用相对于年初的周数减去这学期开学时的周数就是现在是第几周
        week = int(today.strftime("%W")) - self.startWeek
        for i in range(1, 6):
            if now < self.timeline[i]:
                no = i
                break
        if no == 0:
            # 对深夜的情况加以处理
            no = 1
            (week, day) = self._addDay(week, day)
        for i in range(0, defaultDays):
            if i == 0:
                for i in range(no, 7):
                    courses.append((week, day, i))
            else:
                (week, day) = self._addDay(week, day)
                for i in range(1, 7):
                    courses.append((week, day, i))
        return courses

    def _getFutureCoursesByRoomid(self, roomid, days=2):
        '''roomid is expected to be a string, eg.00204108'''

        result = []
        courses = self._transTime(days)
        for course in courses:
            (week, day, no) = course
            querySet = self.cur.execute("select * from schedule \
                where week=%d and day=%d and no=%d and roomid=%s" \
                                        % (week, day, no, str(roomid)))
            if querySet > 0:
                result.append(self.cur.fetchone())

        return result

    def _render(self, t):
        words = ''
        nowWeek = ''
        dayDict = {1: u'周一',
                   2: u'周二',
                   3: u'周三',
                   4: u'周四',
                   5: u'周五',
                   6: u'周六',
                   7: u'周日'}
        noDict = {1: u'第1-2节',
                  2: u'第3-4节',
                  3: u'第5-6节',
                  4: u'第7-8节',
                  5: u'第9-10节',
                  6: u'第11-12节'}
        for course in t:
            if nowWeek != course[2]:
                nowWeek = course[2]
                words += dayDict[nowWeek]
            words += noDict[course[3]] + u'是' + course[6]
            if course[7]:
                words += u'，任课教师是' + course[7]
            words += u'；'

        return words

    def closeSchedule(self):
        self.cur.close()
        self.conn.close()

    def getFutureCoursesByRoom(self, roomName, days=2):
        roomid = self._getRoomidFromName(roomName)
        courses = self._getFutureCoursesByRoomid(roomid, days)
        self.closeSchedule()
        return self._render(courses)

    @staticmethod
    def queryTest():
        s = Schedule()
        r = s.cur.execute("select * from room where id=650")
        print r
        print s._transTime()
        print s._getFutureCoursesByRoomid("00204108"), '\n'
        print s._getRoomidFromName(u"逸夫楼101")
        s.closeSchedule()

def getFutureCoursesByRoom(roomName, days=2):
    s = Schedule()
    return s.getFutureCoursesByRoom(roomName, days)

def main():
    pass

if __name__ == '__main__':
    main()
