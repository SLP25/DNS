
# Domain Name System

## Common Architecture

A minimum of 3 threads:

- 1 thread receiving UDP packets
- 1 thread sending UDP packets
- 1+ threads processing said packets

This can allow a neat way to code multiple servers in one codebase using inheritance.

## SP

###  DNS Queries
```
def processPacket :
	if not SP for domain:
		if interactive request:
		  send address of ST
	  else if recurvise:
		  request info to ST
		  send info-

  if entry not found:
	  send error
	
	send entry
```

### Zone transfers

```
def zoneTransfer:
	if SS not authorized:
		send error
  
  if not SP for domain
	  send error

	switch type of request:
		case 0:
			send version number
		case 2:
			send number of entries
		case 4:
			foreach entry:
				send entry
		otherwise:
			send error: bad request
```

## SS

###  Startup

```
def init :
	foreach domain:
		fetch db
```

###  DNS Queries
```
def processPacket :
	if not SS for domain:
		if interactive request:
		  send address of ST
	  else if recurvise:
		  request info to ST
		  send info

  if entry not found:
	  send error
	
	send entry
```


###  Zone transfer

```
X = .... #Amount of time between zone transfers
def zoneTransfer :
	run once every X seconds:
		foreach domain:
			request DB version
			if version >= our version:
				fetch db
```


## SR

###  Startup

###  DNS Queries
```
def processPacket :
	if in cache:
		send value | error if not exists

  determine next server to ask
	if interactive request:  
		send address of server  
	else if recurvise:  
		request info to server 
	send info
```

## Config Files
Stored in memory the same as cache


## SP Data

### DEFAULT
The DEFAULT macros are replaced before processing the file. The macros are processed in FIFO manner, meaning top macros are replaced first.

### Literally everything else

Class: DNSEntry
		 - Parameter
          - Record Type
          - Value (union of all possible types)
          - TTL
          - Priority

## Logging

### Debug

### Production

## DNS Packet

###  Header

|     Component         | Message Id | Flags     | Response Code     | Number of Values     | Number of Authorities    | Number of Extra Values     |
| :---:        |    :----:   | :---: |  :---: |   :---: |  :---: |   :---: |
| Possible values     | 1 - 65536 (fisicamente 0-65535)      | Q,R,A   | 0-3 | 0-255 | 0-255 | 0-255
| Size (bits)   | 16       | 3      | 2 | 8 | 8 | 8

### Data

|     Name         | Type of Values | Response Values     | Authorities Values     | Number of Extra Values     ||
| :---:        |    :----:   | :---: |  :---: |   :---: |  :---: |
| Possible values     | string      | DNS Entry  | DNS Entry | DNS Entry
| Size (bits)   | variable      | DNS Entry| DNS Entry | DNS Entry

### Allowed Types

- SOASP
- SOAADMIN
- SOASERIAL
- SOARETRY
- SOAEXPIRE
- NS
- A
- CNAME
- MX
- PTR

### DNS Entry

|    Parameter         | Type of Value | Value     | TTL     | Piority       | 
| :---:        |    :----:   | :---: |  :---: |   :---: |
| Possible values     | Type     | String/Ipv4/Ipv6   | 0-2^32-1 | 0-255 
| Size (bits)   | 4   | Variable/32/128 | 32 | 8 


## Cache
 
Every server will implement a positive and negative cache. The cache will consist of a hash table of 
```
(Name, Type Of Value) -> Maybe Entry
```

If an entry is not in cache, no key should exist in the hash table. 

## Zone Transfer

1. SS queries, for each domain it has information about, its SP's once every X seconds
2. If the SS is authorized, the SP returns its database version number, if not, returns an error
3. If the version in SP is greater than the one in the SS, SS requests the database from the SP
4. SP sends the number of entries
5. SS acknowledges
6. SP starts sending the data, one entry per packet

### Packet format

The generic format of the packet is
| Header      | Data     |
| :---        |    :----:   |

The header has the following format

| Sequence Number (3 bits) | Status (2 bits) |
| :---        |    :----:   |

The sequence number is the part of the communication in progress:

| Sequence Number    | Description |
| :---        |    :----:   |  
| 0     | SS requests version number for given domain      |
| 1   | SP returns the version number of the requested domain        | 
| 2   | SS requests the database of a domain        | 
| 3   | SP returns the number of entries to expect       |
| 4   | SS acknowledges the number of entries to expect       |
| 5   | SP sends the database, one entry at a time       |


| Status    | Description |
| :---        |    :----:   |  
| 0     | Success      |
| 1   | Unauthorized        | 
| 2   | No such domain        | 

In case of error, no data is sent. The data part of the packet depends on the sequence number.

### 0/2
The data is a string containing the name of the domain

### 1/3/4
The data is a 32-bit integer corresponding to the version number

### 5
The data is a 16-bit integer corresponding to the number of the entry, and a DNS entry, as described before


## Questions
1. Do we have to hardcode the value of X in the zone transfer protocol or can it be passed as a config variable?
2. How to implement cache drop?
3. Alignment on packets
4. What security information on SS?
5. How to handle subdomains?
6. Which DNS records do we have to send?
7. How to determine if we are the first server
8. How to handle colisions
