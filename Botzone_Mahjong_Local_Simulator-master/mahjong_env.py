import numpy as np
import json
import copy
from MahjongGB import MahjongFanCalculator

def prevTile(x):
    tile_id = int(x[1:2])
    return x[0:1] + str(tile_id-1)

def backTile(x):
    tile_id = int(x[1:2])
    return x[0:1] + str(tile_id+1)

class MahjongEnvironment:
    def __init__(self):
        self.is_end = True
        self.result = -1
    
    def step(self, action:list):
        '''
        用于update状态
        @param: action:
            example:
                [("PASS", 0), ("PASS", 1), ("PASS", 2), ("PASS", 3)]
                0/1/2/3分别表示玩家的id
        '''
        new_action = []
        for x in action:
            print(x[0])
            tmp = json.loads(x[0])
            new_action.append((tmp['response'], x[1]))
        action = new_action
        if self.game_state[:9] == "NEED_PASS":
            if self.game_state != "NEED_PASS":
                '''
                这里可以胡牌
                '''
                for i in range(4):
                    if action[i][0][:2] == "HU":
                        player_id = action[i][1]
                        tmp_hand = copy.deepcopy(self.hand[player_id])
                        try:
                            result = MahjongFanCalculator(
                                tuple(self.pack[player_id]),
                                tuple(tmp_hand),
                                self.disc_tile,
                                len(self.flower[player_id]),
                                False,
                                self.desk.count(self.disc_tile) == 3,
                                False, # 这里没完全理解到这个参数啥意思。。
                                len(self.wall) == 0,
                                player_id,
                                self.wind
                            )
                            sumv = 0
                            for x in result:
                                sumv += x[0]
                            if sumv < 8:
                                raise BaseException(f"{player_id} 进行了错胡")
                        except:
                            raise BaseException(f"{player_id} 进行了错胡")
                        self.is_end = True
                        self.result = player_id
                        return
            for i in range(4):
                if action[i][0][:4] != "PASS":
                    raise BaseException(f"{action[i][1]} 你应该输出PASS")
            self.game_state = ""
        elif self.game_state == "DRAW":
            for i in range(4):
                if action[i][0][:4] == "PASS":
                    if action[i][1] == (self.prev_player+1)%4:
                        raise BaseException(f"{action[i][1]} 你不应该输出PASS"+str(action[i]))
                    continue
                if action[i][1] != (self.prev_player+1)%4:
                    raise BaseException(f"{action[i][1]}你现在应该输出PASS")
                player_id = action[i][1]
                if action[i][0][:4] == "PLAY":
                    self.game_state = "PLAYED"
                    self.player_id = player_id
                    self.disc_tile = action[i][0][5:7]
                    if self.hand[player_id].count(self.disc_tile) == 0:
                        raise BaseException(f"{player_id} 试图discard他没有的牌")
                    self.hand[player_id].pop(self.hand[player_id].index(self.disc_tile))
                    return
                elif action[i][0][:4] == "GANG":
                    self.game_state = "GANGED"
                    self.player_id = player_id
                    self.disc_tile = action[i][0][5:7]
                    if self.hand[player_id].count(self.disc_tile) < 4:
                        raise BaseException(f"{player_id} 试图gang他没有的牌")
                    for j in range(4): self.hand[player_id].pop(self.hand[player_id].index(self.disc_tile))
                    self.pack[player_id].append(("GANG", self.disc_tile, 0))
                    return
                elif action[i][0][:4] == "BUGANG":
                    self.game_state = "BUGANGED"
                    self.player_id = player_id
                    self.disc_tile = action[i][0][7:9]
                    if self.hand[player_id].count(self.disc_tile) == 0:
                        raise BaseException(f"{player_id} 试图bugang他没有的牌")
                    self.hand[player_id].pop(self.hand[player_id].index(self.disc_tile))
                    ok = False
                    for i in range(len(self.pack[player_id])):
                        if self.pack[player_id][i][1] == self.disc_tile:
                            self.pack[player_id][i][0] = "GANG"
                            ok = True
                            break
                    if not ok:
                        raise BaseException(f"{player_id} 试图bugang他没有的PENG")
                    return
                elif action[i][0][:4] == "HU":
                    tmp_hand = copy.deepcopy(self.hand[player_id])
                    tmp_hand.pop(tmp_hand.index(self.last_draw))
                    try:
                        result = MahjongFanCalculator(
                            tuple(self.pack[player_id]),
                            tuple(tmp_hand),
                            self.last_draw,
                            len(self.flower[player_id]),
                            True,
                            self.desk.count(self.last_draw) == 3,
                            self.ganged == 1,
                            len(self.wall) == 0,
                            player_id,
                            self.wind
                        )
                        sumv = 0
                        for x in result:
                            sumv += x[0]
                        if sumv < 8:
                            raise BaseException(f"{player_id} 进行了错胡")
                    except Exception as err:
                        raise BaseException(f"{player_id} 进行了错胡")
                    self.is_end = True
                    self.result = player_id
                    return
        elif self.game_state == "PLAYED_WAITING":
            for i in range(len(action)):
                player_id = action[i][1]
                if action[i][0][:2] == "HU":
                    tmp_hand = copy.deepcopy(self.hand[player_id])
                    try:
                        result = MahjongFanCalculator(
                            tuple(self.pack[player_id]),
                            tuple(tmp_hand),
                            self.disc_tile,
                            len(self.flower[player_id]),
                            False,
                            self.desk.count(self.disc_tile) == 3,
                            False,
                            len(self.wall) == 0,
                            player_id,
                            self.wind
                        )
                        sumv = 0
                        for x in result:
                            sumv += x[0]
                        if sumv < 8:
                            raise BaseException(f"{player_id} 进行了错胡 {sumv}")
                    except:
                        raise BaseException(f"{player_id} 进行了错胡")
                    self.is_end = True
                    self.result = player_id
                    return
            for i in range(len(action)):
                player_id = action[i][1]
                if action[i][0][:4] == "PENG":
                    self.desk.pop(self.desk.index(self.disc_tile))
                    self.pack[player_id].append(("PENG", self.disc_tile, (player_id-self.player_id+4)%4))
                    if self.hand[player_id].count(self.disc_tile) < 2:
                        raise BaseException(f"{player_id} 试图peng他没有的牌")
                    for j in range(2): self.hand[player_id].pop(self.hand[player_id].index(self.disc_tile))
                    self.disc_tile = action[i][0].split(' ')[1]
                    if self.hand[player_id].count(self.disc_tile) == 0:
                        raise BaseException(f"{player_id} 试图在peng的时候discard他没有的牌")
                    self.hand[player_id].pop(self.hand[player_id].index(self.disc_tile))
                    self.player_id = player_id
                    self.game_state = "PENGED"
                    return
                elif action[i][0][:4] == "GANG":
                    self.desk.pop(self.desk.index(self.disc_tile))
                    self.pack[player_id].append(("GANG", self.disc_tile, (player_id-self.player_id+4)%4))
                    if self.hand[player_id].count(self.disc_tile) < 3:
                        raise BaseException(f"{player_id} 试图gang他没有的牌")
                    for j in range(3): self.hand[player_id].pop(self.hand[player_id].index(self.disc_tile))
                    self.disc_tile = ""
                    self.player_id = -1
                    self.game_state = "GANGED"
                    return
            for i in range(len(action)):
                player_id = action[i][1]
                if action[i][0][:3] == "CHI":
                    self.desk.pop(self.desk.index(self.disc_tile))
                    if (player_id+3)%4 != self.player_id:
                        raise BaseException(f"{player_id} 试图从错误的位置进行吃牌")
                    chi_tile = action[i][0][4:6]
                    out_tile = action[i][0][7:9]
                    self.hand[player_id].append(self.disc_tile)
                    if self.hand[player_id].count(out_tile) == 0:
                        raise BaseException(f"{player_id} 试图使用他没有的牌 {out_tile}")
                    if self.hand[player_id].count(chi_tile) == 0:
                        raise BaseException(f"{player_id} 试图使用他没有的牌 {chi_tile}")
                    if self.hand[player_id].count(prevTile(chi_tile)) == 0:
                        raise BaseException(f"{player_id} 试图使用他没有的牌 {prevTile(chi_tile)}")
                    if self.hand[player_id].count(backTile(chi_tile)) == 0:
                        raise BaseException(f"{player_id} 试图使用他没有的牌 {backTile(chi_tile)}")
                    self.hand[player_id].pop(self.hand[player_id].index(out_tile))
                    self.hand[player_id].pop(self.hand[player_id].index(chi_tile))
                    self.hand[player_id].pop(self.hand[player_id].index(prevTile(chi_tile)))
                    self.hand[player_id].pop(self.hand[player_id].index(backTile(chi_tile)))

                    number = 2
                    if prevTile(chi_tile) == self.disc_tile: number = 1
                    if backTile(chi_tile) == self.disc_tile: number = 3
                    
                    self.pack[player_id].append(("CHI", chi_tile, number))
                    self.chi_tile = chi_tile
                    self.disc_tile = out_tile
                    self.player_id = player_id
                    self.game_state = "CHIED"
                    return
            self.game_state = ""
            self.player_id = -1
            return

    def getTile(self, remove=True):
        tile = np.random.choice(self.wall)
        if remove:
            self.wall.pop(self.wall.index(tile))
        return tile

    def reset(self):
        self.wall = []
        self.wall += ["W"+str(i) for i in range(1, 10)]
        self.wall += ["W"+str(i) for i in range(1, 10)]
        self.wall += ["W"+str(i) for i in range(1, 10)]
        self.wall += ["W"+str(i) for i in range(1, 10)]
        self.wall += ["B"+str(i) for i in range(1, 10)]
        self.wall += ["B"+str(i) for i in range(1, 10)]
        self.wall += ["B"+str(i) for i in range(1, 10)]
        self.wall += ["B"+str(i) for i in range(1, 10)]
        self.wall += ["T"+str(i) for i in range(1, 10)]
        self.wall += ["T"+str(i) for i in range(1, 10)]
        self.wall += ["T"+str(i) for i in range(1, 10)]
        self.wall += ["T"+str(i) for i in range(1, 10)]
        self.wall += ["F"+str(i) for i in range(1, 5)]
        self.wall += ["F"+str(i) for i in range(1, 5)]
        self.wall += ["F"+str(i) for i in range(1, 5)]
        self.wall += ["F"+str(i) for i in range(1, 5)]
        self.wall += ["J"+str(i) for i in range(1, 4)]
        self.wall += ["J"+str(i) for i in range(1, 4)]
        self.wall += ["J"+str(i) for i in range(1, 4)]
        self.wall += ["H"+str(i) for i in range(1, 9)]
        self.is_end = False
        self.pack = [[] for i in range(4)]
        self.hand = [[] for i in range(4)]
        self.flower = [[] for i in range(4)]
        self.wind = np.random.randint(0, 4)
        for j in range(13):
            for i in range(4):
                while True:
                    tile = self.getTile()
                    if tile[0:1] == 'H':
                        self.flower[i].append(tile)
                    else:
                        self.hand[i].append(tile)
                        break
        self.game_state = ""
        self.prev_player = 3 # 表示谁上一次打出了最后一张牌
        self.round = 0
        self.desk = []
        self.ganged = 10 # 随便设一个不可能的表示当前和GANG间隔了多少回合
    
    def getEnvironment(self):
        return (self.hand, self.wall)
    
    def removeTile(self, player_id, tile):
        self.hand[player_id].pop(self.hand[player_id].index(tile))

    def state(self):
        '''
        用于给出当前输入
        @return:
            example:
                [("0 0 1",id), ("0 1 1",id), ("0 2 1",id), ("0 3 1",id)]
                分别表示返回给四个bot的信息，其中id对应了这个信息要返回给哪一个bot
        '''
        self.ganged += 1
        if len(self.wall) == 0:
            self.result = -1
            self.is_end = True
            return []
        if self.round == 0: # 发送第一类信息
            ret = []
            for i in range(4):
                tmp = f"0 {i} {self.wind}"
                out = json.dumps({"requests" : [tmp]})
                ret.append((out, i))
            self.round += 1
            self.game_state = "NEED_PASS"
            return ret
        elif self.round == 1: # 发送第二类信息
            ret = []
            flower_data = (' '.join([str(len(self.flower[i])) for i in range(4)])) + " "
            for i in range(4):
                self_flower_data = ' '.join(self.flower[i])
                self_tile = ' '.join(self.hand[i])
                tmp_data = "1 " + flower_data + self_tile + " " + self_flower_data
                ret.append((tmp_data, i))
            self.round += 1
            self.game_state = "NEED_PASS"
            return ret
        if self.game_state == "":
            '''
            某人需要进行一次摸牌
            '''
            current_player = (self.prev_player+1)%4
            tile = self.getTile()
            if tile[0:1] == 'H':
                self.game_state = "NEED_PASS"
                ret = []
                self.flower[current_player].append(tile)
                for i in range(4):
                    ret.append((f"3 {current_player} BUHUA {tile}", i))
                return ret
            else:
                self.game_state = "DRAW"
                self.hand[current_player].append(tile)
                self.last_draw = tile
                ret = [(f"2 {tile}", current_player)]
                for i in range(4):
                    if i == current_player: continue
                    ret.append((f"3 {current_player} DRAW", i))
                return ret
        elif self.game_state == "GANGED":
            '''
            某人刚刚进行了一次杠牌
            '''
            self.prev_player = (self.player_id+3)%4
            self.game_state = "NEED_PASS"
            ret = []
            for i in range(4):
                ret.append((f"3 {self.player_id} GANG", i))
            self.ganged = 0
            return ret
        elif self.game_state == "PENGED":
            '''
            某人刚刚进行了一次碰牌
            '''
            self.prev_player = self.player_id
            self.game_state = "PLAYED_WAITING"
            ret = []
            for i in range(4):
                ret.append((f"3 {self.player_id} PENG {self.disc_tile}", i))
            self.desk.append(self.disc_tile)
            return ret
        elif self.game_state == "CHIED":
            '''
            某人刚刚吃了一下
            '''
            self.prev_player = self.player_id
            self.game_state = "PLAYED_WAITING"
            ret = []
            for i in range(4):
                ret.append((f"3 {self.player_id} CHI {self.chi_tile} {self.disc_tile}", i))
            self.desk.append(self.disc_tile)
            return ret
        elif self.game_state == "PLAYED":
            '''
            刚刚某人正常的打出了一张牌
            '''
            self.prev_player = self.player_id
            self.game_state = "PLAYED_WAITING"
            ret = []
            for i in range(4):
                ret.append((f"3 {self.player_id} PLAY {self.disc_tile}", i))
            self.desk.append(self.disc_tile)
            return ret
        elif self.game_state == "BUGANGED":
            '''
            刚刚某人补杠了一下
            '''
            self.prev_player = (self.player_id+3)%4
            self.game_state = "NEED_PASS_"
            ret = []
            for i in range(4):
                ret.append((f"3 {self.player_id} BUGANG {self.disc_tile}", i))
            self.ganged = 0
            return ret
        
    def isEnd(self):
        return self.is_end

if __name__ == '__main__':
    env = MahjongEnvironment()
    env.reset()

    print(env.state())
    env_state = env.state()
    
    print(env.state())
    #while not env.isEnd():
        






