class Environment:
    def __init__(self):
        '''
        进行初始化环境
        '''
        pass

    def step(self, action:list):
        '''
        action = [(data:string, id:int), ...]
        表示用户id进行了data中的一些操作
        return_information:list
        = [(data:string, id:int), (data:string, id:int), ... ]
        其中data表示要返回的数据，id表示player对应的id
        '''
        pass

    def reset(self):
        '''
        重置当前游戏环境
        '''
        pass

    def getEnvironment(self):
        '''
        获取当前所有信息
        '''
        pass

    def state(self, round:int):
        '''
        :param round 当前回合数
        制作所有要发送给目标单位的信息
        格式为
        [(data:string, id:int), ...]
        id 表示目标player的id
        string 传输内容
        '''
        pass

    def isEnd(self):
        '''
        @return: bool 表示是否结束
        '''
        pass