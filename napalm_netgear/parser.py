import re


def parseFixedLenght(fields, data):
    cell_start = []
    cell_end = []
    res = []
    for a in data:
        if(a.startswith("-")):
            if(len(cell_start) > 0):
                break
            in_cell = False
            for i in range(len(a)):
                if(a[i] == "-" and in_cell is False):
                    cell_start.append(i)
                    in_cell = True
                if(a[i] == " " and in_cell is True):
                    cell_end.append(i)
                    in_cell = False
            if(in_cell):
                cell_end.append(len(a))
            continue

        if(len(cell_start) == 0):
            continue

        item = {}
        for i in range(len(fields)):
            if(fields[i] == ""):
                continue
            item[fields[i]] = a[cell_start[i]:cell_end[i]].strip()
        res.append(item)
    return res


def parseList(data):
    pattern = r"^([^.]+)\.+ (.*)$"
    res = {}
    for line in data:
        match = re.search(pattern, line)
        if(match):
            res[match.group(1).strip()] = match.group(2).strip()
    return res


if __name__ == '__main__':
    data="""(M4250-26G4XF-PoE+)#show interfaces status all

                                   Link    Physical    Physical    Media       Flow
Port       Name                    State   Mode        Status      Type        Control     VLAN
---------  ----------------------  ------  ----------  ----------  ----------  ----------  ----------
0/1                                Down    Auto                                        Inactive     Trunk
0/2                                Down    Auto                                        Inactive     Trunk
0/3                                Down    Auto                                        Inactive     Trunk
0/4                                Down    Auto                                        Inactive     Trunk
0/5                                Down    Auto                                        Inactive     Trunk
0/6                                Down    Auto                                        Inactive     Trunk
0/7                                Down    Auto                                        Inactive     Trunk
0/8                                Down    Auto                                        Inactive     Trunk
0/9                                Down    Auto                                        Inactive     Trunk
0/10                               Down    Auto                                        Inactive     Trunk
0/11                               Down    Auto                                        Inactive     Trunk
0/12                               Down    Auto                                        Inactive     Trunk
0/13                               Down    Auto                                        Inactive     Trunk
0/14                               Down    Auto                                        Inactive     Trunk
0/15                               Down    Auto                                        Inactive     Trunk
0/16                               Down    Auto                                        Inactive     Trunk
0/17                               Down    Auto                                        Inactive     Trunk
0/18                               Down    Auto                                        Inactive     Trunk
0/19                               Down    Auto                                        Inactive     Trunk
0/20                               Down    Auto                                        Inactive     Trunk
0/21                               Down    Auto                                        Inactive     Trunk
0/22                               Down    Auto                                        Inactive     Trunk
0/23                               Down    Auto                                        Inactive     Trunk
0/24                               Down    Auto                                        Inactive     Trunk
0/25                               Down    Auto                                        Inactive     Trunk
0/26                               Down    Auto                                        Inactive     Trunk
0/27                               Down    10G Full                                    Inactive     Trunk
0/28                               Down    10G Full                                    Inactive     Trunk
0/29                               Down    10G Full                                    Inactive     Trunk
0/30                               Up      10G Full    10G Full    10GBase-LR          Inactive     Trunk
lag 1                              Down                                                             1
lag 2                              Down                                                             1
lag 3                              Down                                                             1
lag 4                              Down                                                             1
lag 5                              Down                                                             1
lag 6                              Down                                                             1
lag 7                              Down                                                             1
lag 8                              Down                                                             1
lag 9                              Down                                                             1
lag 10                             Down                                                             1
lag 11                             Down                                                             1
lag 12                             Down                                                             1
lag 13                             Down                                                             1
lag 14                             Down                                                             1
lag 15                             Down                                                             1
lag 16                             Down                                                             1
lag 17                             Down                                                             1
lag 18                             Down                                                             1
lag 19                             Down                                                             1
lag 20                             Down                                                             1
lag 21                             Down                                                             1
lag 22                             Down                                                             1
lag 23                             Down                                                             1
lag 24                             Down                                                             1
vlan 1                             Up      10 Half     10 Half     Unknown
vlan 4000                          Up      10 Half     10 Half     Unknown

(M4250-26G4XF-PoE+)# """
    #print(parseFixedLenght(["name","label","state","","speed"],data.split("\n")))

    data = """(M4250-26G4XF-PoE+)#show interface 0/1

Packets Received Without Error................. 0
Packets Received With Error.................... 0
Broadcast Packets Received..................... 0
Receive Packets Discarded...................... 0
Packets Transmitted Without Errors............. 0
Transmit Packets Discarded..................... 0
Transmit Packet Errors......................... 0
Collision Frames............................... 0
Number of link down events..................... 0
Load Interval.................................. 300
Received Rate(Mbps)............................ 0.0
Transmitted Rate(Mbps)......................... 0.0
Received Error Rate............................ 0
Transmitted Error Rate......................... 0
Packets Received Per Second.................... 0
Packets Transmitted Per Second................. 0
Percent Utilization Received................... 0%
Percent Utilization Transmitted................ 0%
Link Flaps..................................... 0
Time Since Counters Last Cleared............... 11 day 1 hr 50 min 29 sec

(M4250-26G4XF-PoE+)# """
    print(parseList(data.split("\n")))
