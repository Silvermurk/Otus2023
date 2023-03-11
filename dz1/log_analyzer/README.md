# Log analyzer
Software that takes nginx-like logs in ./input dir and extracts first N lines
of urls that have maximum $request_time
* use --congig=path_to_json_file to add external configuration values
* Config example:
{
    "REPORT_SIZE": 80,
    "REPORT_DIR": "./output",
    "LOG_DIR": "./input",
    "SOME_DATA": "SomeData"
}
"REPORT_SIZE": Number of lines that will be in report, 
"REPORT_DIR": Output directory for reports
"LOG_DIR": Input folder where nginx logs are stationed
"SOME_DATA": Custom data field, in case you need to pass something else
------------------------------------------------------------------------------
# Run example
python -m log_analyzer.py --config=config.json

Returns html file of type report-YYY.MM.DD with REPORT_SIZE lines of urls with 
maximum $request_time in REPORT_DIR if any logs were found or analyzed
Will not analyze logs twice, if report with same date is present in REPORT_DIR
------------------------------------------------------------------------------
# Tests
Tests are located in log_analyzer_tests folder.
Tests require pytest to run.

* Run example for all rests
py.test log_analyzer_tests/test_log_analyzer.py
* Run example for single test
py.test log_analyzer_tests/test_log_analyzer.py -k 'test_name'

Tests cover bad input and output directories, config import and report_creator