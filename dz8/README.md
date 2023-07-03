# MemcLoad
The intent of this program is to use Python's multiprocessing module for parsing 
log files (see `sample.tsv.gz`) and caching parsed lines to Memcached.

## **Requirements**
* Python 3.10
* protobuf==3.10.0
* python-memcached==1.59
* six==1.12.0
* memcache==0.12.0

## **Installation**
```
pip install -r requirements.txt
```

## **Tests**
```
python -m memcload.test
```

## **Examples**
Heplp command:
```
python -m memcload --help
```

Dry run:
```
python -m memcload --dry --pattern="./memcload/*.tsv.gz"
```

Test if Memcached is running:
```
python -m memcload --pattern="/path/to/logs/*.tsv.gz"
```
