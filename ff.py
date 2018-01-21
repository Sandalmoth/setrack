#!/usr/bin/python3

import csv
import configparser
import click
import datetime
import re as re
import matplotlib.pyplot as plt


VERSION = '0.0.1'
BPRF = -9999.0


class Control():
	def __init__(self):
		self.verbose = False
		self.inf = None
		self.dbf = None
		self.rf = None


pass_control = click.make_pass_decorator(Control, ensure=True)


def epley(w, r):
    return w*(1.0 + r/30.0)

def iepley(I):
    return (1.0/I - 1.0)*30.0 + 1.0


@click.group()
@click.version_option(version=VERSION)
@click.option('--verbose', is_flag=True, help='Increase output verbosity (maybe).')
@click.argument('inf', type=click.Path())
@pass_control
def main(control, verbose, inf):
	control.verbose = verbose
	control.inf = inf
	ctrl = configparser.ConfigParser()
	ctrl.read(control.inf)
	control.dbf = ctrl['DATABASE']['filename']
	control.rf = ctrl['RECORD']['filename']


@main.command()
@pass_control
def plot(control):
    print(control.inf, control.dbf, control.rf)

    exercise = []
    bwratio = []
    performance = []
    work = []

    # define the one rep max formula and its inverse
    rmf = epley
    irmf = iepley

    with open(control.dbf, 'r') as dbf, open(control.rf, 'r') as rf:
        drdr = csv.DictReader(dbf) # hurr durr durr
        for row in drdr:
            exercise.append(row['exercise'])
            bwratio.append(float(row['bwratio']))
            performance.append([BPRF])
            work.append([0.0])
        if control.verbose:
            print(exercise, bwratio)

        rrdr = csv.DictReader(rf)
        currentbw = 100 # initial guess as it might not be given in the first record
        currentdate = None
        for row in rrdr:
            print(row)

            # update date such that any new input can be read into the last point of performance/work
            previousdate = currentdate
            datenums = [int(x) for x in re.match(r'(\d+)-(\d+)-(\d+)', row['date']).groups()]
            print(datenums)
            currentdate = datetime.date(datenums[0], datenums[1], datenums[2])
            print(currentdate)
            dayspassed = (currentdate - previousdate).days if previousdate is not None else 0
            print(dayspassed)
            if dayspassed > 0:
                for x in performance:
                    x.append(BPRF)
                for x in work:
                    x.append(0.0)

            # update bodyweight
            if row['bodyweight']:
                currentbw = float(row['bodyweight'])

            if row['exercise']:
                exc = exercise.index(row['exercise'])
                reps = int(row['reps'])
                sets = int(row['sets'])
                weight = float(row['weight'])
                print(exc, sets, reps, weight)

                # go with tonnage for now
                work[exc][-1] += sets*reps*(weight + bwratio[exc]*currentbw)

                # estimate 1rm assuming 100% effort
                performance[exc][-1] = max(performance[exc][-1], epley(weight + bwratio[exc]*currentbw, reps) - bwratio[exc]*currentbw)

    print(performance, work)


if __name__ == '__main__':
    main()
