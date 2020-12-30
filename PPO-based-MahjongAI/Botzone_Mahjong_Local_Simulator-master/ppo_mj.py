import numpy as np
import json
import copy
from MahjongGB import MahjongFanCalculator

from mahjong_env import MahjongEnvironment


if __name__ == '__main__':
    env = MahjongEnvironment()
    env.reset()


    env_state = env.state()
    
    print(env.state())
    print(env.state())
    #while not env.isEnd():
        

