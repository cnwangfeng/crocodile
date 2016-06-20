# Tim Cornwell <realtimcornwell@gmail.com>
#
# Visibility data structure: a Table with columns ['uvw', 'time', 'antenna1', 'antenna2', 'vis', 'weight']
# and an attached attribute which is the frequency of each channel

from collections import namedtuple

import numpy as numpy

from astropy.coordinates import SkyCoord
from astropy.table import Table, vstack, Row, Column, MaskedColumn, TableColumns, TableFormatter
from functions.fconfig import fconfig, fconfig_from_name
from crocodile.simulate import *


def fvistab():
    """
    Visibility with uvw, time, a1, a2, vis, weight Columns in
    an astropy Table along with an attribute frequency to hold the frequencies
    and an attribute to hold the direction.

    fvistab is defined to hold an observation with one set of frequencies and one
    direction.
    """
    return namedtuple('fvistable', ['data', 'frequency', 'direction'])


def fvistab_add(fvt1: fvistab, fvt2: fvistab, **kwargs):
    assert len(fvt1.frequency) == len(fvt2.frequency), "fvistab: frequencies should be the same"
    assert numpy.max(numpy.abs(fvt1.frequency - fvt2.frequency)) < 1.0, "fvistab: frequencies should be the same"
    print("fvistab: adding tables with %d rows and %d rows" % (len(fvt1.data), len(fvt2.data)))
    fvt = fvistab()
    fvt.data = vstack([fvt1.data, fvt2.data], join_type='exact')
    fvt.direction = fvt1.direction
    fvt.frequency = fvt1.frequency
    print(u"Created table with {0:d} rows".format(len(fvt.data)))
    assert(len(fvt.data)==(len(fvt1.data)+len(fvt2.data))), 'Length of output data table wrong'
    return fvt


def fvistab_filter(fvis: fvistab, **kwargs):
    print("vistab: No filter implemented yet")
    return fvis


def fvistab_from_array(uvw: numpy.array, time: numpy.array, freq: numpy.array, antenna1: numpy.array,
                       antenna2: numpy.array, vis: numpy.array, weight: numpy.array,
                       direction: SkyCoord, meta: dict, **kwargs):
    """

    :type direction: SkyCoord
    :type meta: object
    """
    nrows = time.shape[0]
    assert uvw.shape[0] == nrows, "Discrepancy in number of rows in uvw"
    assert len(antenna1) == nrows, "Discrepancy in number of rows in antenna1"
    assert len(antenna2) == nrows, "Discrepancy in number of rows in antenna2"
    assert vis.shape[0] == nrows, "Discrepancy in number of rows for vis"
    assert len(freq) == vis.shape[1], "Discrepancy between frequencies and number of channels"
    assert weight.shape[0] == nrows, "Discrepancy in number of rows"
    vt = fvistab()
    vt.data = Table(data=[uvw, time, antenna1, antenna2, vis, weight],
                    names=['uvw', 'time', 'antenna1', 'antenna2', 'vis', 'weight'], meta=meta)
    vt.frequency = freq
    vt.direction = direction
    return vt


def fvistab_from_fconfig(config: fconfig, times: numpy.array, freq: numpy.array, weight: float = 1.0,
                         direction: SkyCoord = None, meta: dict = None, **kwargs):
    """
    Creat a vistable from configuration, hour angles, and direction of source
    :param config: Configuration of antennas
    :param times: hour angles
    :param freq: frequencies (Hz]
    :param weight: weight of a single sample
    :param direction: direction of source
    :rtype: object
    """
    assert direction != None, "Must specify direction"
    nch = len(freq)
    ants_xyz = config.data['xyz']
    nants = len(config.data['names'])
    nbaselines = int(nants * (nants - 1) / 2)
    ntimes = len(times)
    nrows = nbaselines * ntimes
    row = 0
    rvis = numpy.zeros([nrows, nch, 4], dtype='complex')
    rweight = weight * numpy.zeros([nrows, nch, 4], dtype='float')
    rtimes = numpy.zeros([nrows])
    rantenna1 = numpy.zeros([nrows], dtype='int')
    rantenna2 = numpy.zeros([nrows], dtype='int')
    for ha in times:
        rtimes[row:row + nbaselines] = ha * 43200.0 / numpy.pi
        for a1 in range(nants):
            for a2 in range(a1 + 1, nants):
                rantenna1[row] = a1
                rantenna2[row] = a2
                row += 1
    ruvw = xyz_to_baselines(ants_xyz, times, direction.dec)
    print(u"Created {0:d} rows".format(nrows))
    return fvistab_from_array(ruvw, rtimes, freq, rantenna1, rantenna2, rvis, rweight, direction, meta)


if __name__ == '__main__':
    config = fconfig_from_name('VLAA')
    print(config)
    times1 = numpy.arange(-3.0, 0.0, 3.0 / 60.0) * numpy.pi / 12.0
    times2 = numpy.arange(0.0, +3.0, 3.0 / 60.0) * numpy.pi / 12.0
    freq1 = numpy.arange(5e6, 150.0e6, 1e7)
    freq2 = numpy.arange(6e6, 150.0e6, 1e7)
    direction = SkyCoord(ra='00h42m30s', dec='-41d12m00s', frame='icrs')
    vt1 = fvistab_from_fconfig(config, times1, freq1, weight=1.0, direction=direction)
    vt2 = fvistab_from_fconfig(config, times2, freq2, weight=1.0, direction=direction)
    try:
        vtsum = fvistab_add(vt1, vt2)
    except AssertionError:
        print("fvistab: correctly threw AssertionError")
        pass
    vt2 = fvistab_from_fconfig(config, times2, freq1, weight=1.0, direction=direction)
    vtsum = fvistab_add(vt1, vt2)
    print(vtsum.data)
    print(vtsum.frequency)
    print(numpy.unique(vtsum.data['time']))
