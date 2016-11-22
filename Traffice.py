# -*- coding: utf-8 -*-


import os
import datetime
import time
import thread
import sqlite3

class Traffice(object):
    def __init__(self):
        self.port_traffic_dict=[]
        # 配置文件名
        self.conf_file_name = 'portlist.conf'
        # 取值间隔 秒
        self.sleep_time = 30
        # 日志写入间隔
        self.logIntenval = 300
        # 主机ip
        self.host_ip = ''
        # 数据库
        self.dbConn = sqlite3.connect('flow.db',check_same_thread = False)

    def port_traffic(self):
        if os.path.exists(self.conf_file_name):
            # 读取配置文件
            with open(self.conf_file_name, 'r') as f:
                for i in f.readlines():
                    i = i.strip()
                    self.port_traffic_dict.append(i)
                    v=self.dbConn.execute("SELECT port, flow from FlowLog WHERE port="+i)
                    if v.rowcount==-1:
                        self.dbConn.execute(
                            "INSERT INTO FlowLog (port,logDate,flow) VALUES ({0}, {1}, 0)".format(i, str(int(time.time()))))
                        self.dbConn.commit()

    @staticmethod
    def shell_command(command):
        return os.popen(command)

    def iptables_rules(self):
        """清空规则并添加规则"""
        traffic_f = 'iptables -F OUTPUT'
        # 清空OUTPUT链规则
        self.shell_command(traffic_f)
        # 添加规则
        for k in self.port_traffic_dict:
            add_rules = 'iptables -A OUTPUT -s %s/32 -p tcp -m tcp --sport %d' % (self.host_ip, int(k))
            self.shell_command(add_rules)

    def traffic_sum(self):
        """获取流量值并相加放入字典"""
        for k in self.port_traffic_dict:
            # 获取流量shell语句
            o = "iptables -nvxL -t filter |grep -w 'spt:%d' |awk -F' ' '{print $2}'" % int(k)
            # 获取流量值
            result = self.shell_command(o)
            result_str = result.read()
            if result_str:
                try:
                    k_traffic = int(result_str)
                except ValueError:
                    k_traffic = 0
            else:
                k_traffic = 0

            # 添加到数据库

            self.dbConn.execute("INSERT INTO FlowLog (port,logDate,flow) VALUES ({0}, {1}, {2})".format(k, str(int(time.time())),k_traffic))
            self.dbConn.commit()

    def dbTableCreate(self):
        '''创建数据库表'''
        try:
            self.dbConn.execute("CREATE TABLE FlowLog(port int,logDate timestamp, flow int)")
            self.dbConn.commit()
            print "Table created successfully"
        except:
            print "Table is exist"


    def run(self):
        # 读取配置或临时文件 获取端口 流量字典
        self.dbTableCreate()
        self.port_traffic()
        while True:
            # 写入间隔控制
            for _ in range(self.logIntenval):
                # 清空规则并添加规则
                self.iptables_rules()
                # 休眠等结果
                time.sleep(self.sleep_time)
                # 获取流量值并写入数据库
                self.traffic_sum()

    def threadRun(self):
        t = thread.start_new_thread(self.run,())