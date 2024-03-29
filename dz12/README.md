# otus-go-memcload
Go (golang) version of
[MemcLoad](https://github.com/Silvermurk/Otus2023/dz12) Python script. Program parses log records from files (compressed with **gzip**) specified by a glob pattern. Parsed records are serialized with [Protocol Buffers](https://developers.google.com/protocol-buffers/docs/overview) and saved into Memcached storage.

Each line in a log file is a set of 5 tab-separated values, for example:
```
dvid\t63d3\t137.449673958\t89.8917375112\t3553,2919,7602
adid\tad12\t160.372422867\t-49.1875693538\t7848,8357
...
device_type\tdevice_id\latitude\longitude\installed_app_ids
```

Complete example of a log file is *sample.tsv.gz*

# Requirements
* Go (golang)
* Memcached

# Installation
Make sure you have **Go** installation on your system 
(https://golang.org/doc/install)

Prepare working directory:
```bash
mkdir $HOME/otus-memcload && cd $HOME/otus-memcload
export GOPATH=$HOME/otus-memcload
```

Get package:
```bash
go get -v github.com/Silvermurk/Otus2023/dz12
```

Run tests:
```bash
go test github.com/Silvermurk/Otus2023/dz12
```

Install:
```bash
go install github.com/Silvermurk/Otus2023/dz12
```

# Examples

To get help:
```bash
./bin/otus-go-memcload --help
```

To process the sample log file in "dry" mode:
```
cp ./src/github.com/Silvermurk/Otus2023/dz12/sample.tsv.gz .
./bin/otus-go-memcload --pattern "*.tsv.gz" --dry --debug
```

To run Memcached:
```bash
memcached -l 0.0.0.0:33013,0.0.0.0:33014,0.0.0.0:33015,0.0.0.0:33016
```

To process the sample log file and save records from it to Memcached (make sure it's running):
```
cp ./src/github.com/Silvermurk/Otus2023/dz12/sample.tsv.gz .
./bin/otus-go-memcload --pattern "*.tsv.gz"
```

# Comparison with the implementation in Python
Original implementation in Python may be found [here](https://github.com/Silvermurk/Otus2023/dz12)

Testing data: https://disk.yandex.ru/d/OXF7Yqvi2tJmsw

Both implementations are tested with `time` command.

x | Dry                                            | Memcached
--- |------------------------------------------------| ---
**Go** | 30,91s user 0,53s system 337% cpu 8,927 total  | 30,86s user 21,57s system 189% cpu 26,226 total
**Python** | 49,35s user 0,61s system 312% cpu 22,141 total | 69,94s user 23,11s system 228% cpu 58,632 total
