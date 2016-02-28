# -*- coding: utf-8 -*-

"""
Interface file to use processes.

QuDi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

QuDi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with QuDi. If not, see <http://www.gnu.org/licenses/>.

Copyright (C) 2015 Jan M. Binder jan.binder@uni-ulm.de
"""

from core.util.customexceptions import InterfaceImplementationError


class ProcessInterface():
    """ A very simple interface to measure a single value.
        Used for PID controll.
    """

    _modtype = 'ProcessInterface'
    _modclass = 'interface'

    def getProcessValue(self):
        """ Return a measured value """
        raise InterfaceImplementationError('ProcessInterface->getProcessValue')
        return -1

    def getProcessUnit(self):
        """ Return the unit that hte value is measured in as a tuple of ('abreviation', 'full unit name') """
        raise InterfaceImplementationError('ProcessInterface->getProcessUnit')
        return -1