package main

import (
	"bufio"
	"compress/gzip"
	"context"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/bradfitz/gomemcache/memcache"
)

const (
	MaxConcurrentWorkers        = 5
	MaxMemcacheConnectRetries   = 3
	AcceptableInvalidRecordRate = 0.2
)

type Client struct {
	Conn *memcache.Client
	Addr string
}

type Job struct {
	Clients []Client
	File    string
	Dry     bool
	Index   int
}

type Options struct {
	Pattern string
	IDFA    string
	GAID    string
	ADID    string
	DVID    string
	Dry     bool
	Debug   bool
}

type Logger interface {
	Debugf(format string, args ...interface{})
	Infof(format string, args ...interface{})
	Warnf(format string, args ...interface{})
	Errorf(format string, args ...interface{})
}

type logrusLogger struct {
	logger *log.Logger
}

func (l *logrusLogger) Debugf(format string, args ...interface{}) {
	if l.logger != nil {
		l.logger.Printf(format, args...)
	}
}

func (l *logrusLogger) Infof(format string, args ...interface{}) {
	if l.logger != nil {
		l.logger.Printf(format, args...)
	}
}

func (l *logrusLogger) Warnf(format string, args ...interface{}) {
	if l.logger != nil {
		l.logger.Printf(format, args...)
	}
}

func (l *logrusLogger) Errorf(format string, args ...interface{}) {
	if l.logger != nil {
		l.logger.Printf(format, args...)
	}
}

func parseCommandLine() (string, Options) {
	var options Options
	flag.StringVar(&options.Pattern, "pattern", "/data/appsinstalled/*.tsv.gz", "pattern to match log files")
	flag.StringVar(&options.IDFA, "idfa", "localhost:33013", "Memcached server address for IDFA")
	flag.StringVar(&options.GAID, "gaid", "localhost:33014", "Memcached server address for GAID")
	flag.StringVar(&options.ADID, "adid", "localhost:33015", "Memcached server address for ADID")
	flag.StringVar(&options.DVID, "dvid", "localhost:33016", "Memcached server address for DVID")
	flag.BoolVar(&options.Dry, "dry", false, "dry run")
	flag.BoolVar(&options.Debug, "debug", false, "debug mode")
	flag.Parse()
	return flag.Arg(0), options
}

func connectMemcache(addr string) (*memcache.Client, error) {
	var conn *memcache.Client
	var err error

	for i := 1; i <= MaxMemcacheConnectRetries; i++ {
		conn, err = memcache.New(addr)
		if err == nil {
			return conn, nil
		}
		time.Sleep(time.Duration(i*100) * time.Millisecond)
	}

	return nil, fmt.Errorf("failed to connect to memcached server %s after %d retries", addr, MaxMemcacheConnectRetries)
}

func connectClients(options Options) []Client {
	clients := []Client{}
	for _, addr := range []string{options.IDFA, options.GAID, options.ADID, options.DVID} {
		conn, err := connectMemcache(addr)
		if err != nil {
			log.Fatalf("Error connecting to memcache server %s: %s", addr, err)
		}
		client := Client{Conn: conn, Addr: addr}
		clients = append(clients, client)
	}
	return clients
}

func processFile(clients []Client, filename string, dry bool, results chan<- int, logger Logger) {
	logger.Infof("Processing file %s...", filename)

	f, err := os.Open(filename)
	if err != nil {
		logger.Errorf("Error opening file %s: %s", filename, err)
		results <- -1
		return
	}
	defer f.Close()

	gz, err := gzip.NewReader(f)
	if err != nil {
		logger.Errorf("Error creating gzip reader for file %s: %s", filename, err)
		results <- -1
		return
	}
	defer gz.Close()

	reader := bufio.NewReader(gz)
	lineNumber := 0
	invalidRecords := 0

	for {
		line, err := reader.ReadString('\n')
		if err == io.EOF {
			break
		}
		if err != nil {
			logger.Errorf("Error reading file %s: %s", filename, err)
			results <- -1
			return
		}

		line(cont'd)

		lineNumber++

		fields := strings.Split(strings.TrimSpace(line), "\t")
		if len(fields) != 5 {
			logger.Warnf("Invalid record in file %s at line %d: %s", filename, lineNumber, line)
			invalidRecords++
			continue
		}

		lat, err := strconv.ParseFloat(fields[1], 64)
		if err != nil {
			logger.Warnf("Invalid latitude in file %s at line %d: %s", filename, lineNumber, fields[1])
			invalidRecords++
			continue
		}

		lon, err := strconv.ParseFloat(fields[2], 64)
		if err != nil {
			logger.Warnf("Invalid longitude in file %s at line %d: %s", filename, lineNumber, fields[2])
			invalidRecords++
			continue
		}

		var id string
		switch fields[3] {
		case "idfa":
			id = fields[4]
		case "gaid":
			id = "g" + fields[4]
		case "adid":
			id = "a" + fields[4]
		case "dvid":
			id = "d" + fields[4]
		default:
			logger.Warnf("Invalid device type in file %s at line %d: %s", filename, lineNumber, fields[3])
			invalidRecords++
			continue
		}

		mc := clients[int(id[0])%len(clients)]

		key := fmt.Sprintf("%s:%s", id, filepath.Base(filename))
		value := fmt.Sprintf("%.6f,%.6f", lat, lon)

		if !dry {
			err = mc.Conn.Set(&memcache.Item{Key: key, Value: []byte(value)})
			if err != nil {
				logger.Errorf("Error writing to memcache server %s: %s", mc.Addr, err)
				results <- -1
				return
			}
		} else {
			logger.Debugf("Dry run: would write key=%s, value=%s to memcache server %s", key, value, mc.Addr)
		}
	}

	if float64(invalidRecords)/float64(lineNumber) > AcceptableInvalidRecordRate {
		logger.Warnf("Too many invalid records in file %s: %d out of %d", filename, invalidRecords, lineNumber)
		results <- -1
	} else {
		logger.Infof("Processed file %s: %d records, %d invalid", filename, lineNumber, invalidRecords)
		results <- lineNumber
	}
}

func main() {
	log.SetFlags(log.LstdFlags | log.Lmicroseconds)

	filename, options := parseCommandLine()

	var logger Logger
	if options.Debug {
		logger = &logrusLogger{logger: log.New(os.Stdout, "", log.LstdFlags|log.Lmicroseconds)}
	} else {
		logger = &logrusLogger{}
	}

	logFiles, err := filepath.Glob(filename)
	if err != nil {
		logger.Errorf("Error matching files with pattern %s: %s", filename, err)
		os.Exit(1)
	}
	if len(logFiles) == 0 {
		logger.Error("No files found")
		os.Exit(1)
	}

	clients := connectClients(options)

	jobs := make(chan Job, len(logFiles))
	results := make(chan int, len(logFiles))

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go func() {
		<-time.After(5 * time.Minute)
		logger.Error("Timeout exceeded")
		cancel()
	}()

	go func() {
		c := make(chan os.Signal, 1)
		signal.Notify(c, os.Interrupt)
		<-c
		logger.Error("Interrupted")
		cancel()
	}()

	var wg sync.WaitGroup

	for i := 0; i < MaxConcurrentWorkers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for job := range jobs {
				logger.Infof("[%d] Processing %s...", job.Index, job.File)
				processFile(job.Clients, job.File, job.Dry, results, logger)
			}
		}()
	}

	for i, logfile := range logFiles {
		jobs <- Job{Clients: clients, File: logfile, Dry: options.Dry, Index: i}
		select {
		case <-ctx.Done():
			logger.Error("Aborted")
			os.Exit(1)
		default:
		}
	}

	close(jobs)
	go func() {
		wg.Wait()
		close(results)
	}()

	processedFiles := 0
	invalidFiles := 0
	for result := range results {
		processedFiles++
		if result == -1 {
			invalidFiles++
		}
	}

	if processedFiles == 0 {
		logger.Error("No files processed")
		os.Exit(1)
	}