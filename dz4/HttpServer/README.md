# Simple HTTP server
The server uses multiple threads to handle requests. Number of threads is optional (4 by default).
The server supports only GET / HEAD requests and serves static files in specified document root.

## **Requirements**
* Python 3.8+

## **Installation**
```
git clone https://github.com/Silvermurk/Otus2023.git
cd dz4/HttpServer
python main.py
```

## **Tests**
```
python3 -m dz4.tests
```

## **To run HTTP-server**
```
python3.8 -m httpserver --root /path/to/document/root --port 8080 --workers 10
```

## **ApacheBench (ab) test for 100 workers**
```
ab -n 50000 -c 100 -r http://localhost:80/
This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Server Software:        Fancy-Python-HTTP-Server
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        13 bytes

Concurrency Level:      100
Time taken for tests:   1438.245 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      8750000 bytes
HTML transferred:       650000 bytes
Requests per second:    34.76 [#/sec] (mean)
Time per request:       2876.490 [ms] (mean)
Time per request:       28.765 [ms] (mean, across all concurrent requests)
Transfer rate:          5.94 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0   29 116.2      0     511
Processing:     6 2841 255.6   3019    3532
Waiting:        2 1905 633.9   2015    3031
Total:        503 2870 249.4   3020    3532

Percentage of the requests served within a certain time (ms)
  50%   3020
  66%   3021
  75%   3021
  80%   3022
  90%   3023
  95%   3024
  98%   3027
  99%   3520
 100%   3532 (longest request)
```
