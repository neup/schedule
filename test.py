# -*-coding: utf-8 -*-
import schedule

roomName = raw_input('请输入教室的名字:\n')

r = schedule.getFutureCoursesByRoom(roomName.decode('utf-8'))
print r
