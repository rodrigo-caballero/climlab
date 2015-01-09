import numpy as np
import constants as const
from model import _Model


class _TimeSteppingModel(_Model):
    '''A generic parent class for all time-dependent models that use a
    discete forward timestep.'''
    def __init__(self, **kwargs):
        # Create the model dataset
        super(_TimeSteppingModel, self).__init__(**kwargs)
        self.createGroup('timestepping')
        #  time will be an unlimited dimension
        self.createDimension('time', None)
        # Initialize time stepping
        self.set_timestep()
        #  Daughter classes will need to do a bunch of other initialization

    def set_timestep(self, num_steps_per_year=90):
        '''Change the timestep, given a number of steps per calendar year.'''
        self.param('num_steps_per_year', num_steps_per_year)
        self.param('timestep', const.seconds_per_year / self.param('num_steps_per_year'))
        timestep_days = self.param('timestep') / const.seconds_per_day
        days_of_year = np.arange(0., const.days_per_year, timestep_days)
        self.groups['timestepping'].createVariable('days_of_year',
                                                   'float', ('time',))
        self.groups['timestepping'].variables['days_of_year'][:] = days_of_year
        self.param('day_of_year_index', 0, paramType='int')
        self.param('steps', 0, paramType='int')
        self.param('days_elapsed', 0., paramType='float')
        self.param('years_elapsed', 0, paramType='int')

    def step_forward(self):
        '''Daughter classes need to implement details
        for changes in model state.'''
        pass
        self._update_time()

    def _update_time(self):
        '''Increment the timestep counter by one.
        This function is called by the timestepping routines.'''
        self.param('steps') += 1
        # time in days since beginning
        self.param('days_elapsed') += self.param('timestep') / const.seconds_per_day
        if self.param('day_of_year_index') >= self.param('num_steps_per_year')-1:
            self._do_new_calendar_year()
        else:
            self.param('day_of_year_index') += 1

    def _do_new_calendar_year(self):
        '''This function is called once at the end of every calendar year.'''
        self.param('day_of_year_index', 0)  # back to Jan. 1
        self.param('years_elapsed') += 1

    def integrate_years(self, years=1.0, verbose=True):
        '''Timestep the model forward a specified number of years.'''
        numsteps = int(self.num_steps_per_year * years)
        if verbose:
            print("Integrating for " + str(numsteps) + " steps or "
                  + str(years) + " years.")
        #  This implements a generic time-averaging feature
        # using the list of model state variables
        self.state_timeave = {}
        for varname, value in self.state.items():
            self.state_timeave[varname] = np.zeros_like(value)
        #  begin time loop
        for count in range(numsteps):
            self.step_forward()
            for varname, value in self.state.items():
                self.state_timeave[varname] += value
        for varname, value in self.state.items():
            self.state_timeave[varname] /= numsteps
        if verbose:
            print("Total elapsed time is " +
                  str(self.days_elapsed/const.days_per_year) + " years.")

    def integrate_days(self, days=1.0, verbose=True):
        '''Timestep the model forward a specified number of days.'''
        numsteps = int(self.num_steps_per_year / const.days_per_year * days)
        if verbose:
            print("Integrating for " + str(numsteps) + " steps or " +
                  str(days) + " days.")
        #  begin time loop
        for count in range(numsteps):
            self.step_forward()
        if verbose:
            print("Total elapsed time is " +
                  str(self.days_elapsed/const.days_per_year) + " years.")
