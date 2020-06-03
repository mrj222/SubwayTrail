# written by Yang Yixin
# deal with the original data

import folium

def classify_name():
    '''
        Categorize the data by user_ids
        In order to identify one's active path
    '''
    FILE = open('original_data/random_users_signals20170607.csv', 'r')
    cnt = 0
    x = FILE.readline()
    mp = dict()
    while 1:
        x = FILE.readline().strip('\n')
        if not x:
            break
        cell_id, dates, service_type, user_id, web = x.split(',')
        pos = mp.get(user_id)
        if not pos:
            cnt = cnt + 1
            mp[user_id] = 'data/' + str(cnt) + '.txt'
            pos = 'data/' + str(cnt) + '.txt'
            F = open(pos, 'w')
        else :
            F = open(pos, 'a')
        print(x, file=F)
        F.close()
    return cnt

def sort_time(cnt):
    '''
        Arrange the records according to time
    '''
    for i in range(cnt) :
        F = open('data/' + str(i + 1) + '.txt', 'r')
        x = F.read().splitlines()
        F.close()

        v = []
        for d in x :
            cell_id, dates, service_type, user_id, web = d.split(',')
            v.append([d, dates])
        v = sorted(v, key = lambda x : x[1])

        F = open('data/' + str(i + 1) + '.txt', 'w')
        for d in v :
            print(d[0], file = F)
        F.close()

def load_cell() :
    '''
        load cells' location from file
        return a dict addressed by cell_id
    '''
    FILE = open('original_data/cellIdSheet_baidu_hf.txt', 'r')
    x = FILE.read().splitlines()
    FILE.close()

    cell = dict()
    for d in x :
        cell_id, lon, lat, radius = d.split('\t')
        cell[cell_id] = {
            'position' : [float(lat), float(lon)],
            'radius' : float(radius)
        }
    return cell

def basic_map():
    Map = folium.Map(location=[31.83, 117.23], tiles = 'Stamen Toner', zoom_start=12)
    Map.add_child(folium.LatLngPopup())
    # Map.save('test.html')
    return Map

def draw_map(Map, node, color = 'blue'):
    flag = False
    last = None
    for d in node:
        folium.Circle(location = d[0], radius = d[1], fill = True, color = color).add_to(Map)
        if flag :
            folium.PolyLine(locations = [last[0], d[0]], color = color).add_to(Map)
            # folium.PolyLine(locations = [[(a + b) / 2 for a,b in zip(d[0], last[0])], last[0]], color = 'blue').add_to(Map)
        flag = True
        last = d
    # Map.save('test.html')
    return Map


def load_rail_station():
    FILE = open("original_data/rail_station(north_to_south).txt", 'r')
    x = FILE.read().splitlines()
    FILE.close()

    station = []
    for d in x :
        lat, lon = d.split(',')
        station.append([float(lat), float(lon)])

    return station
    
# sort_time(classify_name())