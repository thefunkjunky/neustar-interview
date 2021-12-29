#!/usr/bin/env python3
"""
Samples the last 20 lines of a log file matching pattern:

[2021-07-01 16:49:17,440] INFO Ultradns quiz application took 25 ms

then parses app launch latencies and returns the average and
standard deviation.
"""

import re
import argparse
import pathlib
import json
from typing import Union, List, Tuple


def mean_and_stddev(latencies: List[int]) -> Tuple[float, float]:
  """Takes a list of app launch latencies (in ms) and returns
  a tuple of: (mean, standard_deviation). Returns (None, None)
  if launch_latencies list is empty.
  """
  if not latencies:
    return (None, None)
  mean = sum(latencies) / len(latencies)
  variance = sum([((x - mean) ** 2) for x in latencies]) / len(latencies)
  stddev = variance ** 0.5
  return (mean, stddev)


def parse_launch_latency(
  log_entry: str
  ) -> int:
  """Parses the app launch latency in a log entry and returns the value in ms.
  Pattern regex is "took[ ]*(\\d+)[ ]*(ms|s|m)"."""
  pattern = r"took[ ]*(\d+)[ ]*(ms|s|m)"
  regex = re.compile(pattern)
  matches = re.findall(regex, log_entry)

  if not matches:
    return None

  time = int(matches[0][0])
  time_unit = matches[0][1]
  if time_unit == "s":
    time_ms = time * 1000
  elif time_unit == "m":
    time_ms = time * 60 * 1000
  elif time_unit == "ms":
    time_ms = time

  return time_ms


def sample_logs(
  log_path: Union[str, pathlib.Path],
  match_string: str,
  sample_size: int
  ) -> List[str]:
  """Returns last {sample_size} entries in log matching pattern:

  [2021-07-01 16:49:17,440] INFO {match_string} took 25 ms
  """

  with open(log_path, "r") as f:
    logs = f.readlines()

  match_logs_list = [
    log for log in logs
    if match_string in log
    and parse_launch_latency(log)]

  if sample_size > len(match_logs_list):
    return match_logs_list
  else:
    return match_logs_list[:-sample_size-1:-1]
  return match_logs_list


def main():
  """Main function"""
  parser = argparse.ArgumentParser(
    description="Parse log and return mean/stddev "
    "of application launch latencies."
    )
  parser.add_argument(
    "log_path",
    type=str,
    help="Location of log file to parse."
  )
  parser.add_argument(
    "--match_string",
    type=str,
    default="Ultradns quiz application",
    help="Log entries string to match."
    )
  parser.add_argument(
    "--sample_size",
    type=int,
    default=20,
    help="Number of most recent log entries to sample."
    )
  parser.add_argument(
    "--json",
    action="store_true",
    help="Output mean and stddev as machine readable json."
    )
  args = parser.parse_args()

  match_logs = sample_logs(args.log_path, args.match_string, args.sample_size)
  latencies = [parse_launch_latency(log) for log in match_logs]
  app_launch_mean, app_launch_stddev = mean_and_stddev(latencies)
  if args.json:
      data_dict = {
        "app_launch_latency_mean_ms": app_launch_mean,
        "app_launch_latency_stddev_ms": app_launch_stddev
      }
      message = json.dumps(data_dict)
  elif app_launch_mean and app_launch_stddev and not args.json:
    message = f"App launch mean: {app_launch_mean} ms. "\
      f"Standard Deviation: {app_launch_stddev} ms."
  else:
    message = "No log entries matching pattern."

  print(message)


if __name__ == '__main__':
  main()
