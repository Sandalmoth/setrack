#!/usr/bin/python3

import csv
import configparser
import click
import datetime


VERSION = '0.0.3'

RECORD_FIELDNAMES = ['date', 'exercise', 'sets', 'reps', 'weight', 'rpe', 'bodyweight']
DATABASE_FIELDNAMES = ['exercise', 'aliases', 'bwratio']


class Control():
	def __init__(self):
		self.verbose = False
		self.inf = None
		self.dbf = None
		self.rf = None


pass_control = click.make_pass_decorator(Control, ensure=True)


##################
### MAIN GROUP ###
##################

@click.group()
@click.version_option(version=VERSION)
@click.option('--verbose', is_flag=True, help='Increase output verbosity (maybe).')
@click.argument('inf', type=click.Path())
@pass_control
def main(control, verbose, inf):
	control.verbose = verbose
	control.inf = inf


@main.command()
@click.option('--record', type=click.Path(exists=True))
@click.option('--database', type=click.Path(exists=True))
@click.option('--username', prompt=True, type=str)
@pass_control
def init(control, record, database, username):
	"""Initialize a set of files"""

	# Create record and database files if they do not exist
	if record == None:
		record = control.inf + '.record'
		with open(record, 'w') as rf:
			wtr = csv.DictWriter(rf, fieldnames=RECORD_FIELDNAMES)
			wtr.writeheader()
	if database == None:
		database = control.inf + '.database'
		with open(database, 'w') as dbf:
			wtr = csv.DictWriter(dbf, fieldnames=DATABASE_FIELDNAMES)
			wtr.writeheader()


	# Write to control file
	ctrl = configparser.ConfigParser()
	ctrl['RECORD'] = {}
	# ctrl['RECORD']['fieldnames'] = ' '.join(RECORD_FIELDNAMES)
	ctrl['RECORD']['filename'] = record
	ctrl['DATABASE'] = {}
	# ctrl['DATABASE']['fieldnames'] = ' '.join(RECORD_FIELDNAMES)
	ctrl['DATABASE']['filename'] = database
	ctrl['USERINFO'] = {}
	ctrl['USERINFO']['name'] = username

	with open(control.inf, 'w') as inf: 
		ctrl.write(inf)


######################
### DATABASE GROUP ###
######################

@main.group()
@pass_control
def db(control):
	"""Database-handling function group"""
	ctrl = configparser.ConfigParser()
	ctrl.read(control.inf)
	control.dbf = ctrl['DATABASE']['filename']


@db.command()
@click.option('--bwratio', type=float, default=0.0)
@click.argument('exercise', type=str)
@click.argument('aliases', type=str, nargs=-1)
@pass_control
def entry(control, exercise, aliases, bwratio):
	'''Add an entry to the database'''
	with open(control.dbf, 'a') as dbf:
		wtr = csv.DictWriter(dbf, fieldnames=DATABASE_FIELDNAMES)
		wtr.writerow({
			DATABASE_FIELDNAMES[0]: exercise,
			DATABASE_FIELDNAMES[1]: ' '.join(aliases),
			DATABASE_FIELDNAMES[2]: bwratio
		})


@db.command()
@pass_control
def prnt(control):
	'''Print database in readable format'''
	with open(control.dbf, 'r') as dbf:
		rdr = csv.DictReader(dbf)
		print('\tExercise BWratio Aliases')
		for i, row in enumerate(rdr):
			print(i, row['exercise'], ' ' + row['bwratio'], ' ' + row['aliases'],  sep='\t')



####################
### RECORD GROUP ###
####################

@main.group()
@pass_control
def rec(control):
	"""Record-handling function group"""
	ctrl = configparser.ConfigParser()
	ctrl.read(control.inf)
	control.dbf = ctrl['DATABASE']['filename']
	control.rf = ctrl['RECORD']['filename']

@rec.command()
@click.option('--year', type=int)
@click.option('--month', type=int)
@click.option('--day', type=int)
@click.option('-e', '--exercise', type=str)
@click.option('-s', '--sets', type=int, default=1)
@click.option('-r', '--reps', type=int)
@click.option('-w', '--weight', type=float)
@click.option('--rpe', type=float)
@click.option('--bw', type=float)
@pass_control
def entry(control, year, month, day, exercise, sets, reps, weight, rpe, bw):
	"""Add an entry to the record"""

	# Get the date
	when = datetime.date.today()
	if year != None:
		when = datetime.date(year, when.month, when.day)
	if month != None:
		when = datetime.date(when.year, month, when.day)
	if day != None:
		when = datetime.date(when.year, when.month, day)
	print(when)

	with open(control.dbf, 'r') as dbf, open(control.rf, 'a') as rf:
		rdr = csv.DictReader(dbf)
		wtr = csv.DictWriter(rf, fieldnames=RECORD_FIELDNAMES)

		# If we want to enter an exerces, make sure it exists
		if exercise != None:
			in_db = False
			for row in rdr:
				if (exercise == row['exercise'] or exercise in row['aliases'].split()):
					exercise = row['exercise']
					in_db = True
			if not in_db:
				print('Exercise:', exercise, 'not in database. Aborting entry.')
				return 0

		# A number of things are contingent, so if we don't have all we might as well have none
		if exercise == None or reps == None or weight == None:
			if exercise !=None or reps != None or weight != None:
				print('Exercise, reps and weight have to be specified together')
			exercise = None
			sets = None
			reps = None
			weight = None
			rpe = None

		if exercise == None and sets == None and reps == None and weight == None and rpe == None and bw == None:
			print('Nothing to enter.')
			return 0

		wtr.writerow({
			RECORD_FIELDNAMES[0]: when,
			RECORD_FIELDNAMES[1]: exercise,
			RECORD_FIELDNAMES[2]: sets,
			RECORD_FIELDNAMES[3]: reps,
			RECORD_FIELDNAMES[4]: weight,
			RECORD_FIELDNAMES[5]: rpe,
			RECORD_FIELDNAMES[6]: bw
		})






if __name__ == '__main__':
	main()
	
