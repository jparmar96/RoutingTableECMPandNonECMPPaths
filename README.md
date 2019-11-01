# RoutingTableECMPandNonECMPPaths
1. Takes a show tech-support file as input. 
2. Looks for "show ip route vrf all detail" in the show-tech file.
4. Segregates ECMP and non-ECMP routes.
5. Writes the non-ecmp paths to an output file. 
6. For non-ecmp destinations, if next-hop can be Null0, directly connected or an ip address. (Please advise if I am missing any other type of next-hop here.)
7. The script works with ipv4 routes only.

Structure of output file: 
The script reads the show ip route summary from the show tech and puts that info in the output file. 
After this, the script segregates ecmp and non-ecmp routes and puts the count of them in the output file. 
After this, the script puts a table of (Non-ecmp Destination ---- Subnet mask ----- NextHop IP )
