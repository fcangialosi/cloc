import argparse
import sys
import os
from datetime import datetime, timedelta, date
from collections import defaultdict
import json
from terminaltables import SingleTable
from math import ceil

HOME = os.path.expanduser("~")
CLOC_HOME = HOME + '/.cloc/'
DATA = CLOC_HOME + 'current.txt'
PENDING = CLOC_HOME + 'pending.txt'
PAID = CLOC_HOME + 'paid.txt'
CONFIG = HOME + '/.cloc_config'
tax_rate = None
project_list = {}

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

def write(time, action, project, msg=None):
	with open(DATA, 'a') as f:
		f.write("\t".join(time.split(" ")) + "\t")
		f.write(action + "\t")
		f.write(project + "\t")
		if msg:
			f.write("\""+msg+"\"")
                else:
                    f.write("0")
		f.write("\n")

def cloc_in(args,msg):
	now = datetime.now()
	now_str = str(now).split(".")[0]

	project = "None"
	if len(args) > 1:
		project = args[1]

	write(now_str, 'in', project, msg)

	print "You cloc'd in at " + str(now_str)

def cloc_add(args,msg):
    end = datetime.now()
    start = end - timedelta(minutes=int(args[2]))
    end_str = str(end).split(".")[0]
    start_str = str(start).split(".")[0]

    project = "None"
    if len(args) > 1:
            project = args[1]

    write(start_str, 'in', project, msg)
    write(end_str, 'out', project, msg)

    print "You added a %s-minute work period" % args[2]

def cloc_out(args):
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

	write(now_str, 'out', project)

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

def format_minutes(m):
	return "{:02d}:{:02d}".format(int(m/60), int(round(m % 60)))

def diff_mins(a,b):
	return (b-a).total_seconds() / 60.0

def to_dt(date,time):
	return str_to_date(date + " " + time)

def round_mins_up(mins,min_time=15.0):
    return (ceil(mins / min_time) * min_time) / 60.0

def total_time(filename, project):
    f = open(filename,'r')
    r = f.readlines()

    task_to_mins = defaultdict(float)
    periods = zip(*[iter(r)] * 2)
    for period in periods:
        in_date, in_time, _, in_project, task = period[0].strip().split("\t")
        out_date, out_time, _, out_project, extra = period[1].strip().split("\t")
        extra_mins = float(extra) * 60.0
        period_start = str_to_date(in_date + " " + in_time)
        period_end = str_to_date(out_date + " " + out_time)
        assert(in_project == out_project)
        if in_project != project:
            continue
        task = task.replace("\"","")
        time_spent = (period_end - period_start).total_seconds() / 60.0
        task_to_mins[task] += (time_spent + extra_mins)

    f.close()

    total = 0
    for task in task_to_mins:
        total += round_mins_up(task_to_mins[task])

    return total


def cloc_view(project):
    task_order = []
    task_to_mins = defaultdict(float)
    task_to_dates = defaultdict(set)
    task_to_upcharge = defaultdict(float)
    first_date = None
    last_date = None
    total = 0
    tax_rate = project_list[project]['tax_rate']

    if not project in project_list:
        sys.exit("error: project not listed in cloc config")
    project_rate, project_goal = project_list[project]['rate'], project_list[project]['monthly_goal']

    f = open(DATA,'r')
    r = f.readlines()
    periods = zip(*[iter(r)] * 2)
    for period in periods:
        in_date, in_time, _, in_project, task = period[0].strip().split("\t")
        out_date, out_time, _, out_project, upcharge = period[1].strip().split("\t")
        period_start = str_to_date(in_date + " " + in_time)
        period_end = str_to_date(out_date + " " + out_time)
        assert(in_project == out_project)
        if in_project != project:
            continue

        task = task.replace("\"","")

        start_short = period_start.strftime('%-m/%-d')
        end_short = period_end.strftime('%-m/%-d')
        task_to_dates[task].add(start_short)
        task_to_dates[task].add(end_short)
        if not first_date:
            first_date = start_short
        last_date = end_short

        # TODO round
        time_spent = (period_end - period_start).total_seconds() / 60.0
        task_to_mins[task] += time_spent
        task_to_upcharge[task] += float(upcharge)
        if not task in task_order:
            task_order.append(task)
        f.close()


    i = 1
    total = 0.0
    table_data = [['#','Task','Dates','Hours (+up)', 'Rate (eff)', 'Earned']]
    for task in task_order:
        time_spent = round_mins_up(task_to_mins[task])
        upcharge = task_to_upcharge[task]
        table_data.append([
            str(i),
            task,
            ','.join(sorted(task_to_dates[task])),
            '{:.2f} (+{:.2f})'.format(time_spent, upcharge),
            '${:.0f} (${:.0f})'.format(project_rate, ((upcharge+time_spent)/time_spent) * project_rate ),
            '${:.2f}'.format(project_rate * (time_spent + upcharge))
        ])
        i += 1
        total += (time_spent + upcharge)

    if len(periods)*2 < len(r):
        in_date, in_time, _, in_project, task = r[-1].strip().split("\t")
        period_start = str_to_date(in_date + " " + in_time)
        period_end = datetime.now()
        print period_start, period_end
        task = task.replace("\"","")
        start_short = period_start.strftime('%-m/%-d')
        end_short = period_end.strftime('%-m/%-d')
        if not first_date:
            first_date = start_short
        last_date = end_short

        time_spent = round_mins_up((period_end - period_start).total_seconds() /
                60.0)
        total += time_spent

        table_data.append([
            str(i),
            task,
            'current',
            '{:.2f}'.format(time_spent),
            '${:.2f}'.format(project_rate),
            '${:.2f}'.format(project_rate * time_spent)
        ])
    table_data.append([])

    table_data.append([
	'',
	'Total',
	'{} - {}'.format(first_date,last_date),
    	'{:.2f}'.format(total),
	'',
	'${:.2f}'.format(project_rate * total)
    ])

    table_data.append([
        '',
        'Tax',
        '',
        '',
        '{:.0f}%'.format(tax_rate * 100),
        '${:.2f}'.format(project_rate * total * tax_rate)
    ])
    after_tax_total = project_rate * total * (1-tax_rate)
    table_data.append([
        '',
        'Net',
        '',
        '',
        '',
        '${:.2f}'.format(after_tax_total)
    ])
    
    if project_goal > 0:
        table_data.append([])
        table_data.append([
            '',
            'Goal',
            '',
            '{:.2f}'.format(project_goal / project_rate / (1-tax_rate)),
            '',
            '${:.2f}'.format(project_goal)
        ])
        remaining = project_goal - after_tax_total
        table_data.append([
            '',
            'Remaining',
            '',
            '{:.2f}'.format(remaining / project_rate / (1-tax_rate)),
            '',
            '${:.2f}'.format(remaining)
        ])

    table_instance = SingleTable(table_data, project + " timesheet")
    print
    print(table_instance.table)
    previously_paid = total_time(PAID,project) * 35.0
    print "Previously paid: ${:.2f} (${:.2f} after tax)".format(previously_paid, previously_paid * 0.75)
    pending = total_time(PENDING,project) * 35.0
    print "Pending payment: ${:.2f} (${:.2f} after tax)".format(pending, pending * 0.75)
    print


def cloc_check():
	with open(DATA, 'r') as f:
		last = f.readlines()[-1]
		in_date, in_time, _, in_project, in_msg = last.split("\t")
		start = to_dt(in_date,in_time)
		now = datetime.now()
		print "You have been working for {} on {}".format(format_minutes(diff_mins(start,now)), in_project)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog='cloc', description='cloc is tiny command line application to help you keep track of when you work.')
	parser.add_argument('action', nargs="+", help="cloc in when you start working, then cloc out when youre done. cloc check to see your current status, or cloc view to get a summary.")
	parser.add_argument('-t', '--task', help="Note to be stored along with this time entry",required=False, default=None)

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
		r = json.loads(config.read())
		DATA, project_list = r['data'], r['projects'] 
		config.close()

	task = "None"
	if(args['task']):
            task = args['task']

	if(args['action'][0] == 'in'):
		cloc_in(args['action'],task)
	elif(args['action'][0] == 'out'):
		cloc_out(args['action'])
	elif(args['action'][0] == 'view'):
            args = args['action']
            if len(args) < 2:
		sys.exit("usage: cloc view [project]")
            cloc_view(args[1])
	elif(args['action'][0] == 'check'):
		cloc_check()
        elif(args['action'][0] == 'add'):
                cloc_add(args['action'],task)
	else:
		print "Sorry, {0} is not a valid mode"
		sys.exit(1)
