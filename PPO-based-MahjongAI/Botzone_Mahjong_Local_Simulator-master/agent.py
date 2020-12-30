# -*- coding: utf-8 -*-
import numpy as np
import time
import os
import subprocess
import json
import sys
class Agent:
    '''
    bot包装器，负责创建、交互、监控、结束一个bot程序。
    它不会运行在独立的线程中，会被AI所阻塞。
    每一个bot应该是一个以bot名称命名的文件夹，文件夹下包含main.exe, main或者main.py作为执行文件
    :param name:AI的名称，这个名称应该与bot文件夹名称相同
    :param extra_params:list[]，包含你想在两个通信端口后方为bot运行指令追加的参数。
    '''
    def __init__(self, name:str, extra_params:list=[], offline=False):
        '''
        初始化函数
        :param name : AI的名字
        :param extra_params : 额外参数
        '''
        self.name = name
        self.extra_params = extra_params
        self.connected =  False
        # 换行符，在不同的os下区别对待
        self._crlf = '\r\n' if sys.platform == 'win32' else '\n'
        self.pipe_encoding = 'ascii' # 默认使用ascii编码，不能传输中文
        self.logname = f"bot[{self.name}]"
        self.offline = offline
        self.lastdata = {}

    def connect(self):
        '''
        启动bot程序并进行连接。
        :raise anyerror: 易爆
        '''
        base = os.path.dirname(os.path.dirname(__file__))
        base = os.path.join(base, 'ais')
        base = os.path.join(base, self.name)
        if os.path.exists(os.path.join(base, 'main.py')): 
            if os.name == 'nt': base = "python " + os.path.join(base, 'main.py')
            else: base = "python3 " + os.path.join(base, 'main.py')
        elif os.path.exists(os.path.join(base, 'main.exe')) and os.name == 'nt': base = os.path.join(base, 'main.exe')
        else: base = os.path.join(base, 'main')
        while True:
            try:
                self.p = subprocess.Popen(
                    base+' '+' '.join(self.extra_params),
                    shell=True,
                    stdin = subprocess.PIPE,
                    stdout = subprocess.PIPE,
                )
                break
            except IOError as e:
                print(str(e))
        self.connected = True

    def sendMessage (self, raw:str)->tuple:
        '''
        获得bot的决策，如果决策超时会log并抛出错误。
        会阻塞。
        :param raw: 该回合bot应该获得的字符串json信息
        '''
        if self.offline: self.connect()
        if not self.connected:
            raise Exception('bot并未连接，请先调用connect()函数！')
        if self.p.poll() is not None:
            raise Exception('bot挂之后使用了makeDecision')
        self.p.stdin.write((raw+self._crlf).encode(self.pipe_encoding))
        self.p.stdin.flush()
        if self.offline: self.connected = False
        res = ""
        for tim in range(20):
            try:
                res = self.p.stdout.readline(1024).decode(self.pipe_encoding)
            except:
                res = ""
            if res != "":
                break
        if res == "":
            raise BaseException("接收到了空白的消息")
        return res

    def terminate (self):
        '''
        强制关闭bot
        '''
        if self.p.poll() is None and self.offline==False:
            self.p.kill()
        self.connected = False

    def isAlive(self)->bool:
        '''
        检测bot是否仍在运行
        '''
        if self.offline: return True
        if not self.connected: return False
        if self.p.poll() is not None: 
            self.connected = False
        return self.connected
