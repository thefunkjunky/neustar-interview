#!/usr/bin/env python3
"""
Randomly generates log files
"""

import random
import re
import argparse


def main():
  """Randomly generates log files from a sample log."""
  parser = argparse.ArgumentParser(
    description="Randomly generates log files from a sample log."
    )
  parser.add_argument(
    "sample_log_path",
    type=str,
    help="Location of sample log file."
  )
  parser.add_argument(
    "--dest_log_file",
    type=str,
    default="/var/log/ultradns-quiz-madeup.log",
    help="Location of generated log file."
  )
  parser.add_argument(
    "--min_latency",
    type=int,
    default=0,
    help="Minimum random latency."
  )
  parser.add_argument(
    "--max_latency",
    type=int,
    default=800,
    help="Max random latency."
  )
  parser.add_argument(
    "--max_logs_range",
    type=int,
    default=100,
    help="Max number of random match entry logs."
  )
  parser.add_argument(
    "--match_string",
    type=str,
    default="Ultradns quiz application",
    help="Log entries string to match."
    )
  args = parser.parse_args()

  with open(args.sample_log_path, "r") as f:
    logs = f.readlines()

  match_logs = [
    log for log in logs
    if args.match_string in log
  ]

  non_match_logs = [
    log for log in logs
    if args.match_string not in log
  ]
  generated_logs = non_match_logs.copy()

  len_non_match_logs_list = len(non_match_logs)
  num_match_logs = random.randint(0, args.max_logs_range)
  for n in range(0, num_match_logs):
    random_index = random.randint(0, len_non_match_logs_list - 1)
    random_match_log = random.choice(match_logs)
    random_latency = random.randint(args.min_latency, args.max_latency)
    generated_log = re.sub(
      r"took \d+", f"took {random_latency}",
      random_match_log
    )
    generated_logs[random_index] = generated_log

  with open(args.dest_log_file, "w") as f:
    f.write("".join(generated_logs))

  print("Log generated")


if __name__ == '__main__':
  main()
