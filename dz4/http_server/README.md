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
python3.8 -m httpserver --root /path/to/document/root --port 8080 --workers 4
```

## **ApacheBench (ab) test for 100 workers**
```
PS E:\Work\Otus2023\dz4\http_server> ab -n 50000 -c 100 -r http://localhost:8080/
This is ApacheBench, Version 2.3 <$Revision: 1903618 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)
Completed 5000 requests
Completed 10000 requests
Completed 15000 requests
Completed 20000 requests
Completed 25000 requests
Completed 30000 requests
Completed 35000 requests
Completed 40000 requests
Completed 45000 requests
Completed 50000 requests
Finished 50000 requests


Server Software:        Fancy-Python-HTTP-Server
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        29 bytes

Concurrency Level:      100
Time taken for tests:   22.799 seconds
Complete requests:      50000
Failed requests:        0
Total transferred:      9150000 bytes
HTML transferred:       1450000 bytes
Requests per second:    2193.06 [#/sec] (mean)
Time per request:       45.598 [ms] (mean)
Time per request:       0.456 [ms] (mean, across all concurrent requests)
Transfer rate:          391.92 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.3      0       4
Processing:     2   41   3.1     41     106
Waiting:        1   41   3.1     41     105
Total:          2   42   3.1     41     106

Percentage of the requests served within a certain time (ms)
  50%     41
  66%     41
  75%     42
  80%     43
  90%     45
  95%     47
  98%     50
  99%     51
 100%    106 (longest request)

```
