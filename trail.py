# writen by Yang Yixin
# estimate the trails of users, and draw map

import sys
import math
import numpy as np
from datetime import datetime
from datetime import timedelta

from data import load_cell
from data import basic_map
from data import draw_map
from data import load_rail_station

R = 6371393
def distance(A, B) :
    A = [math.radians(a) for a in A]
    B = [math.radians(b) for b in B]
    C = pow(math.sin((A[0] - B[0]) / 2), 2) + math.cos(A[0])*math.cos(B[0])*pow(math.sin((A[1] - B[1]) / 2), 2)
    # print(C)
    Distance = 2*R*math.asin(math.sqrt(C))
    return Distance

def clean_data(number, Map) :
    F = open('data/' + str(number) + '.txt', 'r')
    x = F.read().splitlines()
    F.close()
    S = dict()
    cell = load_cell()
    Move = []
    pre_time = None
    pre_cell = None
    for d in x :
        cell_id, dates, service_type, user_id, web = d.split(',')
        if not cell_id in cell:
            continue
        dt = datetime.strptime(dates, '%Y-%m-%d %H:%M:%S')
        if len(S)!= 0:
            s = (dt - pre_time).seconds
            if s and (distance(cell[cell_id]['position'], cell[pre_cell]['position'])/s > 60) :
                # print(distance(cell[cell_id]['position'], cell[pre_cell]['position'])/s)
                continue
            if (s <= 10) or (pre_cell == cell_id):
                if not (cell_id in S) :
                    S[cell_id] = s/2
                else:
                    S[cell_id] += s/2
                S[pre_cell] += s/2
            else: 
                pos = [0, 0]
                sum_time = 0
                for key, value in S.items():
                    pos = [a * value + b for a,b in zip(cell[key]['position'], pos)]
                    sum_time += value
                if not (sum_time == 0):
                    pos = [round(a / sum_time, 6) for a in pos]
                else :
                    a = [key for key, value in S.items()]
                    pos = cell[a[0]]['position']
                Move.append([pos, sum_time, [pre_time - timedelta(seconds = sum_time), pre_time]]) 
                # [position, sum_time, [start_time, end_time]]
                S = dict()
        if not (cell_id in S):
            S[cell_id] = 0
        pre_cell = cell_id
        pre_time = dt
    if Map:
        Map = draw_map(Map, [[a[0],300] for a in Move] )
        F = open('test.txt', 'w')
        for v in Move:
            print(v[0], v[1], '[', v[2][0],',', v[2][1], ']', file = F)
        F.close()
    return Move

def deal(st, ed):
    if st == ed:
        return False
    print(st)
    print(ed)
    return True

eps = 0.01
def railway(number, Map):
    Move = clean_data(number, Map)
    st = None
    ed = None
    last_time = None
    last_pos = None
    direction = None
    for a in Move:
        pos = a[0]
        sum_time = a[1]
        time = a[2]
        flag1 = True # = false :can not be in 
        flag2 = True # = false :only can be start or end
        if (pos[0] < 31.69) or (pos[0] > 31.89) :
            flag1 = False
        if (pos[1] < 117.28) or (pos[1] > 117.32) :
            flag1 = False
        if (direction == None) and (last_pos != None):
            direction = np.sign(pos[0] - last_pos[0])
        if (last_pos != None) and (direction != None) and ((pos[0] - last_pos[0]) * direction < -eps):
            flag2 = False
        if (sum_time > 90) or ((last_time != None) 
                            and (time[0] - last_time[1]).seconds > distance(pos, last_pos)*60*60/80000) :
            flag2 = False
        if flag1 == True:
            if st == None:
                st = a
            ed = a
        if (flag1 == False) or (flag2 == False):
            if (st != None) and (ed != None) :
                deal(st, ed)
            direction = None
            if flag1 == False:
                st = None
                ed = None
                last_pos = None
                last_time = None
            else :
                st = a
                ed = a
                last_pos = pos
                last_time = time

def deal_with(number, passby, ans, Map) :
    pre_station = -1
    pre_dist = 0
    pre_time = None
    pre_flag = False
    start = None
    interval = []
    node = []
    for id, x in enumerate(passby) :
        station = x[0]
        dist = x[1]
        time = x[2]
        flag = x[3]
        position = x[4]
        if (not start) and (flag) :
            start = [station, time[0]]
        if (station > pre_station) or (station == pre_station and dist >= pre_dist) :
            pre_station = station
            pre_dist = dist
            pre_time = time
            pre_flag = flag
            node.append(position)
        else :
            if (pre_station != -1) and pre_flag and start:
                if start[0] != pre_station:
                    interval.append((start, [pre_station, pre_time[1]]))
                    if  Map:
                        node = [[a,300] for a in node]
                        draw_map(Map, node, color = 'green')
                node = []
            start = [station, time[0]]
            pre_station = station
            pre_dist = dist
            pre_time = time
            pre_flag = flag
    if (pre_station != -1) and pre_flag:
        if start[0] != pre_station:
            interval.append((start, [pre_station, pre_time[1]]))
            if  Map:
                node = [[a,300] for a in node]
                draw_map(Map, node, color = 'green')
        node = []
    pre_station = 100 # max station id
    pre_dist = 0
    start = None
    for id, x in enumerate(passby) :
        station = x[0]
        dist = x[1]
        time = x[2]
        flag = x[3]
        position = x[4]
        if (not start) and (flag) :
            start = [station, time[0]]
        if (station < pre_station) or (station == pre_station and dist >= pre_dist) :
            pre_station = station
            pre_dist = dist
            pre_time = time
            pre_flag = flag
            node.append(position)
        else :
            if (pre_station != 100) and pre_flag and start:
                if start[0] != pre_station:
                    interval.append((start, [pre_station, pre_time[1]]))
                    if  Map:
                        node = [[a,300] for a in node]
                        draw_map(Map, node, color = 'green')
                node = []
            start = [station, time[0]]
            pre_station = station
            pre_dist = dist
            pre_time = time
            pre_flag = flag
    if (pre_station != 100) and pre_flag and start:
        if start[0] != pre_station:
            interval.append((start, [pre_station, pre_time[1]]))
            if  Map:
                node = [[a,300] for a in node]
                draw_map(Map, node, color = 'green')
        node = []
    for start, end in interval :
        if (start[0] != end[0]) :
            ans.append([number, [start[0], end[0]], [start[1], end[1]]])
    return ans

def nearest_station(stations, position) :
    min_dist = None
    ret = None
    for id, station in enumerate(stations) :
        dist = distance(station, position)
        if (not min_dist) or (min_dist > dist) :
            min_dist = dist
            ret = id
    return ret, min_dist
        

def is_on_subway(number, Map, ans) :
    Move = clean_data(number, Map)

    passby = []
    pre_position = None
    pre_time = None
    pre_station = None
    for x in Move:
        position = x[0]
        sum_time = x[1]
        time = x[2]
        station_id, dist = nearest_station(station, position)
        if not pre_station :
            pre_station = station_id
        if pre_time and pre_position :
            if (((time[0] - pre_time).seconds - 45 * (abs(station_id - pre_station) - 1)) > 0) :
                velocity = distance(pre_position, position) / ((time[0] - pre_time).seconds - 45 * (abs(station_id - pre_station) - 1))
            else :
                velocity = 40
        else :
            velocity = 20
        if Map:
            print(station_id, dist, velocity, time[0])
        if (dist > 400) and (dist <= 2000) and (sum_time < 30) and (velocity >= 8) and (velocity < 25) and pre_time:
            passby.append([station_id, dist, time, False, position]) # at the middle of stations
            pre_time = time[1]
            pre_position = position
            pre_station = station_id
        elif (dist < 400) and (sum_time > 45) and (velocity >= 8) and (velocity < 25):
            if sum_time <= 70 :
                passby.append([station_id, dist, time, False, position]) # at the station
            passby.append([station_id, dist, time, True, position])
            pre_time = time[1]
            pre_position = position
            pre_station = station_id
        else :
            while len(passby) and (passby[len(passby) - 1][3] == False) :
                passby.pop()
            ans = deal_with(number, passby, ans, Map)
            passby = []
            pre_time = None
            pre_position = None
            pre_station = None
            flag = False
            if (dist < 400) and (sum_time > 70):
                flag = True
                passby.append([station_id, dist, time, True, position])
                pre_time = time[1]
                pre_position = position
                pre_station = station_id
    return ans

def draw_station(station, Map) :
    Map = draw_map(Map, [[a, 300] for a in station], 'red')
    return Map

def draw_with_user(number):
    F = open('data/' + str(number) + '.txt', 'r')
    x = F.read().splitlines()
    F.close()

    Map = basic_map()
    cell = load_cell()
    node = []
    flag = False
    last = None
    for d in x :
        cell_id, dates, service_type, user_id, web = d.split(',')
        if (cell_id == last) :
            continue
        flag = True
        last = cell_id
        if not cell_id in cell :
            continue
        else :
            node.append(cell[cell_id])
    Map = draw_map(Map, node)
    return Map


'''
Map = basic_map()
station = load_rail_station()
# draw_station(station, Map)
# railway(i, Map)
if (len(sys.argv) <= 1) :
    for i in range(1, 50001):
        FILE = open('result/ans.txt', 'a')
        print(i)
        ans = []
        ans = is_on_subway(i, None, ans)
        for x in ans:
            print('user_number:', x[0], 'start_end_station:', x[1], 'start_end_time:', x[2][0], x[2][1], file = FILE)
        FILE.close()
else :
    i = int(sys.argv[1])
    ans = []
    is_on_subway(i, Map, ans)
    for x in ans:
        print('user_number:', x[0], 'start_end_station:', x[1], 'start_end_time:', x[2][0], x[2][1])
        
'''