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

from __future__ import (absolute_import, division,
                        print_function)
import six
import importlib
import time
import logging
from .scrape import vt_reserved
from vistrails.core.modules.vistrails_module import (Module, ModuleSettings,
                                                     ModuleError)

from vistrails.core.modules.config import IPort, OPort

logger = logging.getLogger(__name__)


# module-level 'constants' at bottom


def gen_module(input_ports, output_ports, docstring,
               module_name, library_func, module_namespace,
               dict_port=None):
    """
    Parameters
    ----------
    input_ports : list
       List of input ports

    output_ports : list
       List of output ports

    docstring : ?
    module_name : str
        The name of the module (as displayed in vistrails

    library_func : callable
        The callable object to be wrapped for VisTrails

    module_namespace : str
        Vistrails namespace to use

    dict_port : ?
    """
    # convert input/output specs into VT port objects
    input_ports = [IPort(**pdict) for pdict in input_ports]
    output_ports = [OPort(**pdict) for pdict in output_ports]
    mandatory = []
    optional = []

    # create the lists of mandatory and optional input ports
    for port in input_ports:
        if port == dict_port:
            # since dict port must be in the input_ports list but we dont want
            # to treat it as a normal input port, do not assign it as
            # optional or mandatory
            continue
        if port.optional:
            optional.append(port.name)
        else:
            mandatory.append(port.name)

    def compute(self):
        dict_from_port = {}
        params_dict = {}
        if dict_port is not None:
            dict_from_port = self.get_input(dict_port.name)

        for opt in optional:
            if opt in dict_from_port:
                # obtain the parameter from the passed in dict
                params_dict[opt] = dict_from_port[opt]
            if self.has_input(opt):
                if opt in vt_reserved:
                    p_name = '_' + opt
                else:
                    p_name = opt
                params_dict[opt] = self.get_input(p_name)

        for mand in mandatory:
            if mand in vt_reserved:
                p_name = '_' + mand
            else:
                p_name = mand
            if mand in dict_from_port:
                params_dict[mand] = dict_from_port[mand]
            try:
                params_dict[mand] = self.get_input(p_name)
            except ModuleError as me:
                if mand in params_dict:
                    # pass on this exception, as the dictionary on dict_port
                    # has taken care of this key
                    pass
                else:
                    logger.debug('The mandatory port {0} does not have input'
                                 'and the input dictionary is either not '
                                 'present or doesn\'t contain this key'
                                 ''.format(mand))
                    raise ModuleError(__name__, me)
        # check for the presence of a 'value' attribute on the incoming
        # port values. This indicates that this is a NSLS2 port type
        for name, val in six.iteritems(params_dict):
            if hasattr(val, 'value'):
                params_dict[name] = val.value
        ret = library_func(**params_dict)
        if len(output_ports) == 1:
            self.set_output(output_ports[0].name, ret)
        else:
            for (out_port, ret_val) in zip(output_ports, ret):
                self.set_output(out_port.name, ret_val)

    _settings = ModuleSettings(namespace=module_namespace)

    new_class = type(str(module_name),
                     (Module,), {'compute': compute,
                                 '__module__': __name__,
                                 '_settings': _settings,
                                 '__doc__': docstring,
                                 '__name__': module_name,
                                 '_input_ports': input_ports,
                                 '_output_ports': output_ports})
    return new_class


def gen_module_ufunc(input_ports, output_ports, docstring,
               module_name, library_func, module_namespace,
               dict_port=None):
    if dict_port is not None:
        raise NotImplementedError("Dict_port is not supported for ufuncs")
    # can't unpack dicts into ufuncs, assume all are
    # mandatory
    input_ports = [IPort(**pdict) for pdict in input_ports]
    output_ports = [OPort(**pdict) for pdict in output_ports]

    mandatory = input_ports
    arg_names = [m.name for m in mandatory]
    if len(mandatory) != library_func.nin:
        raise ValueError("wrap {} : \n".format(library_func.__name__) +
                         "the docstring parsing went wrong " +
                         "ufunc should have {} args".format(library_func.nin) +
                         " parsing docstring has {}".format(len(mandatory)))

    if len(output_ports) != library_func.nout:
        raise ValueError("wrap {} : \n".format(library_func.__name__) +
                         "the docstring parsing went wrong" +
                         "ufunc should have {} out".format(library_func.nout) +
                         " parsing docstring has {}".format(len(output_ports)))

    def compute(self):
        args = list()
        for arg_name in arg_names:
            args.append(self.get_input(arg_name))

        ret = library_func(*args)
        if len(output_ports) == 1:
            self.set_output(output_ports[0].name, ret)
        else:
            for (out_port, ret_val) in zip(output_ports, ret):
                self.set_output(out_port.name, ret_val)

    _settings = ModuleSettings(namespace=module_namespace)

    new_class = type(str(module_name),
                     (Module,), {'compute': compute,
                                 '__module__': __name__,
                                 '_settings': _settings,
                                 '__doc__': docstring,
                                 '__name__': module_name,
                                 '_input_ports': input_ports,
                                 '_output_ports': output_ports})
    return new_class


def normalize_name_space(namespace):
    """Clean up namespace paths

    Parameters
    ----------
    namespace : str
        A namespace spec which may be mal-formed (use '.', not '|'

    Returns
    -------
    vt_namespace : str
        The namespace formatted as VT expects (with '|' as separator)

    """
    if _VT_SEP in namespace:
        # do nothing, namespace is correctly formatted, yay!
        # we let other possible separators pass as-is
        return namespace
    else:
        # loop over the namespace separators
        for sep in _NAMESPACE_SEPS:
            # check for the presence of sep in the namespace input parameter
            if sep in namespace:
                # split the namespace so that it is separated by vertical bars
                # this will only replace the first one it finds, order in
                # _VT_SEP is precedence order.
                namespace = _VT_SEP.join(namespace.split(sep))
                return namespace
    # fall through if there are no separators, use as-is
    return namespace


def wrap_function(func_name, module_path, input_ports, output_ports,
                  doc_string, f_type,
                  add_input_dict=False, namespace=None):
    """Perform the wrapping of functions into VisTrails modules

    Parameters
    ----------
    func_name : str
        Name of the function to wrap into VisTrails. Example 'grid3d'

    module_path : str
        Name of the module which contains the function. Example: 'skxray.core'



    add_input_dict : bool, optional
        Flag that instructs the wrapping machinery to add a dictionary input
        port to the resultant VisTrails module. This dictionary port is
        solely a convenience function whose main purpose is to unpack the
        dictionary into the wrapped function

    namespace : str, optional
        Path to the function in VisTrails.  This should be a string separated
        by vertical bars: |.  Example: 'vis|test' will put the new VisTrail
        module at the end of expandable lists vis -> test -> func_name
        currently supports separations by '|' and '.'
    """
    # list common separators for the namespace argument

    # copy as we might mutate below
    input_ports = list(input_ports)
    # deal with default value
    if namespace is None:
        namespace = module_path
    # normalize separators
    namespace = normalize_name_space(namespace)

    logger.debug('func_name {0} has import path {1} and should be placed in'
                 ' namespace {3}. It should include an '
                 'input dictionary as a port ({2})'
                 ''.format(func_name, module_path, add_input_dict, namespace))
    t1 = time.time()

    if add_input_dict:
        # define a dictionary input port if necessary
        dict_port = dict(name='input_dict', signature=('basic:Dictionary'),
                          label='Dictionary of input parameters.'
                                'Convienence port')
        input_ports.append(dict_port)
    else:
        dict_port = None

    # look up the callable object
    mod = importlib.import_module(module_path)
    func = getattr(mod, func_name)
    # actually create the VisTrail module
    generated_module = _GEN_MOD_LOOKUP[f_type](input_ports=input_ports,
                                                output_ports=output_ports,
                                                docstring=doc_string,
                                                module_name=func_name,
                                                module_namespace=namespace,
                                                library_func=func,
                                                dict_port=dict_port)

    logger.info('func_name {0}, module_name {1}. Time: {2}'
                ''.format(func_name, module_path, format(time.time() - t1)))
    return generated_module


def wrap_class(class_name, module_path, add_input_dict=False, namespace=None):
    raise NotImplementedError("wrap_class is not implemented yet. "
                              "Go yell at Eric...")


_GEN_MOD_LOOKUP = {'func': gen_module,
                   'ufunc': gen_module_ufunc}
_NAMESPACE_SEPS = ('.', )
_VT_SEP = '|'
