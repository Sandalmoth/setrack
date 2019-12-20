#!/usr/bin/python3


import csv
import datetime
import math
import random
import re
from io import StringIO
from copy import deepcopy

import click
import numpy as np
import toml
from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib import dates as mdates
from matplotlib.colors import Normalize
from matplotlib.dates import MO
from scipy.optimize import minimize


def general_epley(weight, reps, slope=29.0):
    return weight*(1 + (reps - 1)/slope)


def inverse_general_epley(orm, weight, slope=29.0):
    return slope*(orm/weight - 1) + 1


def forward_general_epley(orm, reps, slope=29.0):
    return orm/(1 + (reps - 1)/slope)


def iso_to_date(iso):
    y, m, d = re.match(r'(\d+)-(\d+)-(\d+)', iso).groups()
    return datetime.date(int(y), int(m), int(d))


def get_weights(dates, reference_date=None):
    if reference_date is None:
        reference_date = max(dates)
    ages = np.array([abs((reference_date - x).days) for x in dates])
    age_weights = ages/30 + 1
    # age_weights = np.ceil(age_weights + 1)
    age_weights = age_weights**2
    return age_weights


def fit_rmcurve(amraps, reference_date=None):
    rps = amraps['reps']
    wts = amraps['weight']
    age_weights = get_weights(amraps['date'], reference_date)
    return minimize(
        lambda x: np.sum((rps - inverse_general_epley(x[0], wts, x[1]))**2 / age_weights),
        [300.0, 29.0],
        method='L-BFGS-B'
    ).x


def parse_amraps(amrap_string):
    amrap_buffer = StringIO(amrap_string)
    rdr = csv.DictReader(amrap_buffer)
    amraps = {x: [] for x in rdr.fieldnames}
    for l in rdr:
        for k, v in l.items():
            if k == 'date':
                v = iso_to_date(v)
            elif k == 'weight':
                v = float(v)
            elif k == 'reps':
                v = int(v)
            amraps[k].append(v)
    amraps = {k: np.array(v) for k, v in amraps.items()}
    return amraps


def round_to(x, base):
    return base * round(float(x) / base)


class Control():
	def __init__(self):
		self.dbfile = None


pass_control = click.make_pass_decorator(Control, ensure=True)


@click.group()
@click.argument('dbfile', type=str)
@pass_control
def main(control, dbfile):
    control.dbfile = dbfile + '.toml'


@main.command()
@click.argument('exercise', type=str)
@click.argument('amrap', type=str)
@click.option('-d', '--date', type=str)
@pass_control
def entry(control, exercise, amrap, date):
    db = toml.load(control.dbfile)

    if date == None:
        date = datetime.date.today()

    reps, weight = re.match(r'(\d+)x(\d+\.?\d*)', amrap).groups()
    csv_buffer = StringIO(db[exercise]['amraps'])
    fieldnames = csv_buffer.__next__()
    fieldnames = fieldnames.rstrip()
    fieldnames = fieldnames.split(',')
    csv_buffer.seek(0, 2)
    wtr = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    wtr.writerow(
        {
            'date': date,
            'reps': reps,
            'weight': weight,
        }
    )

    csv_buffer.seek(0)
    db[exercise]['amraps'] = csv_buffer.read()

    with open(control.dbfile, 'w') as out_toml:
        toml.dump(db, out_toml)


@main.command()
@click.option('-i', '--infile', type=click.Path())
@click.option('-o', '--outfile', type=click.Path())
@pass_control
def parse(control, infile, outfile):
    db = toml.load(control.dbfile)
    for exercise in db['exercises']:
        amraps = parse_amraps(db[exercise]['amraps'])
        db[exercise]['orm'], db[exercise]['slope'] = fit_rmcurve(amraps)

    re_plan = re.compile(r'(.*)\[(.*)\](.*)$')
    re_options = re.compile(r'(\d+)x(\d+);([a-z])(\d+\.?\d*)')

    with open(infile, 'r') as input:
        with open(outfile, 'w') as output:
            for line in input:
                print(line)
                plan = re_plan.match(line)
                if plan is None:
                    output.write(line)
                    continue
                print(plan.groups())
                exercise = plan.groups()[0].rstrip()
                options = re_options.findall(plan.groups()[1])
                print(options)
                option = random.choice(options)
                print(option)
                sets = int(option[0])
                reps = int(option[1])
                vol_marker = option[2]
                vol = float(option[3])
                if vol_marker == 'r':
                    hidden_reps = reps + vol
                elif vol_marker == 'f':
                    hidden_reps = reps/vol
                weight = forward_general_epley(
                    db[exercise]['orm'],
                    hidden_reps,
                    db[exercise]['slope']
                )
                print(weight)
                weight = round_to(weight, db[exercise]['rounding'])
                print(weight)
                output.write(
                    plan.groups()[0] + 'x'.join(
                        [str(x) for x in [sets, reps, weight]]
                    ) + plan.groups()[2] + '\n'
                )


@main.command()
@pass_control
def plotfit(control):
    db = toml.load(control.dbfile)

    n_exercises = len(db['exercises'])
    grid_size = math.ceil(n_exercises**0.5)

    fig, axs = plt.subplots(nrows=grid_size, ncols=grid_size)

    for i, exercise in enumerate(db['exercises']):
        this_axs = axs[int(i/grid_size)][i%grid_size]
        amraps = parse_amraps(db[exercise]['amraps'])
        x_axis = np.linspace(1, 15, 100)
        orm, slope = fit_rmcurve(amraps)
        rmcurve = forward_general_epley(orm, x_axis, slope)
        print(exercise, orm, slope)
        weights = get_weights(amraps['date'])
        this_axs.scatter(amraps['reps'], amraps['weight'],
                         s=weights*10,
                         c=-weights,
                         norm=Normalize(vmin=-max(weights) - 1,
                                        vmax=0),
                         marker='o',
                         cmap=cm.Greys)
        this_axs.plot(x_axis, rmcurve, color='k')
        this_axs.text(0.6, 0.6,
                      '\n'.join([str(x) + " RM: " + str(
                          round(forward_general_epley(orm, x, slope), 1)
                      ) for x in [1, 5, 10]]),
                      transform=this_axs.transAxes)
        this_axs.set_xlim(0, 16)
        this_axs.set_xticks([1, 5, 10, 15])
        this_axs.grid()
        this_axs.set_title(exercise)

    plt.tight_layout()
    plt.show()


@main.command()
@pass_control
@click.option('--future/--no-future', default=False)
def plottime(control, future):
    db = toml.load(control.dbfile)

    n_exercises = len(db['exercises'])
    grid_size = math.ceil(n_exercises**0.5)

    fig, axs = plt.subplots(nrows=grid_size, ncols=grid_size)

    months = mdates.MonthLocator()
    months_fmt = mdates.DateFormatter('%Y-%m')
    days = mdates.WeekdayLocator(byweekday=MO)

    for i, exercise in enumerate(db['exercises']):
        this_axs = axs[int(i/grid_size)][i%grid_size]
        amraps = parse_amraps(db[exercise]['amraps'])
        if future:
            x_axis = [amraps['date'][0] + datetime.timedelta(days=x) for x in range((amraps['date'][-1] - amraps['date'][0]).days)]
        else:
            x_axis = amraps['date']
        rm_axis = []
        rms = [1, 5, 10]
        linestyles = ['-', '--', 'dotted']
        for j, date in enumerate(x_axis):
            if future:
                orm, slope = fit_rmcurve(amraps, date)
                rm_axis.append([round(forward_general_epley(orm, x, slope), 1) for x in rms])
            else:
                if j == 0:
                    continue
                old_amraps = {k: v[:j + 1] for k, v in amraps.items()}
                orm, slope = fit_rmcurve(old_amraps)
                rm_axis.append([round(forward_general_epley(orm, x, slope), 1) for x in rms])
        if not future:
            x_axis = x_axis[1:]
        for j, rm in enumerate(rms):
            this_axs.plot(x_axis, [x[j] for x in rm_axis], color='k', linestyle=linestyles[j])
        this_axs.xaxis.set_major_locator(months)
        this_axs.xaxis.set_major_formatter(months_fmt)
        this_axs.xaxis.set_minor_locator(days)
        this_axs.grid(which='minor')
        this_axs.set_title(exercise)
        this_axs.format_xdata = mdates.DateFormatter('%Y-%m-%d')

    min_date = min([[x.get_xlim()[0] for x in y] for y in axs])[0]
    max_date = max([[x.get_xlim()[1] for x in y] for y in axs])[0]
    for y in axs:
        for x in y:
            x.set_xlim(min_date, max_date)

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
