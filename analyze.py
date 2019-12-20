#!/usr/bin/python3

import csv
import datetime
import matplotlib.pyplot as plt
import sys
import re


args = sys.argv[1:]


def iso_to_date(iso):
    y, m, d = re.match(r'(\d+)-(\d+)-(\d+)', iso).groups()
    return datetime.date(int(y), int(m), int(d))


def moving_median(v, window=5):
    e = (window - 1) / 2
    mm = []
    for i in range(len(v)):
        imin = int(i - e) if i - e > 0 else 0
        imax = int(i + e + 1) if i + e < len(v) else len(v)
        sample = sorted(v[imin:imax])
        x = int(len(sample) / 2)
        if len(sample) % 2 == 0:
            mm.append((sample[x - 1] + sample[x]) / 2)
        else:
            mm.append(sample[x])
    return mm


def moving_mean(v, window=5):
    e = (window - 1) / 2
    mm = []
    for i in range(len(v)):
        imin = int(i - e) if i - e > 0 else 0
        imax = int(i + e + 1) if i + e < len(v) else len(v)
        sample = sorted(v[imin:imax])
        mm.append(sum(sample) / len(sample))
        # x = int(len(sample) / 2)
        # if len(sample) % 2 == 0:
        #     mm.append((sample[x - 1] + sample[x]) / 2)
        # else:
        #     mm.append(sample[x])
    return mm


def epley(w, r):
    return w * (1 + r/30)
    # return w * r/30



def main():
    dbfile = args[0] + '.database'
    recfile = args[0] + '.record'
    print('Reading:')
    print(dbfile, recfile)

    database = {}
    with open(dbfile, 'r') as dbf:
        rdr = csv.DictReader(dbf)
        for x in rdr:
            database[x['exercise']] = float(x['bwratio'])
    print('\nDatabase:')
    print(database)

    dates = []
    with open(recfile, 'r') as rbf:
        rdr = csv.DictReader(rbf)
        for x in rdr:
            print(x)
            if x['date'] in dates:
                pass
            else:
                dates.append(x['date'])
    print(dates)

    record = {}
    for x in database.keys():
        record[x] = [[] for y in range(len(dates))]
    bw = [None for x in range(len(dates))]
    with open(recfile, 'r') as rbf:
        rdr = csv.DictReader(rbf)
        for x in rdr:
            i = dates.index(x['date'])
            print(i, x)
            if x['bodyweight']:
                bw[i] = float(x['bodyweight'])
            ex = x['exercise']
            if ex:
                print(ex)
                record[ex][i].append([int(x['sets']), int(x['reps']), float(x['weight'])])
    print(record)

    last_bw = bw[0]
    for i in range(len(bw)):
        if bw[i] == None:
            bw[i] = last_bw
        else:
            last_bw = bw[i]
    print(bw)

    dates = [iso_to_date(x) for x in dates]

    fig, ax = plt.subplots(nrows=2, ncols=2)
    plt.tight_layout()

    # Bodyweight plot

    coming_days = [datetime.timedelta(days=x - 28) + dates[-1] for x in range(58)]
    ax[0][0].plot(coming_days, [bw[-1] for __ in coming_days], linestyle=':', color='lightgray', alpha=0.6)
    ax[0][0].plot(coming_days, [bw[-1] + (i - 28)/7 for i, __ in enumerate(coming_days)], linestyle=':', color='lightgray', alpha=0.6)
    ax[0][0].plot(coming_days, [bw[-1] - (i - 28)/7 for i, __ in enumerate(coming_days)], linestyle=':', color='lightgray', alpha=0.6)
    ax[0][0].plot(coming_days, [bw[-1] + (i - 28)/14 for i, __ in enumerate(coming_days)], linestyle=':', color='lightgray', alpha=0.6)
    ax[0][0].plot(coming_days, [bw[-1] - (i - 28)/14 for i, __ in enumerate(coming_days)], linestyle=':', color='lightgray', alpha=0.6)
    ax[0][0].plot(coming_days, [bw[-1] + (i - 28)/28 for i, __ in enumerate(coming_days)], linestyle=':', color='lightgray', alpha=0.6)
    ax[0][0].plot(coming_days, [bw[-1] - (i - 28)/28 for i, __ in enumerate(coming_days)], linestyle=':', color='lightgray', alpha=0.6)

    ax[0][0].plot(dates, bw, '.')
    ax[0][0].plot(dates, moving_median(bw))
    ax[0][0].plot(dates, moving_mean(bw, window=9))
    ax[0][0].set_ylabel('bodyweight')
    ax[0][0].grid(b=True, which='major', color='lightgray', linestyle='--')

    # Lifted weight

    for ex in database.keys():
        xax = [x for x, y in zip(dates, record[ex]) if y]
        yax = [max([z[2] for z in y]) + bw[dates.index(x)]*database[ex] for x, y in zip(dates, record[ex]) if y]
        # yax = [max([y[2] for y in x]) for x in record[ex] if x]
        print(xax)
        print(yax)
        ax[0][1].plot(xax, yax, '-o')
        ax[0][1].set_ylabel('Weight + (partial) bodyweight')
        ax[0][1].grid(b=True, which='major', color='lightgray', linestyle='--')

    # Estimated 1rm

    orm = epley
    for ex in database.keys():
        xax = [x for x, y in zip(dates, record[ex]) if y]
        yax = [max([epley(z[2] + bw[dates.index(x)]*database[ex], z[1]) - bw[dates.index(x)]*database[ex] if z[1] > 1 else z[2] for z in y]) for x, y in zip(dates, record[ex]) if y]
        print(xax)
        print(yax)
        ax[1][0].plot(xax, yax, '-o')
        ax[1][0].set_ylabel('Estimated 1rm')
        ax[1][0].legend()
        ax[1][0].grid(b=True, which='major', color='lightgray', linestyle='--')

    # Volume

    for ex in database.keys():
        xax = [x for x, y in zip(dates, record[ex]) if y]
        yax = [sum([(z[2]+bw[dates.index(x)]*database[ex])*z[1]*z[0] for z in y]) + bw[dates.index(x)]*database[ex] for x, y in zip(dates, record[ex]) if y]
        print(xax)
        print(yax)
        ax[1][1].plot(xax, yax, '-o')
        ax[1][1].set_ylabel('Total volume')
        ax[1][1].grid(b=True, which='major', color='lightgray', linestyle='--')

    plt.show()


if __name__ == '__main__':
    main()
