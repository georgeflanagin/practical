# -*- coding: utf-8 -*-
""" A stopwatch class for timing events. """

# Added for Python 3.5+
import typing
from typing import *
import datetime
import time


# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2020, University of Richmond'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'me@georgeflanagin.com'
__status__ = 'Prototype'

__license__ = 'MIT'

class Stopwatch:
    """
    Note that the laps are a dict, so you can name them
    as you like, and they will still be regurgitated in order
    later on. Starting with Python 3.6, all dicts are ordered.
    """
    conversions = {
        "minutes":(1/60),
        "seconds":1,
        "tenths":10,
        "deci":10,
        "centi":100,
        "hundredths":100,
        "milli":1000,
        "micro":1000000
        }


    def __init__(self, *, units:object='milli'):
        """
        Build the Stopwatch object, and click the start button. For ease of
        use, you can use the text literals 'seconds', 'tenths', 'hundredths',
        'milli', 'micro', 'deci', 'centi' or any integer as the units. 

        'minutes' is also provided if you think this is going to take a while.

        The default is milliseconds, which makes a certain utilitarian sense.
        """
        try:
            self.units = units if isinstance(units, int) else Stopwatch.conversions[units]
        except:
            self.units = 1000

        self.laps = dict.fromkeys(['start'], time.time())


    def start(self) -> float:
        """
        For convenience, in case you want to print the time when
        you started.

        returns -- the time you began.
        """

        return self.laps['start']


    def lap(self, event:object=None) -> float:
        """
        Click the lap button. If you do not supply a name, then we
        call this event 'start+n", where n is the number of events 
        already recorded including start. 

        returns -- the time you clicked the lap counter.
        """
        if event:
            self.laps[event] = time.time()
        else:
            event = 'start+{}'.format(len(self.laps))
            self.laps[event] = time.time()

        return self.laps[event]
    

    @property
    def laps_data(self) -> dict:
        return { k : v-self.laps['start'] for k, v in self.laps.items() }


    def stop(self) -> float:
        """
        This function is a little different than the others, because
        it is here that we apply the scaling factor, and calc the
        differences between our laps and the start. 

        returns -- the time you declared stop.
        """
        return_value = self.laps['stop'] = time.time()
        diff = self.laps['start']
        for k in self.laps:
            self.laps[k] -= diff
            self.laps[k] *= self.units
            
        return return_value


    def __repr__(self) -> str:
        return str(self.laps)


    def __format__(self, spec=None) -> str:
        """
        Facilitate printing nicely.

        returns -- a nicely formatted list of events and time
            offsets from the beginning:

        Units are in sec/1000
        ------------------
        start     :  0.000000
        lap one   :  10191.912651
        start+2   :  15940.931320
        last lap  :  27337.829828
        stop      :  31454.867363

        """
        # w is the length of the longest event name.
        w = max(len(k) for k in self.laps)

        # A clever print statement is required.
        s = "{:" + "<{}".format(w) + "}  : {: f}"
        header = "Units are in sec/{}".format(self.units) + "\n" + "-"*(w+20) + "\n"

        return header + "\n".join([ s.format(k, self.laps[k]) for k in self.laps ])


