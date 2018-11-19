#!/usr/bin/env python
"""
Simple FoundationDB exporter
"""

import argparse
import sys
import json
import threading
import time

import fdb
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY


# Set API version to first stable release
fdb.api_version(100)


def read_metrics(db):
    return db["\xff\xff/status/json"]


class FdbCollector(object):
    db = fdb.open()

    def collect(self):
        data = json.loads(read_metrics(self.db).decode())

        # https://github.com/apple/foundationdb/issues/398
        yield GaugeMetricFamily('fdb_workload_operations_reads_per_second',
            'Read operations per second',
            value=data['cluster']['workload']['operations']['reads']['hz'])

        yield GaugeMetricFamily('fdb_workload_operations_writes_per_second',
            'Total number of write operations',
            value=data['cluster']['workload']['operations']['writes']['hz'])

        yield CounterMetricFamily('fdb_workload_operations_writes_total',
            'Total number of write operations',
            value=data['cluster']['workload']['operations']['writes']['counter'])

        yield CounterMetricFamily('fdb_workload_transactions_committed_total',
            'Total number of committed transactions',
            value=data['cluster']['workload']['transactions']['committed']['counter'])

        yield CounterMetricFamily('fdb_workload_transactions_conflicted_total',
            'Total number of transaction conflicts',
            value=data['cluster']['workload']['transactions']['conflicted']['counter'])

        yield CounterMetricFamily('fdb_workload_transactions_started_total',
            'Total number of started transactions',
            value=data['cluster']['workload']['transactions']['started']['counter'])

        yield CounterMetricFamily('fdb_latency_read_seconds',
            'Time to perform a single read',
            value=data['cluster']['latency_probe']['read_seconds'])

        yield CounterMetricFamily('fdb_latency_commit_seconds',
            'Time to commit a sample transaction',
            value=data['cluster']['latency_probe']['commit_seconds'])


REGISTRY.register(FdbCollector())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=9444, type=int)
    args = parser.parse_args()

    print "Listening on 0.0.0.0:%d" % args.port

    # TODO: this starts a thread :(
    start_http_server(args.port)
    while True:
        time.sleep(1)
