#!/usr/bin/env python

import argparse
import datetime
import os
import pickle
import signal
import subprocess

try:
	import tqdm
except ImportError:
	tqdm = None

from pprint import pprint

import numpy as np

parser = argparse.ArgumentParser(description='Runs ping, parses and analyse results.')
parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output.')
parser.add_argument('-c', '--count', metavar='N', type=int, default=None, help='Number of pings to send.')
parser.add_argument('-d', '--dump_freq', metavar='N', type=int, default=10, help='How many steps to wait between intermediate saves.')
parser.add_argument('host', type=str, help='hostname or ip to ping.')
parser.add_argument('save_path', type=str, default=None, nargs='?', help='where to save pkl.')

args = parser.parse_args()

def analyse(body, reference_date):
	missed = [int(line.split()[-1]) for line in body if line.startswith("Request timeout")]

	pinglines = [line for line in body if line and not line.startswith("Request timeout")]
	pings = []
	for line in pinglines:
		parts = line.split()
		h, m, s = map(int, parts[0].split('.')[0].split(':'))
		timestamp = datetime.datetime(reference_date.year, reference_date.month, reference_date.day, h , m, s)
		if (timestamp - reference_date).total_seconds() < 0:
			timestamp = timestamp + datetime.timedelta(days=1)
			reference_date = timestamp
		icmp_seq = int(parts[5].split('=')[1])
		ping = float(parts[7].split('=')[1])
		pings.append((timestamp, icmp_seq, ping))

	jitter = []
	for i in range(len(pings)-1):
		timestamp, icmp_seq, ping = pings[i]
		_, next_icmp, next_ping = pings[i+1]
		if next_icmp == (icmp_seq + 1):
			jitter.append((timestamp, icmp_seq, abs(next_ping - ping)))

	return pings, jitter, missed


def main():
	cmd = "ping --apple-time {count} {host}".format(**{
		"count": "-c {}".format(args.count) if args.count is not None else "",
		"host": args.host
	}).split()

	def handler(signum, frame):
		if args.verbose:
			print(" Manually ending ping session.")

	signal.signal(signal.SIGINT, handler)

	start_time = datetime.datetime.now()

	if args.save_path is None:
		args.save_path = start_time.strftime("./jitter_%d%m%y_%Hh%M.pkl")
	elif os.path.isdir(args.save_path):
		args.save_path = start_time.strftime(os.path.join(args.save_path, "jitter_%d%m%y_%Hh%M.pkl"))

	if args.verbose:
		print("Starting ping.")

	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, encoding='utf=8')

	header = next(proc.stdout).strip()
	
	body = []
	stats = []

	if tqdm and args.count is not None:
		prog = tqdm.tqdm(total=args.count, leave=False)
	else:
		prog = None

	in_body = True
	for i, line in enumerate(proc.stdout):
		line = line.strip()
		if not line:
			continue
		if line.startswith('---'):
			in_body = False
		if in_body:
			if prog is not None:
				prog.update(1)

			if args.verbose:
				if prog is None:
					print(line)
				else:
					prog.write(line)

			body.append(line)

			if (i+1) % args.dump_freq == 0:
				pings, jitter, missed = analyse(body, start_time)
				
				if args.verbose:
					msg = "Saving data to {} after {} pings.".format(args.save_path, i+1)
				
					if prog is None:
						print(msg)
					else:
						prog.write(msg)
				
				with open(args.save_path, "wb") as f:
					pickle.dump((pings, jitter, missed), f)
		else:
			stats.append(line)

	pings, jitter, missed = analyse(body, start_time)

	if args.verbose:
		print("Saving final data to {}.".format(args.save_path))
	with open(args.save_path, "wb") as f:
		pickle.dump((pings, jitter, missed), f)

	if args.verbose:
		print("\n".join(stats))

if __name__ == "__main__":
	main()