# written by Miao Ruijie
# estimate the trails of usrs in another way
# the basic idea is to find the cells that have intersection with the railway, and
# for each cell, record its corresponding stations

from data import *
from trail import *
import json
import math
from geographiclib.geodesic import Geodesic


subway_velocity = 30 * 1000 / (60 * 60) # the average velocity of the subway

def bearing(A, B):
    geod = Geodesic.WGS84
    g = geod.Inverse(A[0], A[1], B[0], B[1])
    return g['azi1'] * math.pi / 180


def point_to_line(point, lineStart, lineEnd):
    delta_Sp = distance(lineStart, point) / R
    theta_Sp = bearing(lineStart, point)
    theta_SE = bearing(lineStart, lineEnd)
    return abs(math.asin(math.sin(delta_Sp) * math.sin(theta_Sp - theta_SE)) * R)

def point_in_range(point, lineStart, lineEnd):
    theta_Sp = bearing(lineStart, point)
    theta_SE = bearing(lineStart, lineEnd)
    theta_ES = bearing(lineEnd, lineStart)
    theta_Ep = bearing(lineEnd, point)
    return -math.pi / 2 < (theta_Sp - theta_SE) < math.pi / 2 \
           and -math.pi / 2 < (theta_ES - theta_Ep) < math.pi / 2


def draw_useful_cell(Map):
    cell = load_cell()
    with open('CellToStation.txt', 'r') as f:
        CtoS = json.load(f)
    cnt = 0
    for cell_id in CtoS:
        cnt += 1
        Map = draw_map(Map, [[cell[cell_id]['position'], cell[cell_id]['radius']]])
    print(cnt)
    Map.save('test.html')

    return Map


def create_CellToStation(cell, stations):
    '''
    :return: CtoS, a dictionary from cell to its relative stations
    there are two conditions:
        1. CtoS[cell_id]=['st', index1, index2, ...], show the cell cover station[index1], ...
        2. CtoS[cell_id]=['pass',[pre,next]] show the cell cover the railway
            between two cells;
    '''
    CtoS = dict()
    for cell_id in cell:
        for index in range(len(stations)):
            if distance(stations[index], cell[cell_id]['position']) < cell[cell_id]['radius']:
                if cell_id not in CtoS:
                    CtoS[cell_id] = ['st']
                CtoS[cell_id].append(index)
        if cell_id in CtoS:
            continue
        for index in range(1, len(stations)):
            pre_index = index - 1
            if point_to_line(cell[cell_id]['position'], stations[pre_index], stations[index]) < cell[cell_id]['radius'] \
                and point_in_range(cell[cell_id]['position'], stations[pre_index], stations[index]):
                if cell_id not in CtoS:
                    CtoS[cell_id] = ['pass']
                CtoS[cell_id].append([pre_index, index])

        if CtoS[cell_id][0] == 'pass' and len(CtoS[cell_id]) > 2:
            CtoS[cell_id] = ['st']
            for p in CtoS[cell_id][1:]:
                pre, next = p
                if pre not in CtoS[cell_id]:
                    CtoS[cell_id].append(pre)
                if next not in CtoS[cell_id]:
                    CtoS[cell_id].append(next)

    with open('CellToStation.txt', 'w+') as f:
        f.write(json.dumps(CtoS, indent=4))
    return CtoS


def usr_trail(CtoS, usr_path):
    '''
    :param CtoS: dictionary of CellToStation
    :param usr_path: path of usr's data
    :return: a list of usr's trail, may consists three kinds:
        '#': usr out of subway's range
        ['st', [index1, index2,..], [start_time, end_time]]: usr may stay in stations
        ['pass', [[pre1,next1],[pre2,next2],...],[start_time,end_time]]: usr may pass between stations
    '''
    f = open(usr_path, 'r')
    x = f.read().splitlines()
    f.close()

    # combine the adjacent record in the same cell
    v = []
    for d in x:
        cell_id, dates, service_type, user_id, web = d.split(',')
        if len(v) and v[-1]['id'] == cell_id:
            v[-1]['end_time'] = dates
        else:
            cell_time = dict()
            cell_time['id'] = cell_id
            cell_time['start_time'] = cell_time['end_time'] = dates
            v.append(cell_time)

    # use CtoS to transform cell_id to stations
    station_time = []
    for cell_time in v:
        if cell_time['id'] in CtoS: # the cell is alongside the railway
            if CtoS[cell_time['id']][0] == 'st': # the cell cover stations
                start = datetime.strptime(cell_time['start_time'], '%Y-%m-%d %H:%M:%S')
                end = datetime.strptime(cell_time['end_time'], '%Y-%m-%d %H:%M:%S')
                stay_station = CtoS[cell_time['id']][1:]
                station_time.append(['st', stay_station, [start, end]])
            else: # the cell cover the railway between stations
                pass_between = CtoS[cell_time['id']][1:]
                start = datetime.strptime(cell_time['start_time'], '%Y-%m-%d %H:%M:%S')
                end = datetime.strptime(cell_time['end_time'], '%Y-%m-%d %H:%M:%S')
                if (end - start).seconds < 3 * 60: # if usr take the subway, he must pass quickly
                    station_time.append(['pass', pass_between, [start, end]])

                elif len(station_time) and station_time[-1] != '#': # do not take subway
                    station_time.append('#')

        else: # the cell in out of the range on railway
            if len(station_time) and station_time[-1] != '#':
                station_time.append('#')

    return station_time


def judge_stay_velocity(stations, st1, st2, start_time, end_time):
    '''
    if subway can stay in range[st1, st2] from start_time to end_time
    return True, else return False
    '''
    if (end_time - start_time).seconds < 60 * 3:
        return True
    dist = distance(stations[st1], stations[st2])
    velocity = dist / (end_time - start_time).seconds
    if velocity < 20 * 1000 / (60*60):
        return False
    return True


def find_longest_path(prob_list):
    max_len = 0
    max_start = 0
    tmplen = 0
    start = 0
    for p in range(len(prob_list)):
        if prob_list[p] and tmplen == 0:
            start = p
        if prob_list[p]:
            tmplen += 1
        elif not prob_list[p] and len:
            if max_len < tmplen:
                max_len = tmplen
                max_start = start
            tmplen = 0

    if max_len < tmplen:
        max_len = tmplen
        max_start = start

    return max_len, max_start


def deal_usrSeg(trail): # deal with a segment trail of usr
    stations = load_rail_station()
    usr_trail = []
    for t in trail:
        if len(usr_trail) and t[0] == usr_trail[-1][0] and t[1] == usr_trail[-1][1]:
            usr_trail[-1][2][1] = t[2][1]
        else:
            usr_trail.append(t)

    forward_prob = []
    pre_st = None
    min_st_index = 0

    # create forward_prob
    for t in trail:
        pass_forward = True
        # judge direction
        if t[0] == 'pass':
            pass_forward &= (min_st_index <= t[1][0][0])
            next_min = t[1][0][1]
        else:
            pass_forward &= (min_st_index <= t[1][-1])
            next_min = t[1][0] if min_st_index > t[1][-1] else max(min_st_index, t[1][0])
        # judge velocity
        if pre_st and pass_forward:
            if t[0] == 'pass':
                pass_forward = judge_stay_velocity(stations, min_st_index, t[1][0][1], pre_st[2][1], t[2][0])
            else:
                pass_forward = judge_stay_velocity(stations, min_st_index, t[1][-1], pre_st[2][1], t[2][0])

        if pre_st:
            forward_prob.append(pass_forward)
        min_st_index = next_min
        pre_st = t

        if t[0] == 'pass':
            forward_prob.append(True)
        else:
            forward_prob.append(judge_stay_velocity(stations, t[1][0], t[1][-1], t[2][0], t[2][1]))

    pre_st = None
    max_st_index = 22
    backward_prob = []

    # create backward_prob
    for t in trail:
        pass_backward = True
        # judge direction
        if t[0] == 'pass':
            pass_backward &= (max_st_index >= t[1][0][1])
            next_max = t[1][0][0]
        else:
            pass_backward &= (max_st_index >= t[1][-1])
            next_max = t[1][-1] if max_st_index < t[1][0] else min(max_st_index, t[1][-1])
        # judge velocity
        if pre_st and pass_backward:
            if t[0] == 'pass':
                pass_backward = judge_stay_velocity(stations, t[1][0][0], max_st_index, pre_st[2][1], t[2][0])
            else:
                pass_backward = judge_stay_velocity(stations, t[1][0], max_st_index, pre_st[2][1], t[2][0])

        if pre_st:
            backward_prob.append(pass_backward)
        max_st_index = next_max
        pre_st = t

        if t[0] == 'pass':
            backward_prob.append(True)
        else:
            backward_prob.append(judge_stay_velocity(stations, t[1][0], t[1][-1], t[2][0], t[2][1]))

    forward_len, forward_start = find_longest_path(forward_prob)
    backward_len, backward_start = find_longest_path(backward_prob)

    if forward_len <= 1 and backward_len <= 1:
        return 'unsolvable'

    if forward_len >= backward_len: # forward
        start = forward_start // 2
        end = math.ceil((forward_start+forward_len-1)/2)
        # start station and time
        if trail[start][0] == 'pass':
            start_st = trail[start][1][0][0]
            start_st_time = trail[start][2][0]
        else:
            start_st_list = []
            for st in trail[start][1]:
                if (trail[start+1][0] == 'st' and st <= trail[start+1][1][-1]) or \
                        (trail[start+1][0]=='pass' and st <= trail[start+1][1][0][1]):
                    start_st_list.append(st)
            start_st = start_st_list[len(start_st_list)//2]
            if len(start_st_list) == 1:
                start_st_time = trail[start][2][1]
            else:
                start_st_time = trail[start][2][0] + timedelta(
                    seconds=(trail[start][2][1] - trail[start][2][0]).seconds / 2)
        # end station and time
        if trail[end][0] == 'pass':
            end_st = trail[end][1][0][1]
            end_st_time = trail[end][2][1]
        else:
            end_st_list = []
            for st in trail[end][1]:
                if (trail[end-1][0] == 'st' and st >= trail[end-1][1][0]) or \
                        (trail[end-1][0]=='pass' and st >= trail[end-1][1][0][1]):
                    end_st_list.append(st)
            end_st = end_st_list[len(end_st_list)//2]
            if len(end_st_list) == 1:
                end_st_time = trail[end][2][1]
            else:
                end_st_time = trail[end][2][0] + timedelta(
                    seconds=(trail[end][2][1] - trail[end][2][0]).seconds / 2)
    else: # backward
        start = backward_start // 2
        end = math.ceil((backward_start + backward_len - 1) / 2)
        # start station and time
        if trail[start][0] == 'pass':
            start_st = trail[start][1][0][1]
            start_st_time = trail[start][2][0]
        else:
            start_st_list = []
            for st in trail[start][1]:
                if (trail[start + 1][0] == 'st' and st >= trail[start + 1][1][0]) or \
                        (trail[start + 1][0] == 'pass' and st >= trail[start + 1][1][0][0]):
                    start_st_list.append(st)
            start_st = start_st_list[len(start_st_list) // 2]
            if len(start_st_list) == 1:
                start_st_time = trail[start][2][1]
            else:
                start_st_time = trail[start][2][0] + timedelta(
                    seconds=(trail[start][2][1] - trail[start][2][0]).seconds / 2)
        # end station and time
        if trail[end][0] == 'pass':
            end_st = trail[end][1][0][0]
            end_st_time = trail[end][2][1]
        else:
            end_st_list = []
            for st in trail[end][1]:
                if (trail[end-1][0] == 'st' and st <= trail[end-1][1][-1]) or \
                        (trail[end-1][0] == 'pass' and st <= trail[end-1][1][0][0]):
                    end_st_list.append(st)
            end_st = end_st_list[len(end_st_list)//2]
            if len(end_st_list) == 1:
                end_st_time = trail[end][2][1]
            else:
                end_st_time = trail[end][2][0] + timedelta(
                    seconds=(trail[end][2][1] - trail[end][2][0]).seconds / 2)

    if start_st != end_st and start_st_time != end_st_time:
        dist = distance(stations[start_st], stations[end_st])
        min_time = dist / (40*1000/3600)
        max_time = dist / (10*1000/3600)
        if max_time >= (end_st_time - start_st_time).seconds >= min_time:
            return start_st, end_st, start_st_time, end_st_time
    return 'unsolvable'


def deal_usrTrail(trail): # deal with the whole trail of usrs
    pre = 0
    schedule = []
    for pos in range(len(trail)):
        if trail[pos] == '#':
            if deal_usrSeg(trail[pre:pos]) != 'unsolvable':
                schedule.append(deal_usrSeg(trail[pre:pos]))
            pre = pos + 1

    if deal_usrSeg(trail[pre:]) != 'unsolvable':
        schedule.append(deal_usrSeg(trail[pre:]))
    return schedule


'''
Map = basic_map()
Map = draw_station(stations, Map)
with open('CellToStation.txt', 'r') as f:
    CtoS = json.load(f)
cnt = 0
for cell_id in CtoS:
    cnt += 1
    Map = draw_map(Map, [[cell[cell_id]['position'], cell[cell_id]['radius']]])
print(cnt)
Map.save('test.html')
'''

cell = load_cell()
stations = load_rail_station()
with open('CellToStation.txt', 'r') as f:
    CtoS = json.load(f)
usr_num = 50000
cnt = 0
f = open('usr_subway.txt', 'w+')

for i in range(usr_num):
    trail = usr_trail(CtoS, 'data/'+str(i+1)+'.txt')
    schedule = deal_usrTrail(trail)
    if len(schedule):
        for way in schedule:
            print('usr_number:', i+1, 'start_st:', way[0], 'end_st:', way[1], 'start_time:',
                  way[2].strftime("%Y-%m-%d %H:%M:%S"), 'end_time:', way[3].strftime("%Y-%m-%d %H:%M:%S"), file=f)
        cnt += 1
print(cnt)



