import json
import random
import time
import pickle
from MahjongGB import MahjongFanCalculator


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
    pack = []       # 自己的明牌列表
    all_shown_cards = []    # 全局明牌列表，用于算番（和绝张）
    card_wall_remain = [21, 21, 21, 21]     # 记录每个人牌墙还有几张，用来算isLast判断海底捞月/妙手回春
    last_card = None    # 上回合打出的牌
    all_requests = full_input["requests"]
    all_responses = full_input["responses"]
    for ix in range(len(all_requests)):     # 因为当前turn也可能新增牌(IX=2)，所以最后一轮也得算
        myInput = all_requests[ix].strip() # i回合我的输入
        #myOutput = all_responses[ix].strip() # i回合我的输出
        
        if ix == 0:     # 第一轮只需要记录自己的ID
            myID = int(myInput.split(' ')[1])
            curQuan = int(myInput.split(' ')[2])
        elif ix == 1:   # 第二轮记录初始牌
            myInput = myInput.split(' ')[5:]    # 忽略花牌
            for cur_card in myInput:
                my_cards.append(cur_card)
                avail_cards.append(cur_card)
        else:   # 开始对局, 恢复局面
            myInput = myInput.split(' ')
            cur_index = int(myInput[0])
            all_shown_cards = add_all_shown_cards(all_shown_cards, myInput, last_card)

            if cur_index == 2:  # 自己摸到了一张牌
                my_cards.append(myInput[1])
                avail_cards.append(myInput[1])
                card_wall_remain[myID] -= 1     # 更新自己的牌墙
            
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
                        # 计算是谁给我的碰
                        src_id = int(all_requests[ix-1].strip().split(' ')[1])
                        src = (myID + 4 - src_id) % 4
                        # 加入明牌中
                        pack.append(['PENG', last_card, src])
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
                        # 判断第几张是上家供牌（last_card）
                        last_card_num = int(last_card[1])
                        src = 2 + last_card_num - mid_num
                        # 加入明牌中
                        pack.append(['CHI', mid, src])
                    elif myInput[2] == 'GANG':
                        #assert(False)
                        if int(all_requests[ix-1].strip().split(' ')[0]) == 2:     # 暗杠
                            avail_cards.remove(last_card)       # 之前摸了一张新的牌，杠了，所以四张牌都应从avail_cards中去除
                            my_cards.remove(last_card)          # 我们规定杠的牌不算手牌，所以手牌不包括这一张。不过其实my_cards没啥用，只是为了debug
                            src = 0     # 算番器的规则是暗杠的source是0，上下对是123
                        else:   # 明杠
                            # 明杠是拿来别人打出来的last_card，所以avail_cards删除现有的三张，my_cards没区别
                            src_id = int(all_requests[ix-1].strip().split(' ')[1])  # 计算是谁给我的杠
                            src = (myID + 4 - src_id) % 4
                        avail_cards.remove(last_card)
                        avail_cards.remove(last_card)
                        avail_cards.remove(last_card)
                        # 加入明牌中
                        pack.append(['GANG', last_card, src])
                    elif myInput[2] == 'BUGANG':    # 补杠
                        #assert(False)
                        avail_cards.remove(last_card)       # 摸了一张牌后补杠，这张牌无效了
                        my_cards.remove(last_card)          # 且由于是杠，这张牌不算手牌
                        check_peng_exist = False
                        for ix, cur_pack in enumerate(pack):
                            if cur_pack[0] == 'PENG' and cur_pack[1] == last_card:
                                pack[ix][0] = 'GANG'
                                check_peng_exist = True
                                break
                        assert(check_peng_exist)
                # 更新别人的牌墙
                if myInput[2] == 'DRAW':
                    card_wall_remain[cur_id] -= 1
            # 更新上一张牌，用以帮助恢复吃、碰、杠相关局面
            last_card = myInput[-1]
    
    last_is_gang = False
    if len(all_requests) > 2:
        request_before = all_requests[-2].strip().split(' ')
        if len(request_before) in (3, 4) and request_before[2] in ('GANG', 'BUGANG') and int(request_before[1]) == myID:
            last_is_gang = True
    ret = {
        'turn_id': len(all_requests),
        'data': my_data,
        'id': myID,
        'cards': sorted(my_cards),
        'avail_cards': sorted(avail_cards),
        'cur_request': all_requests[-1].strip().split(' '),
        'pack': pack,
        'quan': curQuan,
        'all_shown_cards': all_shown_cards,
        'last_is_gang': last_is_gang,
        'card_wall_remain': card_wall_remain,
    }
    return ret


def add_all_shown_cards(all_shown_cards, cur_request, last_card):
    # 更新全局明牌信息
    cur_index = int(cur_request[0])
    if cur_index != 3:  
        return all_shown_cards

    # 只需考虑 play/chi/peng/gang
    if cur_request[2] == 'PLAY':
        all_shown_cards.append(cur_request[3])
    elif cur_request[2] == 'PENG':
        # 碰的一张之前已经加入明牌中了（不论是 PLAY/PENG/CHI/BUGANG 打出的）
        all_shown_cards.append(last_card)
        all_shown_cards.append(last_card)
        # 又打出一张，也要加入明牌中
        all_shown_cards.append(cur_request[3])
    elif cur_request[2] == 'CHI':
        # 通过last_card和mid共同判断应该如何更新明牌
        # 只需加入mid-1, mid, mid+1再去掉last_card即可
        mid = cur_request[3]
        all_shown_cards.remove(last_card)        
        mid_num = int(mid[1])
        all_shown_cards.append(mid[0]+str(mid_num-1))
        all_shown_cards.append(mid)
        all_shown_cards.append(mid[0]+str(mid_num+1))
        # 打出的牌也要加入明牌，注意这里是第4项
        all_shown_cards.append(cur_request[4])
    elif cur_request[2] == 'GANG':
        # 需要分情况，明杠和暗杠
        if all_shown_cards.count(last_card) != 0:
            # 若为明杠，杠的那张牌是别人打出的，已经加入明牌里了，只需要单独加三张即可
            all_shown_cards.append(last_card)
            all_shown_cards.append(last_card)
            all_shown_cards.append(last_card)
        else:
            # 若为暗杠，不是明牌，啥都不干即可
            pass
    elif cur_request[2] == 'BUGANG':    # 补杠，之前的碰已经加入明牌了，只需要多加一张新摸的就行
        all_shown_cards.append(cur_request[3])

    return all_shown_cards


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
        if cur_id != dat['id'] and cur_action == 'BUGANG':
            return 'qiang_gang_hu'
        
    
    # 否则都直接pass即可
    print(json.dumps({"response":"PASS", 'debug': [" ".join(dat['cards']), time.time()-t0]}))
    exit(0)


def load_precomputed_table(pkl_route):
    with open(pkl_route, 'rb') as fin:
        return pickle.load(fin)


def select_action(dat):
    # 加载计算好的评分表
    tables = load_precomputed_table(dat['pkl_route'])
    state = dat['state']
    debug = {
        'cards': " ".join(dat['cards']),
        'avail_cards': " ".join(dat['avail_cards']),
        'elapsed_time': time.time()-t0,
        'table_stats': list(map(len, tables)),
        'pack': dat['pack'],
        #'all_shown_cards': dat['all_shown_cards'],
        'card_wall_remain': dat['card_wall_remain'],
    }

    if state == 'self_play':
        # 先尝试胡牌
        isGang = dat['last_is_gang']  # 判定是否杠上开花
        is_hu, judge_re = judge_hu(dat, True, isGang)
        if is_hu:   # 目前策略是能胡直接胡
            print(json.dumps({'response': 'HU', 'debug': debug}))
            exit(0)

        # 出牌算法
        policy = 'table'
        play_card_selected, max_score = play_card(dat, tables, policy)
        global_action = "PLAY {}".format(play_card_selected)
        global_max_score = -1
        # 考虑暗杠或补杠
        angang_reward, bugang_reward = 0.02, 0.02
        angang_res = gang_card_angang(dat, tables, max_score, reward=angang_reward)
        bugang_res = gang_card_bugang(dat, tables, max_score, reward=bugang_reward)

        if angang_res != False:
            global_max_score, global_action = angang_res
        if bugang_res != False:
            cur_max_score, cur_action = bugang_res
            if cur_max_score > global_max_score:
                global_max_score = cur_max_score
                global_action = cur_action
        print(json.dumps({"response": global_action, 'debug': debug}))

    elif state == 'chi_peng_gang':
        # 先尝试胡牌
        is_hu, judge_re = judge_hu(dat, False, False)
        if is_hu:   # 目前策略是能胡直接胡
            print(json.dumps({'response': 'HU', 'debug': debug}))
            exit(0)
        
        cur_card = dat['cur_request'][-1]   # 上一张别人打出的牌
        policy, peng_reward, minggang_reward = 'table', 0, 0.01
        global_max_score, global_action = -1, "PASS"  # 最终的选择

        # 尝试杠牌, 若可以则直接杠
        gang_res = gang_card_minggang(dat, tables, policy, minggang_reward)
        if gang_res != False:
            max_score, action = gang_res
            if max_score > global_max_score:
                global_max_score = max_score
                global_action = action
        
        # 尝试碰牌
        peng_res = peng_card(dat, tables, policy, peng_reward)
        if peng_res != False:
            max_score, action = peng_res
            if max_score > global_max_score:
                global_max_score = max_score
                global_action = action
        
        # 尝试吃牌
        chi_res = chi_card(dat, tables, policy)
        if chi_res != False:
            max_score, action, _ = chi_res
            if max_score > global_max_score:
                global_max_score = max_score
                global_action = action

        print(json.dumps({"response": global_action, 'debug': debug}))
    
    else:   # 尝试抢杠胡
        is_hu, judge_re = judge_hu(dat, False, True)
        if is_hu:   # 目前策略是能胡直接胡
            print(json.dumps({'response': 'HU', 'debug': debug}))
            exit(0)
        action = "PASS"
        print(json.dumps({"response": action, 'debug': debug}))
    exit(0)


def get_keys(cards):
    # 将card list转换成整数key，每种花色一个key
    # 如["B1", "B1", "B4"]对应的key为200100000
    tong_key, tiao_key, wan_key, feng_key, jian_key = 0,0,0,0,0
    for card in cards:
        if card[0] == 'B':
            tong_key += 10**(9-int(card[1]))
        elif card[0] == 'T':
            tiao_key += 10**(9-int(card[1]))
        elif card[0] == 'W':
            wan_key += 10**(9-int(card[1]))
        elif card[0] == 'F':
            feng_key += 10**(4-int(card[1]))    # F1~F4为东南西北
        elif card[0] == 'J':
            jian_key += 10**(3-int(card[1]))     # J1~J3为中发白
    return tong_key, tiao_key, wan_key, feng_key, jian_key


def cal_score(cards, tables):
    # 计算当前card list的胡牌概率/打分
    # 方法为: 将筒条万风箭分别拆出来，查表/搜索得到每种花色含/不含将的胡牌得分
    # 之后枚举，找到恰有一个将的所有牌胡牌概率最大值，作为cards的打分，总的分值用各花色分值求和而得
    # tables为tuple，包含三种花色牌胡牌概率表
    # NOTE:
    #   1. 这个计算仅针对没有鸣的牌(avail_cards)，计算活牌的估值
    # TODO:
    #   1. 原始github实现计算了听牌，若cards已经听牌，则按照听牌数量计算打分，目前还没实现，之后实现

    all_keys = get_keys(cards)
    table_normal, table_feng, table_jian = tables
    all_tables = [table_normal, table_normal, table_normal, table_feng, table_jian]
    max_score, jiang_selected = -1, None

    # 枚举将在每一种花色的情况
    for jiang_type in range(5):
        is_jiang = [0]*5
        is_jiang[jiang_type] = 1
        cur_score = sum([cur_table[cur_key][cur_is_jiang] for cur_table, cur_key, cur_is_jiang in zip(all_tables, all_keys, is_jiang)])
        if cur_score > max_score:
            jiang_selected = jiang_type
            max_score = cur_score
    
    return max_score, jiang_selected


def play_card(dat, tables, policy='table'):
    # 出牌算法，策略可选为'random', 'table', 'search'
    # random为从可以打的牌中随机选一张
    # table为根据打表估值，枚举每一张可打牌，看哪一张去掉后总估值最大，选择该牌
    # search为搜索算法，待实现

    if policy == 'random':
        return random.choice(dat['avail_cards']), -1
    
    elif policy == 'table':
        max_score, play_card_selected = -1, None
        for card in set(dat['avail_cards']):
            dat['avail_cards'].remove(card)
            cur_score, jiang_selected = cal_score(dat['avail_cards'], tables)
            dat['avail_cards'].append(card)
            if cur_score > max_score:
                max_score = cur_score
                play_card_selected = card

        return play_card_selected, max_score

    else:
        raise NotImplementedError


def chi_card(dat, tables, policy='table'):
    # 吃牌算法，策略可选为 'table', 'search'
    # 若当前request不能吃，直接返回False，否则根据policy做决策
    # table根据打表估值，分别计算吃前/所有可能的吃后/吃后再出一张牌后avail_cards的估值
    
    cur_card = dat['cur_request'][-1]
    # 只有序数牌才能吃
    if cur_card[0] not in ('B', 'T', 'W'):
        return False
    # 只能吃上家
    if (int(dat['cur_request'][1])+1)%4 != dat['id']:
        return False
    
    if policy == 'table':
        avail_chi_actions = []  # 记录可行的吃法及相应估值结果
        raw_score, _ = cal_score(dat['avail_cards'], tables)
        max_score = raw_score
        card_l2 = cur_card[0]+str(int(cur_card[1])-2)
        card_l1 = cur_card[0]+str(int(cur_card[1])-1)
        card_r1 = cur_card[0]+str(int(cur_card[1])+1)
        card_r2 = cur_card[0]+str(int(cur_card[1])+2)
        
        # 枚举三种情况
        if dat['avail_cards'].count(card_l2) > 0 and dat['avail_cards'].count(card_l1) > 0:
            dat['avail_cards'].remove(card_l2)
            dat['avail_cards'].remove(card_l1)
            new_score, _ = cal_score(dat['avail_cards'], tables)
            play_card_selected, new_max_score = play_card(dat, tables, policy='table')
            dat['avail_cards'].append(card_l2)
            dat['avail_cards'].append(card_l1)
            if new_max_score > max_score:
                max_score = new_max_score
                action = "CHI {} {}".format(card_l1, play_card_selected)
                avail_chi_actions.append([0, card_l1, play_card_selected, new_score, new_max_score])
        
        if dat['avail_cards'].count(card_l1) > 0 and dat['avail_cards'].count(card_r1) > 0:
            dat['avail_cards'].remove(card_l1)
            dat['avail_cards'].remove(card_r1)
            new_score, _ = cal_score(dat['avail_cards'], tables)
            play_card_selected, new_max_score = play_card(dat, tables, policy='table')
            dat['avail_cards'].append(card_l1)
            dat['avail_cards'].append(card_r1)
            if new_max_score > max_score:
                max_score = new_max_score
                action = "CHI {} {}".format(cur_card, play_card_selected)
                avail_chi_actions.append([1, cur_card, play_card_selected, new_score, new_max_score])
        
        if dat['avail_cards'].count(card_r1) > 0 and dat['avail_cards'].count(card_r2) > 0:
            dat['avail_cards'].remove(card_r1)
            dat['avail_cards'].remove(card_r2)
            new_score, _ = cal_score(dat['avail_cards'], tables)
            play_card_selected, new_max_score = play_card(dat, tables, policy='table')
            dat['avail_cards'].append(card_r1)
            dat['avail_cards'].append(card_r2)
            if new_max_score > max_score:
                max_score = new_max_score
                action = "CHI {} {}".format(card_r1, play_card_selected)
                avail_chi_actions.append([2, card_r1, play_card_selected, new_score, new_max_score])
        
        if len(avail_chi_actions) == 0:
            return False
        else:
            return max_score, action, avail_chi_actions
    
    else:
        raise NotImplementedError


def peng_card(dat, tables, policy='table', reward=0):
    # 碰牌算法，策略可选为 'table', 'search'
    # 若当前request不能碰，直接返回False，否则根据policy做决策
    # table根据打表估值，分别计算碰前/碰后/碰后再出一张牌后avail_cards的估值
    # 另外可以设置碰牌reward来鼓励碰牌带来的番

    # 先判断碰牌是否合法
    cur_card = dat['cur_request'][-1]
    if dat['avail_cards'].count(cur_card) < 2:
        return False

    if policy == 'table':
        # 原始得分
        raw_score, _ = cal_score(dat['avail_cards'], tables)
        # 碰后得分
        dat['avail_cards'].remove(cur_card)
        dat['avail_cards'].remove(cur_card)
        new_score, _ = cal_score(dat['avail_cards'], tables)
        # 碰+出牌后得分
        play_card_selected, new_max_score = play_card(dat, tables, policy='table')

        dat['avail_cards'].append(cur_card)
        dat['avail_cards'].append(cur_card)

        if new_max_score >= raw_score:
            action = "PENG {}".format(play_card_selected)
            return new_max_score, action
        return False

    else:
        raise NotImplementedError


def gang_card_minggang(dat, tables, policy='table', reward=0.):
    # 杠别人打出的牌, 即明杠

    # 先判断杠牌是否合法
    cur_card = dat['cur_request'][-1]
    if dat['avail_cards'].count(cur_card) < 3:
        return False
    
    if policy == 'table':
        # 原始得分
        raw_score, _ = cal_score(dat['avail_cards'], tables)
        # 杠后得分
        dat['avail_cards'].remove(cur_card)
        dat['avail_cards'].remove(cur_card)
        dat['avail_cards'].remove(cur_card)
        new_score, _ = cal_score(dat['avail_cards'], tables)

        dat['avail_cards'].append(cur_card)
        dat['avail_cards'].append(cur_card)
        dat['avail_cards'].append(cur_card)

        if new_score + reward >= raw_score:
            action = "GANG"
            return new_score + reward, action
        return False

    else:
        raise NotImplementedError


def gang_card_angang(dat, tables, max_play_card_score, policy='table', reward=0.):
    # 杠自己刚刚摸的牌, 即暗杠
    # max_play_card_score: 如果不杠，打出去一张牌后活牌牌型的最高得分

    # 先判断杠牌是否合法，由于当前request为摸牌，这张牌在parse_input中已经放入avail_cards中，故需要4张
    cur_card = dat['cur_request'][-1]   # 这一把摸到的牌，已经放到avail_cards中
    if dat['avail_cards'].count(cur_card) < 4:
        return False
    
    if policy == 'table':
        # 杠后得分
        dat['avail_cards'].remove(cur_card)
        dat['avail_cards'].remove(cur_card)
        dat['avail_cards'].remove(cur_card)
        dat['avail_cards'].remove(cur_card)
        new_score, _ = cal_score(dat['avail_cards'], tables)

        dat['avail_cards'].append(cur_card)
        dat['avail_cards'].append(cur_card)
        dat['avail_cards'].append(cur_card)
        dat['avail_cards'].append(cur_card)

        # 考虑是否暗杠，实际上是比较杠/不杠的估值
        # 对于不杠，由于这一把摸了牌，必须要打一张，所以其估值为打了一张之后的最大估值
        # 对于杠，这4张牌都是死牌了，故为余下牌的估值
        # 然而，杠之后实际上还有一轮摸牌、打牌，实际上之后的估值还会提升（因为至少能把摸的牌打掉，估值不会下降），所以这个比较是不公平的
        # 纯粹基于table的方法无法估计下一轮的后验分布，所以这里引入了reward，给杠本身加一点激励，有助于得到暗杠2番
        # 但这个reward也不能太大，避免凑杠而拆牌的情况发生（e.g. W1, W2, W3*3 + W3, 不应杠）
        if new_score + reward >= max_play_card_score:
            action = "GANG {}".format(cur_card)
            return new_score + reward, action
        return False

    else:
        raise NotImplementedError


def gang_card_bugang(dat, tables, max_play_card_score, policy='table', reward=0.):
    # 杠自己刚刚摸的牌并加到一个明刻上, 即补杠
    # max_play_card_score: 如果不杠，打出去一张牌后活牌牌型的最高得分

    # 先判断杠牌是否合法，要求之前碰过这张牌
    cur_card = dat['cur_request'][-1]   # 这一把摸到的牌，已经放到avail_cards中
    check_peng_exist = False
    pack = dat['pack']
    for ix, cur_pack in enumerate(pack):
        if cur_pack[0] == 'PENG' and cur_pack[1] == cur_card:
            check_peng_exist = True
            break
    if not check_peng_exist:
        return False
    
    if policy == 'table':
        # 杠后得分
        dat['avail_cards'].remove(cur_card)
        new_score, _ = cal_score(dat['avail_cards'], tables)

        dat['avail_cards'].append(cur_card)

        # 这里reward的意义和暗杠实际上一样，其实在补杠中这个问题更直接
        # 因为对于打分，补杠就相当于打出摸得那张牌，这个得分肯定不会高于max_play_card_score
        # 所以必须要有reward补杠才有效
        if new_score + reward >= max_play_card_score:
            action = "BUGANG {}".format(cur_card)
            return new_score + reward, action
        return False

    else:
        raise NotImplementedError


def judge_hu(dat, isZimo, isGang):
    # 调用算番库判定有没有胡牌
    # 当前明牌、和牌
    cur_pack = tuple((tuple(pk) for pk in dat['pack']))
    winTile = dat['cur_request'][-1]
    
    # 自摸一张牌(包括杠上开花)，此时新的那张牌已经加入avail_cards了，但判胡时不应在手牌里，所以去掉
    if isZimo:
        dat['avail_cards'].remove(winTile)
    cur_hand = tuple(dat['avail_cards'])    # 当前手牌
    
    # 判定海底捞月、妙手回春需要计算别人的牌墙
    if isZimo:
        next_id = (dat['id'] + 1) % 4   # 判断我的下家牌墙里有没有牌
    else:
        next_id = (int(dat['cur_request'][1]) + 1) % 4  # 判断出牌者的下家牌墙里有没有牌
    isLast = (dat['card_wall_remain'][next_id] == 0)    # 没牌了，则是妙手回春/海底捞月，即isLast
    if isGang and not isZimo:   # 但是如果是抢杠胡，isLast一定是False，这块需要特判，因为那张胡牌实际上没打出来，没有所谓的下家
        isLast = False

    # 判定和绝张需要判定明牌里面是否已经有三张winTile
    if dat['all_shown_cards'].count(winTile) + int(isZimo) >= 4:
        isJuezhang = True
    else:
        isJuezhang = False

    try:
        judge_res = MahjongFanCalculator(cur_pack, cur_hand, winTile, 0, isZimo, isJuezhang, isGang, isLast, dat['quan'], dat['id'])
    except Exception as err:
        judge_res = str(err)
    # print(judge_res, '\n', isZimo, isGang, isLast, isJuezhang)
    
    if isinstance(judge_res, str):
        cur_fan = 0
    else:
        cur_fan = sum([fan[0] for fan in judge_res])

    # 之后还得恢复回来，因为还可能计算别的
    if isZimo:
        dat['avail_cards'].append(winTile)

    if cur_fan >= 8:
        return True, judge_res
    else:
        return False, judge_res


def main():
    full_input = json.loads(input())
    ret = parse_input(full_input)
    state = do_early_pass(ret)
    ret['state'] = state
    ret['pkl_route'] = './data/Majiang/table_normal_feng_jian.pkl'
    select_action(ret)


def unit_test():

    temp_dat = {
        "turn_id": 168,
        "data": None,
        "id": 3,
        "cards": ['F1', 'F1', 'F1', 'F4', 'F4', 'F4', 'T1', 'T1', 'T1', 'T5', 'T6', 'T6', 'T6'],
        "avail_cards": ['F1', 'F1', 'F1', 'T1', 'T1', 'T1', 'T5'],
        "cur_request": ["3", "1", "PLAY", "F1"],
        "pack": [['PENG', 'F4', 3], ['PENG', 'T6', 3]],
        "quan": 3,
        "all_shown_cards": ['F2', 'F3', 'J1', 'J3', 'J3', 'B1', 'T9', 'F2', 'J2', 'W5', 'W6', 'W7', 'B8', 'B2', 'T9', 'T3', 'T9', 'B9', 'F4', 'F4', 'F4', 'T2', 'T3', 'T4', 'W5', 'W8', 'B8', 'J2', 'W1', 'B3', 'B4', 'B5', 'W9', 'T5', 'T2', 'B2', 'T5', 'T1', 'W9', 'F2', 'B8', 'W7', 'B6', 'B9', 'J3', 'T9', 'B7', 'W1', 'J1', 'W2', 'W2', 'W3', 'W4', 'T4', 'F2', 'F3', 'F3', 'F3', 'T7', 'T7', 'T7', 'B9', 'T3', 'T7', 'B4', 'F4', 'B2', 'T5', 'W6', 'B8', 'J2', 'B2', 'W8', 'J2', 'B1', 'B6', 'B4', 'T6', 'T6', 'T6', 'W2', 'J3', 'J1', 'B7', 'B3', 'W6', 'T8', 'B5', 'B3', 'B4', 'T2', 'T2', 'W4', 'B5', 'T8', 'B1', 'W1', 'W2', 'B6', 'B9', 'W7', 'T6', 'F1'],
        "last_is_gang": False,
        "card_wall_remain": [0, 1, 3, 1],
        "state": "chi_peng_gang",
        "pkl_route": "./data/Majiang/table_normal_feng_jian.pkl"
    }

    temp_dat = {
        "turn_id": 168,
        "data": None,
        "id": 3,
        "cards": ['F4', 'F4', 'F4', 'T6', 'T6', 'T6', 'W1', 'W2', 'W3', 'W3', 'W3', 'T1', 'T3', 'W3'],
        "avail_cards": ['W1', 'W2', 'W3', 'W3', 'W3', 'T1', 'T3', 'W3'],
        "cur_request": ["2", "W3"],
        #"cur_request": ["3", "1", "PLAY", "W3"],
        "pack": [['PENG', 'F4', 3], ['PENG', 'T6', 3]],
        "quan": 3,
        "all_shown_cards": ['F2', 'F3', 'J1', 'J3', 'J3', 'B1', 'T9', 'F2', 'J2', 'W5', 'W6', 'W7', 'B8', 'B2', 'T9', 'T3', 'T9', 'B9', 'F4', 'F4', 'F4', 'T2', 'T3', 'T4', 'W5', 'W8', 'B8', 'J2', 'W1', 'B3', 'B4', 'B5', 'W9', 'T5', 'T2', 'B2', 'T5', 'T1', 'W9', 'F2', 'B8', 'W7', 'B6', 'B9', 'J3', 'T9', 'B7', 'W1', 'J1', 'W2', 'W2', 'W3', 'W4', 'T4', 'F2', 'F3', 'F3', 'F3', 'T7', 'T7', 'T7', 'B9', 'T3', 'T7', 'B4', 'F4', 'B2', 'T5', 'W6', 'B8', 'J2', 'B2', 'W8', 'J2', 'B1', 'B6', 'B4', 'T6', 'T6', 'T6', 'W2', 'J3', 'J1', 'B7', 'B3', 'W6', 'T8', 'B5', 'B3', 'B4', 'T2', 'T2', 'W4', 'B5', 'T8', 'B1', 'W1', 'W2', 'B6', 'B9', 'W7', 'T6', 'F1'],
        "last_is_gang": False,
        "card_wall_remain": [0, 1, 3, 1],
        "state": "self_play",
        "pkl_route": "./data/Majiang/table_normal_feng_jian.pkl"
    }
    select_action(temp_dat)


if __name__ == "__main__":
    #unit_test()
    main()