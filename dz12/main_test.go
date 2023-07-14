package main

import (
    "testing"

    "github.com/golang/protobuf/proto"
    "github.com/Silvermurk/OTUSMemcload/appsinstalled"
)

type protoTestcase struct {
    lat  float64
    lon  float64
    apps []uint32
}

func areSlicesEqual(a, b []uint32) bool {
    if len(a) != len(b) {
        return false
    }

    for i := range a {
        if a[i] != b[i] {
            return false
        }
    }

    return true
}

func TestProto(t *testing.T) {
    cases := []protoTestcase{
        {42.345, 33.5677, []uint32{1, 2, 3}},
        {-42.345, 0.0, []uint32{100, 200, 300}},
        {-0.0, 100, nil},
        {0.0, 0.0, nil},
    }

    for _, tc := range cases {
        test := &appsinstalled.UserApps{
            Lon:  proto.Float64(tc.lon),
            Lat:  proto.Float64(tc.lat),
            Apps: tc.apps,
        }

        data, err := proto.Marshal(test)
        if err != nil {
            t.Errorf("marshaling error: %v", err)
        }

        newTest := &appsinstalled.UserApps{}
        if err := proto.Unmarshal(data, newTest); err != nil {
            t.Errorf("unmarshaling error: %v", err)
        }

        if *test.Lon != *newTest.Lon {
            t.Errorf("Lon-s are not equal: %v, %v", *test.Lon, *newTest.Lon)
        }

        if *test.Lat != *newTest.Lat {
            t.Errorf("Lat-s are not equal: %v, %v", *test.Lat, *newTest.Lat)
        }

        if !areSlicesEqual(test.Apps, newTest.Apps) {
            t.Errorf("Apps-s are not equal: %v, %v", test.Apps, newTest.Apps)
        }
    }
}

func TestParseRecordErrors(t *testing.T) {
    validCases := []string{
        "gaid\t123456\t24.567\t42.1344\t1,2,3,4,5",
        "aaa\t123456\t2\t4\t1",
        "bbb\ta      \t-9999\t0\t",
    }

    for _, tc := range validCases {
        _, err := ParseRecord(tc)
        if err != nil {
            t.Errorf("unexpected error for valid record %q: %v", tc, err)
        }
    }

    invalidCases := []string{
        "",
        "gaid\t123456\t24.56742.1344\t1,2,3,4,5",
        "aaa\t123456\tasd\t4\t1",
        "bbb\ta      \t-9999\ta\t",
        "aaa\t-9999\ta\t",
    }

    for _, tc := range invalidCases {
        _, err := ParseRecord(tc)
        if err == nil {
            t.Errorf("expected error for invalid record %q, but got none", tc)
        }
    }
}

func TestParseRecord(t *testing.T) {
    cases := []struct {
        input    string
        expected Record
    }{
        {
            input: "gaid\t123456\t24.567\t42.1344\t1,2,3,4,5",
            expected: Record{
                Type: "gaid",
                ID:   "123456",
                Lat:  24.567,
                Lon:  42.1344,
                Apps: []uint32{1, 2, 3, 4, 5},
            },
        },
        {
            input: "aaa\t123456\t2\t4\t1",
            expected: Record{
                Type: "aaa",
                ID:   "123456",
                Lat:  2.0,
                Lon:  4.0,
                Apps: []uint32{1},
            },
        },
        {
            input: " \t111\t0\t0\t   ",
            expected: Record{
                Type: " ",
                ID:   "111",
                Lat:  0.0,
                Lon:  0.0,
                Apps: []uint32{},
            },
        },
    }

    for _, tc := range cases {
        record, err := ParseRecord(tc.input)
        if err != nil {
            t.Errorf("unexpected error for valid record %q: %v", tc.input, err)
            continue
        }

        if record.Type != tc.expected.Type {
            t.Errorf("Types are not equal: %q, %q", record.Type, tc.expected.Type)
        }

        if record.ID != tc.expected.ID {
            t.Errorf("IDs are not equal: %q, %q", record.ID, tc.expected.ID)
        }

        if record.Lat != tc.expected.Lat {
            t.Errorf("Lats are not equal: %v, %v", record.Lat, tc.expected.Lat)
        }

        if record.Lon != tc.expected.Lon {
            t.Errorf("Lons are not equal: %v, %v", record.Lon, tc.expected.Lon)
        }

        if !areSlicesEqual(record.Apps, tc.expected.Apps) {
            t.Errorf("Apps-s are not equal: %v, %v", record.Apps, tc.expected.Apps)
        }
    }
}