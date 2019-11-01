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
        if not "show flowcontrol" in line and flag == 1:
            routes.append(line)
        elif "show flowcontrol" in line and flag == 1:
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
            dict1[matches[0]] = [matches[1]]
            previousDest = matches[0]
            subnetMatch = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/(\d{1,2})", line)
            subnetMask[matches[0]] = str(subnetMatch.group(1))
        if len(matches) == 1 and "via" in line:
            dict1[previousDest].append(matches[0])
        if len(matches) == 1 and "directly connected" in line:
            dict1[matches[0]] = "directly connected"

    for key, value in dict1.items():
        if value == "directly connected":
            nonEcmpRoutes[key] = "directly connected"
        if len(value) > 1 and "directly connected" not in value:
            ecmpRoutes[key] = value
        if len(value) == 1 and "directly connected" not in value:
            nonEcmpRoutes[key] = value

    pprint(ecmpRoutes)
    print("--------------------------------------------------------------------------")
    pprint(nonEcmpRoutes)
    print("--------------------------------------------------------------------------")
    pprint(subnetMask)

    #pprint(dict1)
    #return ecmpRoutes, nonEcmpRoutes

    print("\n \n Table of non-ECMP routes:")
    table = PrettyTable(["Destination", "Nexthops"])
    for key, value in nonEcmpRoutes.items():
        table.add_row([key, value])

    print table

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


    routes = getAllRoutes(fileData)

    segregateRoutes(routes)


    writeFile(args.filename, writeData)
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
