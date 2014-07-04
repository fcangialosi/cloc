import argparse
import sys
import os
import datetime
import json

HOME = os.path.expanduser("~")
DATA = HOME + '/cloc.txt'
CONFIG = HOME + '/.cloc_config'

def write(time, action, project, msg):
	with open(DATA, 'a') as f:
		f.write(time + " ")
		f.write(action + " ")
		f.write(project + " ")
		f.write(msg)
		f.write("\n")

def cloc_in(args,msg):
	now = datetime.datetime.now()
	now_str = str(now).split(".")[0]

	project = "None"
	if len(args) > 1:
		project = args[1]

	write(now_str, 'in', project, msg)

	print "You cloc'd in at " + str(now_str)

def cloc_out(args,msg):
	now = datetime.datetime.now()
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

	datetime_in = datetime.datetime.strptime(time_in, "%Y-%m-%d %X")
	time_elapsed = now - datetime_in
	seconds_elapsed = int((time_elapsed.seconds % 3600) % 60)
	minutes_elapsed = int((time_elapsed.seconds % 3600) / 60)
	hours_elapsed = int(time_elapsed.seconds / 3600)
	days_elapsed = int(time_elapsed.days)

	print "You cloc'd out at " + str(now_str)
	print "You worked for",
	if days_elapsed > 0:
		print "{0} day(s),".format(days_elapsed),
	if hours_elapsed > 0:
		print "{0} hour(s),".format(hours_elapsed),
	if minutes_elapsed > 0:
		print "{0} minutes(s),".format(minutes_elapsed),
	if seconds_elapsed > 0:
		print "{0} seconds(s)".format(seconds_elapsed)

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
	else:
		print "Sorry, {0} is not a valid mode"
		sys.exit(1)
