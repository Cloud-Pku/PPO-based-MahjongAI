import json
import random
import time
import pickle

# 全局开始时间
t0 = time.time()


def parse_input(full_input):

    # 解析读入的JSON
    if "data" in full_input:
        my_data = full_input["data"]; # 该对局中，上回合该Bot运行时存储的信息
    else:
        my_data = None

    # 分析自己收到的输入和自己过往的输出，并恢复状态
    my_cards = []   # card 列表
    avail_cards = []    # 当前可以打的牌列表, 排除吃碰杠之后的死牌
    last_card = None    # 上回合打出的牌
    all_requests = full_input["requests"]
    all_responses = full_input["responses"]
    for ix in range(len(all_requests)):     # 因为当前turn也可能新增牌(IX=2)，所以最后一轮也得算
        myInput = all_requests[ix].strip() # i回合我的输入
        #myOutput = all_responses[ix].strip() # i回合我的输出
        
        if ix == 0:     # 第一轮只需要记录自己的ID
            myID = int(myInput.split(' ')[1])
        elif ix == 1:   # 第二轮记录初始牌
            myInput = myInput.split(' ')[5:]    # 忽略花牌
            for cur_card in myInput:
                my_cards.append(cur_card)
                avail_cards.append(cur_card)
        else:   # 开始对局, 恢复局面
            myInput = myInput.split(' ')
            cur_index = int(myInput[0])
            if cur_index == 2:  # 自己摸到了一张牌
                my_cards.append(myInput[1])
                avail_cards.append(myInput[1])
            if cur_index == 3:  # draw/chi/peng/gang
                cur_id = int(myInput[1])
                if cur_id == myID:  # 自己做的动作，所以要更新牌型
                    if myInput[2] == 'PLAY':
                        my_cards.remove(myInput[3])
                        avail_cards.remove(myInput[3])
                    elif myInput[2] == 'PENG':
                        #assert(False)
                        my_cards.append(last_card)
                        # 碰的刻子之后不能打
                        avail_cards.remove(last_card)
                        avail_cards.remove(last_card)
                        my_cards.remove(myInput[3])
                        avail_cards.remove(myInput[3])
                    elif myInput[2] == 'CHI':
                        #assert(False)
                        my_cards.append(last_card)
                        avail_cards.append(last_card)
                        # 吃的那个顺子之后都不能打了
                        mid = myInput[3]
                        mid_num = int(mid[1])
                        avail_cards.remove(mid[0]+str(mid_num-1))
                        avail_cards.remove(mid)
                        avail_cards.remove(mid[0]+str(mid_num+1))
                        my_cards.remove(myInput[4])
                        avail_cards.remove(myInput[4])
                    elif myInput[2] == 'GANG':
                        #assert(False)
                        avail_cards.remove(last_card)
                        avail_cards.remove(last_card)
                        avail_cards.remove(last_card)
                    elif myInput[2] == 'BUGANG':
                        #assert(False)
                        pass
            last_card = myInput[-1]
    
    ret = {
        'turn_id': len(all_requests),
        'data': my_data,
        'id': myID,
        'cards': sorted(my_cards),
        'avail_cards': sorted(avail_cards),
        'cur_request': all_requests[-1].strip().split(' '),
    }
    return ret


def do_early_pass(dat):
    # 有些request只能pass，直接返回了就行
    myInput = dat['cur_request']
    cur_index = int(myInput[0])

    if cur_index == 2:
        # 摸到一张牌，需要做进一步决策，所以不pass
        return 'self_play'
    if cur_index == 3:
        # 别人打出一张牌，或者吃碰杠后打出一张牌，需要做进一步决策，也不pass
        cur_id = int(myInput[1])
        cur_action = myInput[2]
        if cur_id != dat['id'] and cur_action in ['PLAY', 'PENG', 'CHI']:
            return 'chi_peng_gang'
    
    # 否则都直接pass即可
    print(json.dumps({"response":"PASS", 'debug': [" ".join(dat['cards']), time.time()-t0]}))
    exit(0)


def select_action(dat):

    ########################################################
    ########################################################
    ####           若修改决策算法修改这里即可            ####
    ####   如需额外信息修改parse_input中增加返回信息即可  ####
    ########################################################
    ########################################################

    state = dat['state']
    debug = {
        'cards': " ".join(dat['cards']),
        'avail_cards': " ".join(dat['avail_cards']),
        'elapsed_time': time.time()-t0,
    }
    if state == 'self_play':
        # 出牌算法: 随机从可出的牌里面选择
        play_card_selected = random.choice(dat['avail_cards'])
        print(json.dumps({"response":"PLAY {}".format(play_card_selected), 'debug': debug}))
    else:
        print(json.dumps({"response":"PASS", 'debug': debug}))
    exit(0)


def main():
    full_input = json.loads(input())
    ret = parse_input(full_input)
    state = do_early_pass(ret)
    ret['state'] = state
    select_action(ret)


if __name__ == "__main__":
    main()