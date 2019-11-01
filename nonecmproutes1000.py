#!/usr/bin/python2.7
from jsonrpclib import Server
import sys
import argparse
import os
import warnings
from pprint import pprint
import collections
import re
import json
from prettytable import PrettyTable


warnings.filterwarnings("ignore")

def is_valid_file(arg):
    #Checks if the arg is an actual file
    if not os.path.exists(arg):
        msg = "{0} is not a file or it does not exist".format(arg)
        raise argparse.ArgumentTypeError(msg)
    else:
        return arg

def parse_args():
    parser = argparse.ArgumentParser(
        epilog="This script takes an input config file and writes an output EOS config file.\
        Example: python translate.py -f filename")
    parser.add_argument("-f", "--filename", required=True,
                        help="input config file", metavar="FILE",
                        type=is_valid_file)
    args = parser.parse_args()
    return args

def readFile(filename):
    with open(filename) as f:
        lines = [line.strip() for line in f]
    return lines

def writeFile(filename, writeData):
    with open(filename + ".new", "w+") as f:
        f.write('\n'.join(str(line) for line in writeData))

def getRouteSummary(fileData):
    flag = 0
    routeSummary = []
    for line in fileData:
        if "show ip route vrf all summary" in line:
            flag = 1
        if not "show port numbering" in line and flag == 1:
            routeSummary.append(line)
        elif "show port numbering" in line and flag == 1:
            break
    return routeSummary

def getAllRoutes(fileData):
    flag = 0
    routes = []
    for line in fileData:
        if "show ip route vrf all detail" in line:
            flag = 1
        if not "show ip route host" in line and flag == 1:
            routes.append(line)
        elif "show ip route host" in line and flag == 1:
            break
    return routes

def segregateRoutes(routes):
    ecmpRoutes = {}
    nonEcmpRoutes = {}
    dict1 = {}
    subnetMask = {}
    for line in routes:
        matches = re.findall(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
        if len(matches) == 2:
            dict2 = {}
            dict2["NH"] = [matches[1]]
            previousDest = matches[0]
            subnetMatch = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/(\d{1,2})", line)
            dict2["SM"] = str(subnetMatch.group(1))

        if len(matches) == 1 and "via" in line:
            dict2["NH"].append(matches[0])

        if len(matches) == 2 and matches[0] not in dict1.keys():
            dict1[matches[0]] = dict2

        if len(matches) == 1 and ("directly connected" in line):
            if "Null0" in line:
                dict2 = {}
                dict2["NH"] = "Null0"
                subnetMatch = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/(\d{1,2})", line)
                dict2["SM"] = str(subnetMatch.group(1))
                if matches[0] not in dict1.keys():
                    dict1[matches[0]] = dict2
            else:
                dict2 = {}
                dict2["NH"] = "directly connected"
                subnetMatch = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/(\d{1,2})", line)
                dict2["SM"] = str(subnetMatch.group(1))
                if matches[0] not in dict1.keys():
                    dict1[matches[0]] = dict2

    #pprint (dict1)

    for dest, internalDict in dict1.items():
        dict2 = {}
        for attri , value in internalDict.items():
            if attri == "NH" and len(value) > 1 and "directly connected" not in value:
                dict2["NH"] = value
                dict2["SM"] = dict1[dest]["SM"]
                ecmpRoutes[dest] = dict2

            if attri == "NH" and value == "directly connected":
                dict2["NH"]  = "directly connected"
                dict2["SM"] = dict1[dest]["SM"]
                nonEcmpRoutes[dest] = dict2

            if attri == "NH" and value == "Null0":
                dict2["NH"]  = "Null0"
                dict2["SM"] = dict1[dest]["SM"]
                nonEcmpRoutes[dest] = dict2

            if attri == "NH" and len(value) == 1:
                dict2["NH"] = value
                dict2["SM"] = dict1[dest]["SM"]
                nonEcmpRoutes[dest] = dict2

    #return ecmpRoutes, nonEcmpRoutes
#    print("--------------------------------------------------------------------------")
#    pprint(nonEcmpRoutes)
#    print("--------------------------------------------------------------------------")

    table = PrettyTable(["Non-Ecmp Destination",  "Subnet Mask", "Nexthop IP"])

    for dest, dict3 in nonEcmpRoutes.items():
        table.add_row([dest,  nonEcmpRoutes[dest]["SM"], dict3["NH"]])

    numNonEcmp = len(nonEcmpRoutes.keys())
    numEcmp = len(ecmpRoutes.keys())

    print table
    return numNonEcmp, numEcmp, table

def main():
    if not sys.version_info[0] < 3:
        raise Exception("This script uses Python2. You tried to use Python3 or later version.")
        sys.exit(0)
    print("**********----------Starting main----------**********")
    args = parse_args()
    fileData = readFile(args.filename)
    writeData = []

    summary = []
    summary = getRouteSummary(fileData)
    for line in summary:
        writeData.append( line )
    writeData.append("------------------------------------------------------------------------------------- \n")

    routes = getAllRoutes(fileData)

    numNonEcmp, numEcmp, table = segregateRoutes(routes)

    print("Count of Non-ECMP routes: " + str(numNonEcmp) )
    print("Count of ECMP routes: " + str(numEcmp) )
    print("Total routes: " + str(numNonEcmp + numEcmp) )

    writeData.append("Count of Non-ECMP routes: " + str(numNonEcmp) )
    writeData.append("Count of ECMP routes: " + str(numEcmp) )
    writeData.append("Total routes: " + str(numNonEcmp + numEcmp) )
    writeData.append("\n \n ")


    writeFile(args.filename, writeData)

    table_txt = table.get_string()
    with open(args.filename + ".new", "a+") as f:
        f.write(table_txt)

#    print(writeData)
    print("**********----------Script complete----------**********")
    print("Input config file name: " + args.filename)
    print("Output config file name: " + args.filename + ".new")
    print("**********----------End----------**********")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
