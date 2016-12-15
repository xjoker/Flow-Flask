# -*- coding: utf-8 -*-
from flask import Flask,render_template
from Traffice import Traffice
import time
import calendar
import datetime

app = Flask(__name__)

traffic = Traffice()
# 主机IP
traffic.host_ip = '127.0.0.1'


def timestamp_datetime(value):
    format = '%Y-%m-%d %H:%M:%S'
    value = time.localtime(value)
    dt = time.strftime(format, value)
    return dt


def datetime_timestamp(dt):
    time.strptime(dt, '%Y-%m-%d %H:%M:%S')
    s = time.mktime(time.strptime(dt, '%Y-%m-%d %H:%M:%S'))
    return int(s)


@app.route('/')
def hello_world():
    nowMonthFlow=[]
    lastMonthFlow = []
    lastRepoTime=""
    today = datetime.date.today()
    # 获得数据库内最后一条数据的更新时间
    for row in traffic.dbConn.execute("SELECT * FROM FlowLog ORDER BY logDate DESC LIMIT 1"):
        lastRepoTime=str(timestamp_datetime(row[1]))

    # 本月计算
    _, last_day_num = calendar.monthrange(today.year, today.month)
    nowStartTime=datetime_timestamp("{0}-{1}-1 00:00:00".format(int(today.year),int(today.month)))
    nowStopTime=datetime_timestamp("{0}-{1}-{2} 23:59:59".format(int(today.year),int(today.month),int(last_day_num)))

    portList=traffic.dbConn.execute("SELECT distinct  port from FlowLog;")

    for i in portList:
        nMonth = traffic.dbConn.execute(
            "SELECT port, logDate,sum(flow) from FlowLog WHERE logDate>{0} and logDate<{1} and port={2}".format(nowStartTime,nowStopTime,i[0]))
        for b in nMonth:
            tr=round((b[2] / 1024 / 1024), 2)
            nowMonthFlow.append([b[0],tr,(tr/1024)*1+8]);


    # 上月计算
    lastMonth = datetime.date(day=1, month=today.month, year=today.year) - datetime.timedelta(days=1)

    lastStartTime = datetime_timestamp("{0}-{1}-1 00:00:00".format(int(lastMonth.year), int(lastMonth.month)))
    lastStopTime = datetime_timestamp("{0}-{1}-{2} 23:59:59".format(int(lastMonth.year), int(lastMonth.month), int(lastMonth.day)))

    for i in portList:
        lMonth = traffic.dbConn.execute(
            "SELECT port, logDate,sum(flow) from FlowLog WHERE logDate>{0} and logDate<{1} and port={2}".format(lastStartTime,lastStopTime,i[0]))
        if lMonth[0]:
            for b in lMonth:
                tr = round((b[2] / 1024 / 1024), 2)
                lastMonthFlow.append([b[0], tr, (tr / 1024) * 1 + 8]);


    return render_template('index.html',nowMonthFlow=nowMonthFlow,lastMonthFlow=lastMonthFlow,lastRepoTime=lastRepoTime)

if __name__ == '__main__':
    traffic.threadRun()
    app.run(host='0.0.0.0',port=5000,debug=False)