import csv
import configparser
import click


VERSION = '0.0.1'

RECORD_FIELDNAMES = ['date', 'exercise', 'sets', 'reps', 'weight', 'bodyweight']
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
@click.option('--bwratio', type=float)
@click.argument('exercise', type=str)
@click.argument('aliases', type=str, nargs=-1)
@pass_control
def entry(control, exercise, aliases, bwratio):
	with open(control.dbf, 'a') as dbf:
		wtr = csv.DictWriter(dbf, fieldnames=DATABASE_FIELDNAMES)
		wtr.writerow({
			DATABASE_FIELDNAMES[0]: exercise,
			DATABASE_FIELDNAMES[1]: ' '.join(aliases),
			DATABASE_FIELDNAMES[2]: bwratio
		})


####################
### RECORD GROUP ###
####################

@main.group()
@pass_control
def rec():
	"""Record-handling function group"""
	ctrl = configparser.ConfigParser()
	ctrl.read(control.inf)
	control.dbf = ctrl['DATABASE']['filename']
	control.rf = ctrl['RECORD']['filename']

@rec.command()
@pass_control
def insert(control):
	"""Enter session recording environment for specified file"""
	csv.DictWriter(control.inf)


if __name__ == '__main__':
	main()