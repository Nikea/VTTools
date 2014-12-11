# ######################################################################
# Copyright (c) 2014, Brookhaven Science Associates, Brookhaven        #
# National Laboratory. All rights reserved.                            #
#                                                                      #
# Redistribution and use in source and binary forms, with or without   #
# modification, are permitted provided that the following conditions   #
# are met:                                                             #
#                                                                      #
# * Redistributions of source code must retain the above copyright     #
#   notice, this list of conditions and the following disclaimer.      #
#                                                                      #
# * Redistributions in binary form must reproduce the above copyright  #
#   notice this list of conditions and the following disclaimer in     #
#   the documentation and/or other materials provided with the         #
#   distribution.                                                      #
#                                                                      #
# * Neither the name of the Brookhaven Science Associates, Brookhaven  #
#   National Laboratory nor the names of its contributors may be used  #
#   to endorse or promote products derived from this software without  #
#   specific prior written permission.                                 #
#                                                                      #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS  #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT    #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS    #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE       #
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,           #
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES   #
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR   #
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)   #
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,  #
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OTHERWISE) ARISING   #
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE   #
# POSSIBILITY OF SUCH DAMAGE.                                          #
########################################################################
from __future__ import (absolute_import, division, print_function,
                        )
import six
from bubblegum.qt_widgets import query_widget
from logging import Handler
from vistrails import api
from vistrails.core.modules.vistrails_module import Module, ModuleSettings
from vistrails.core.modules.config import IPort, OPort
from .broker import search_keys_dict
from .broker import search
import numpy as np
from metadataStore.utilities.utility import get_data_keys
import enaml
from enaml.qt.qt_application import QtApplication
import logging
logger = logging.getLogger(__name__)


def add_to_canvas(query_dict, unique_query_dict, single_result):

    # get the controller (will be needed to change the module names
    controller = api.get_current_controller()

    # add the broker module to the canvas
    mod_broker = api.add_module(0, -100, 'org.vistrails.vistrails.NSLS2',
                                'BrokerQuery', 'broker')

    api.change_parameter(mod_broker.id, 'query_dict', [query_dict])
    api.change_parameter(mod_broker.id, 'unique_query_dict',
                         [unique_query_dict])
    # refresh the canvas
    controller.current_pipeline_scene.recreate_module(
        controller.current_pipeline, mod_broker.id)

    # get the data dict from the data broker
    mod_dict = api.add_module(0, -200, 'org.vistrails.vistrails.NSLS2',
                              'CalibrationParameters', 'broker')
    # connect the broker to the dict
    api.add_connection(mod_broker.id, 'query_result', mod_dict.id, 'run_header')

    # get the datakeys from the run header
    data_keys = get_data_keys(single_result)
    if 'time' in data_keys:
        data_keys.remove('time')
    horz_offset = 250
    init_horz = -300
    vert_offset = -300

    for index, (key) in enumerate(data_keys):
        # add the vistrails module for the listify key
        # add the vistrails module for the listify operation
        mod_listify = api.add_module(init_horz + horz_offset * index,
                                     vert_offset,
                                     'org.vistrails.vistrails.NSLS2',
                                     'Listify', 'broker')
        # change the key parameter to be 'key'
        api.change_parameter(mod_listify.id, 'data_key', [key])
        # change the module name to [key]
        controller.add_annotation(('__desc__', key),
                                  mod_listify.id)
        # refresh the canvas
        controller.current_pipeline_scene.recreate_module(
            controller.current_pipeline, mod_listify.id)

        # connect the broker result to the listify module
        api.add_connection(mod_broker.id, 'query_result',
                           mod_listify.id, 'run_header')


def gen_unique_id(run_header):
    """
    Create a unique search dictionary from the run header that gets fed in.

    Parameters
    ----------
    run_header : dict
        The run header that gets returned by the data broker

    Returns
    -------
    dict
        Search dictionary that, when unpacked into
        metadataStore.userapi.commands.search will guarantee that a single run
        header is returned
    """
    logger.debug("run_header.__class__: {0}".format(run_header.__class__))
    logger.debug("run_header: {0}".format(run_header))
    return_dict = {"owner": run_header["owner"],
                   "data": True,
                   "scan_id": run_header["scan_id"]
                   }

    return return_dict


def search_databroker(search_dict):
    """
    Function that gets fed to the query widget which gets executed when the
    'search' button is pressed

    Parameters
    ----------
    search_dict : dict
        Dictionary which has k:v pairs that
        metadataStore.userapi.commands.search understands

    Returns
    -------
    dict
        Dictionary of run headers that get returned by the data broker
    """
    result = search(**search_dict)
    logger.debug('search_dict: {0}'.format(search_dict))

    return result


# query_window = query_widget.QueryMainWindow(keys=search_keys_dict,
#                                             search_func=search_databroker,
#                                             add_func=add_to_canvas,
#                                             unique_id_func=gen_unique_id)


from bubblegum.xrf.model.xrf_model import XRF
with enaml.imports():
    from bubblegum.xrf.view.xrf_view import XrfGui

xrf_view = XrfGui()
xrf_view.xrf_model = XRF()

def setup_bnl_menu():
    """
    Creates and hooks up a BNL specific menu in the main window
    """
    bw = api.get_builder_window()
    # grab the menu bar
    menu_bar = bw.menuBar()

    bnl_menu = menu_bar.addMenu("BNL")
    print('\n\n\n\n\n\nBNL Menu Added\n\n\n\n\n\n\n\n\n')

    def foo():
        print('menu bar clicked!')
        # query_window.show()
        xrf_view.show()


    bnl_menu.addAction("demo", foo)


class ForwardingHandler(Handler):
    """

    This Handler forwards all records on to some other logger.  This is
    useful when integrating with an existing libraries/programs/GUIs
    that make use of logging.  This allows messages to hop between logger
    trees to either capture logging or inject messages into other handlers.

    Parameters
    ----------
    other_logger : logging.Logger
        The logger to forward
    """
    def __init__(self, other_logger):
        Handler.__init__(self)
        self._other_logger = other_logger

    def emit(self, record):
        self._other_logger.handle(record)


class Flatten(Module):
    _settings = ModuleSettings(namespace="utility")

    _input_ports = [
        IPort(name="list_of_lists",
              label="List of lists to flatten",
              signature="basic:List"),
    ]

    _output_ports = [
        OPort(name="flattened", signature="basic:List"),
    ]

    def compute(self):
        # gather input
        lists = self.get_input('list_of_lists')
        raveled = [np.ravel(im) for im in lists]
        flattened = [item for sublist in raveled for item in sublist]
        self.set_output('flattened', flattened)


class Average(Module):
    _settings = ModuleSettings(namespace="utility")

    _input_ports = [
        IPort(name="input",
              label="Iterable to compute the average of",
              signature="basic:Variant"),
    ]

    _output_ports = [
        OPort(name="avg", signature="basic:Float"),
        OPort(name="avg_str", signature="basic:String"),
    ]

    def compute(self):
        # gather input
        input = self.get_input('input')
        # np.average(input)
        avg = np.average(input)

        self.set_output('avg',  avg)
        self.set_output('avg_str',  str(avg))


class SwapAxes(Module):
    _settings = ModuleSettings(namespace="utility")
    _input_ports = [
        IPort(name='arr',
              label='N-D array',
              signature='basic:List'),
        IPort(name='ax0',
              label='Axis to swap from',
              signature='basic:Integer'),
        IPort(name='ax1',
              label='Axis to swap from',
              signature='basic:Integer'),
    ]
    _output_ports = [
        OPort(name='out',
              signature='basic:List')
    ]

    def compute(self):
        arr = self.get_input('arr')
        ax0 = self.get_input('ax0')
        ax1 = self.get_input('ax1')
        arr = np.asarray(arr)

        self.set_output('out', np.swapaxes(arr, ax0, ax1))


class Crop2D(Module):
    """Cropping Module

    Create a binary mask for an image based on two points

    +---------------------+
    |                     |
    | p1-> +----+         |
    |      |    |         |
    |      +----+ <- p2   |
    |                     |
    +---------------------+

    p1 = (row, col)
    p2 = (row, col)

    Input ports are p1r, p1c, p2r, p2c.  Any combination of input ports are
    valid.  If either of the p1 ports are not present their value will set to
    zero.  If either of the p2 ports are not present, their value will be set
    to the number of rows or columns, respectively.
    """

    _settings = ModuleSettings(namespace="utility")
    _input_ports = [
        IPort(name='num_rows',
              label='Number of rows in the image',
              signature='basic:Integer'),
        IPort(name='num_cols',
              label='Number of columns in the image',
              signature='basic:Integer'),
        IPort(name='top_left_row',
              label='pixel coordinate of the row of the top left corner',
              signature='basic:Integer'),
        IPort(name='top_left_column',
              label='pixel coordinate of the column of the top left corner',
              signature='basic:Integer'),
        IPort(name='bottom_right_row',
              label='pixel coordinate of the row of the bottom right corner',
              signature='basic:Integer'),
        IPort(name='bottom_right_column',
              label='pixel coordinate of the column of the bottom right corner',
              signature='basic:Integer'),
    ]
    _output_ports = [
        OPort(name='bin_mask',
              signature='basic:Variant')
    ]

    def compute(self):
        rows = self.get_input('num_rows')
        cols = self.get_input('num_rows')
        im = np.zeros((rows, cols), 'Bool')
        p1c = 0
        p1r = 0
        p2c = cols
        p2r = rows
        if self.has_input('top_left_column'):
            p1c = self.get_input('top_left_column')
        if self.has_input('top_left_row'):
            p1r = self.get_input('top_left_row')
        if self.has_input('bottom_right_column'):
            p2c = self.get_input('bottom_right_column')
        if self.has_input('bottom_right_row'):
            p2r = self.get_input('bottom_right_row')

        im[p1r:p2r, p1c:p2c] = True

        self.set_output('bin_mask', im)


def vistrails_modules():
    setup_bnl_menu()
    return [Flatten, Average, SwapAxes, Crop2D]
