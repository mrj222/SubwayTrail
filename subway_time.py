# written by Miao Ruijie

from typing import Any, Union

import numpy as np
import math
from datetime import datetime, timedelta
from datetime import timedelta

from data import  load_rail_station
from trail import distance

subway_velocity = 30 * 1000 / (60 * 60) # the average velocity of the subway
common_interval = 8 * 60 + 45 # the interval of two next trip not in peak time
peak_interval = 6 * 60 + 58 # the interval of two next trip in peak time
standard_time = datetime(2017, 6, 7, 17, 0, 0)

morning_peak_start = datetime(2017, 6, 7, 7, 0, 0)
morning_peak_end = datetime(2017, 6, 7, 9, 0, 0)
evening_peak_start = datetime(2017, 6, 7, 17, 0, 0)
eveing_peak_end = datetime(2017, 6, 7, 19, 0, 0)


def user_schedule(): # load schedule of station and its arrive time
    '''
    :return: [forward_schedule, backward_schedule], forward_schedule is the movement of usr go from No. a to No. b,
        where a < b, and backward_schedule otherwise
    '''
    # file = open("result/ans.txt", 'r')
    file = open('result/usr_subway.txt', 'r')
    forward_schedule = []
    backward_schedule = []
    while 1:
        x = file.readline().strip('\n')
        if not x:
            break
        x = x.split(' ')
        # print(x)
        user = int(x[1])
        # start_station = int(x[3].strip('[').strip(','))
        start_station = int(x[3])
        # end_station = int(x[4].strip(']'))
        end_station = int(x[5])
        start_time = datetime.strptime(x[7]+' '+x[8], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(x[10]+' ' + x[11], '%Y-%m-%d %H:%M:%S')
        if start_station < end_station :
            forward_schedule.append([user, start_station, start_time])
            forward_schedule.append([user, end_station, end_time])
        else :
            backward_schedule.append([user, start_station, start_time])
            backward_schedule.append([user, end_station, end_time])
    file.close()
    return [forward_schedule, backward_schedule]


def station_distance(): # calculate the adjacent station distance
    station_dist = []
    station = load_rail_station()
    for i in range(22):
        station_dist.append(distance(station[i], station[i+1]))
    return station_dist


def subway_start_time(start_station_id, schedule): # estimate the start time of subway in the trip
    station_dist=station_distance()
    start_time = []
    for user, station_id, arrive_time in schedule:
        if station_id > start_station_id:
            Distance = sum(station_dist[:station_id])
        else:
            Distance = sum(station_dist[station_id:])
        t = arrive_time - timedelta(seconds=Distance / subway_velocity)
        if t < standard_time:
            if t < morning_peak_start:
                delta_t = math.ceil((morning_peak_start - t).seconds / common_interval)
                t += timedelta(seconds=delta_t*common_interval)
            if t < morning_peak_end:
                delta_t = math.ceil((morning_peak_end - t).seconds / peak_interval)
                t += timedelta(seconds=delta_t*peak_interval)
            if t < evening_peak_start:
                delta_t = math.ceil((evening_peak_start - t).seconds / common_interval)
                start_time.append([user, t + timedelta(seconds=delta_t*common_interval)])
        else:
            if t > eveing_peak_end:
                delta_t = math.floor((t - eveing_peak_end).seconds / common_interval)
                t -= timedelta(seconds=delta_t * common_interval)

            delta_t = math.floor((t - evening_peak_start).seconds / peak_interval)
            start_time.append([user, t - timedelta(seconds=delta_t* peak_interval)])
    return start_time


def get_max_interval(time, interval_len=40, max_len=peak_interval):
    '''
    :return:
    max_cnt: the max number of trails that agree with the output schedule
    max_left, max_right: [17:00:00 + seconds=(max_left), 17:00:00 + seconds=(max_right)] is the best interval
    '''
    time.sort()
    max_cnt = 0
    max_left = max_right = 0
    for i in range(len(time)):
        cnt = 0
        left = time[i]
        for j in range(i, len(time)):
            if time[j] - time[i] > interval_len:
                break
            cnt += 1
            right = time[j]
        if cnt > max_cnt:
            max_cnt = cnt
            max_left = left
            max_right = right

    block = (interval_len - (max_right - max_left))/2
    if block > max_left:
        max_left = 0
        max_right = interval_len
    elif block > (max_len - max_right):
        max_right = max_len
        max_left = max_right - interval_len
    else:
        max_left -= block
        max_right -= block

    return max_cnt, max_left, max_right


print('schedule loading')
[f_schedule, b_schedule] = user_schedule()
print(len(f_schedule))
print(len(b_schedule))
f_start_time = subway_start_time(0, f_schedule)
# b_start_time = subway_start_time(22, b_schedule)
# start_time = f_start_time + b_start_time

over_time = []
user_overtime = []
for user, t in f_start_time:
    over_time.append((t-standard_time).seconds)
    user_overtime.append([user, (t-standard_time).seconds])

'''
F = open('overtime2.txt', 'a')
for t in over_time:
    print(t, file=F) 
F.close()
'''

max_cnt, max_l, max_r = get_max_interval(over_time)

# output the the usr_num that agree with the time schedule
F = open('result/user.txt', 'w+')
for usr, t in user_overtime:
    if max_l <= t <= max_r:
        print(usr, file=F)
F.close()

# print the
print(max_cnt, max_l, max_r)


