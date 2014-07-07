import argparse
import sys
import os
from datetime import datetime, timedelta, date
import json

HOME = os.path.expanduser("~")
DATA = HOME + '/cloc.txt'
CONFIG = HOME + '/.cloc_config'

def delta_to_str(delta):
	seconds_elapsed = int((delta.seconds % 3600) % 60)
	minutes_elapsed = int((delta.seconds % 3600) / 60)
	hours_elapsed = int(delta.seconds / 3600)
	days_elapsed = int(delta.days)

	result = ""

	if days_elapsed > 0:
		result+="{0} day(s), ".format(days_elapsed)
	if hours_elapsed > 0:
		result+="{0} hour(s), ".format(hours_elapsed)
	if minutes_elapsed > 0:
		result+="{0} minutes(s), ".format(minutes_elapsed)
	if seconds_elapsed > 0:
		result+="{0} seconds(s)".format(seconds_elapsed)

	return result

def str_to_date(string):
	return datetime.strptime(string, "%Y-%m-%d %X")

def write(time, action, project, msg):
	with open(DATA, 'a') as f:
		f.write(time + " ")
		f.write(action + " ")
		f.write(project + " ")
		f.write(msg)
		f.write("\n")

def cloc_in(args,msg):
	now = datetime.now()
	now_str = str(now).split(".")[0]

	project = "None"
	if len(args) > 1:
		project = args[1]

	write(now_str, 'in', project, msg)

	print "You cloc'd in at " + str(now_str)

def cloc_out(args,msg):
	now = datetime.now()
	now_str = str(now).split(".")[0]

	project = "None"
	with open(DATA, 'r') as f:
		r = f.readlines()
		if len(r) < 1:
			print "Whoa there, you haven't even cloc'd in yet!"
			sys.exit(1)
		last_line = r[-1].strip().split()
		if not last_line[2] == 'in':
			print "Whoa there, you haven't even cloc'd in yet!"
			sys.exit(1)
		else:
			time_in = last_line[0] + " " + last_line[1]
			project = last_line[3]

	write(now_str, 'out', project, msg)

	datetime_in = datetime.strptime(time_in, "%Y-%m-%d %X")
	time_elapsed = now - datetime_in
	
	print "You cloc'd out at " + str(now_str)
	print "You worked for",
	print delta_to_str(time_elapsed)
	
def total_range(range_start, range_end):

	total = timedelta(microseconds=0)

	with open(DATA, 'r') as f:

		r = f.readlines()
		periods = zip(*[iter(r)] * 2)

		for period in periods:

			period_start = str_to_date(period[0].split()[0] + " " + period[0].split()[1])
			period_end = str_to_date(period[1].split()[0] + " " + period[1].split()[1])
			period_start_in_range = (range_start <= period_start <= range_end)
			period_end_in_range = (range_start <= period_end <= range_end)

			if(period_start_in_range and period_end_in_range):
				total += (period_end-period_start)
			elif(period_start_in_range):
				total += (range_end-period_start)
			elif(period_end_in_range):
				total += (period_end-range_start)

	return total

def cloc_total(args):
	if len(args) < 2:
		when = 'today'
	else:
		when = args[1]

	if when == 'today':
		today = date.today()
		today_start = datetime.combine(today, datetime.min.time())
		today_end = datetime.combine(today, datetime.max.time())
		total = total_range(today_start, today_end)

	elif when == 'yesterday':
		yesterday = date.today() - timedelta(days=1)
		yesterday_start = datetime.combine(yesterday, datetime.min.time())
		yesterday_end = datetime.combine(yesterday, datetime.max.time())
		total = total_range(yesterday_start, yesterday_end)

	elif when == 'week':
		print 'TODO week'

	elif when == 'month':
		print 'TODO month'

	elif when == 'year':
		print 'TODO year'

	else:
		when = ' '.join(args[1:])
		this_year = str(date.today().year)
		if len(when.split('to')) <= 1:
			start_day = end_day = datetime.strptime(when.strip() + " " + this_year, "%b %d %Y").date()
		else:
			start_day = datetime.strptime(when.split('to')[0].strip()+ " " + this_year , "%b %d %Y").date()
			end_day = datetime.strptime(when.split('to')[1].strip() + " " + this_year, "%b %d %Y").date()

		query_start = datetime.combine(start_day, datetime.min.time())
		query_end = datetime.combine(end_day, datetime.max.time())
		total = total_range(query_start, query_end)

	print delta_to_str(total)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog='cloc', description='cloc is tiny command line application to help you keep track of when you work.')
	parser.add_argument('action', nargs="+", help="cloc in when you start working, then cloc out when youre done")
	parser.add_argument('-m', '--message', help="Note to be stored along with this time entry",required=False, default=None)
		
	args = vars(parser.parse_args())

	if not os.path.isfile(CONFIG):
		print "It looks like this is your first time using cloc.."
		print "Please choose a file for your timesheets (default is ~/cloc.txt): ",
		user_file = sys.stdin.readline().strip()

		if(len(user_file) > 1):
			if(user_file[0] == '~'):
				DATA = HOME + user_file[1:]
			else:
				DATA = user_file
		
		if not os.path.isfile(DATA):
			open(DATA, 'w').close()
			print "\rCreated " + DATA + " (did not exist)"
		else:
			print "\rUsing " + DATA + " (already exists)"

		with open(CONFIG, 'w') as config:
			settings = {}
			settings['data'] = DATA
			config.write(json.dumps(settings))
	else:
		config = open(CONFIG, 'r')
		r = config.read()
		DATA = json.loads(r)['data']
		config.close()

	msg = "None"
	if(args['message']):
		msg = args['message']

	if(args['action'][0] == 'in'):
		cloc_in(args['action'],msg)
	elif(args['action'][0] == 'out'):
		cloc_out(args['action'],msg)
	elif(args['action'][0] == 'total'):
		cloc_total(args['action'])
	else:
		print "Sorry, {0} is not a valid mode"
		sys.exit(1)
