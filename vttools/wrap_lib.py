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
                        print_function, unicode_literals)
import six
import inspect
import importlib
import pprint
import time
import sys
import logging
import re
from collections import OrderedDict
from numpydoc.docscrape import FunctionDoc, ClassDoc
from vistrails.core.modules.vistrails_module import (Module, ModuleSettings,
                                                     ModuleError)
from vistrails.core.modules.config import IPort, OPort
import numpy as np

logger = logging.getLogger(__name__)


class AutowrapError(Exception):
    '''Exception to flag an autowrapping error

    '''
    pass

def obj_src(py_obj, escape_docstring=True):
    """Get the source for the python object that gets passed in

    Parameters
    ----------
    py_obj : obj
        Any python object

    escape_doc_string : bool
        If true, prepend the escape character to the docstring triple quotes

    Returns
    -------
    list
        Source code lines

    Raises
    ------
    IOError
        Raised if the source code cannot be retrieved
    """
    src = inspect.getsource(py_obj)
    if escape_docstring:
        src.replace("'''", "\\'''")
        src.replace('"""', '\\"""')
    return src
    # return src.split('\n')


def docstring_class(pyobj):
    """Get the docstring dictionary of a class

    Parameters
    ----------
    pyobj : function name or class name
        Any object in Python for which you want the docstring

    Returns
    -------
    ClassDoc
        If pyobj is a class

    A dictionary of the formatted numpy docstring can be
        accessed by :code:`return_val._parsed_data`
        Keys:
            'Signature': '',
            'Summary': [''],
            'Extended Summary': [],
            'Parameters': [],
            'Returns': [],
            'Raises': [],
            'Warns': [],
            'Other Parameters': [],
            'Attributes': [],
            'Methods': [],
            'See Also': [],
            'Notes': [],
            'Warnings': [],
            'References': '',
            'Examples': '',
            'index': {}
    Taken from:
        https://github.com/numpy/numpydoc/blob/master/numpydoc/docscrape.py#L94
    """
    if inspect.isclass(pyobj):
        return ClassDoc(pyobj)
    else:
        raise ValueError("The pyobj input parameter is not a class."
                         "Your parameter returned {0} from "
                         "type(pyobj)".format(type(pyobj)))


def docstring_func(pyobj):
    """Get the docstring dictionary of a function

    Parameters
    ----------
    pyobj : function name
        Any object in Python for which you want the docstring

    Returns
    -------
    FunctionDoc
        If pyobj is a function or class method

    A dictionary of the formatted numpy docstring can be
        accessed by :code:`return_val._parsed_data`
        Keys:
            'Signature': '',
            'Summary': [''],
            'Extended Summary': [],
            'Parameters': [],
            'Returns': [],
            'Raises': [],
            'Warns': [],
            'Other Parameters': [],
            'Attributes': [],
            'Methods': [],
            'See Also': [],
            'Notes': [],
            'Warnings': [],
            'References': '',
            'Examples': '',
            'index': {}
    Taken from:
        https://github.com/numpy/numpydoc/blob/master/numpydoc/docscrape.py#L94
    """
    if inspect.isfunction(pyobj) or inspect.ismethod(pyobj):
        return FunctionDoc(pyobj)
    else:
        raise ValueError("The pyobj input parameter is not a function."
                         "Your parameter returned {0} from "
                         "type(pyobj)".format(type(pyobj)))


sig_map = {
    'ndarray': 'basic:Variant',
    'array': 'basic:Variant',
    'array_like': 'basic:Variant',
    'np.ndarray': 'basic:Variant',
    'list': 'basic:List',
    'int': 'basic:Integer',
    'integer': 'basic:Integer',
    'scalar': 'basic:Float',
    'float': 'basic:Float',
    'tuple': 'basic:Tuple',
    'dict': 'basic:Dictionary',
    'bool': 'basic:Boolean',
    'str': 'basic:String',
    'string': 'basic:String',
    'numpy.dtype': 'basic:String',
    'np.dtype': 'basic:String',
    'dtype': 'basic:String',
    'sequence': 'basic:List'
}


def pytype_to_vtsig(param_type, param_name):
    """Transform 'arg_type' into a vistrails port signature

    Parameters
    ----------
    param_type : str
        The type of the parameter from the library function to be wrapped

    param_name : str
        The name of the parameter from the library function to be wrapped

    Returns
    -------
    port_sig : str
        The VisTrails port signature
    """
    port_sig = None
    # bash to lower case
    param_name = param_name.lower()
    param_type = param_type.lower()
    # see if special handling needs to occur because of the parameter name
    if param_name in sig_map:
        port_sig = sig_map[param_name]
    # if no special handling is required then create a port based on the
    # parameter type
    elif param_type in sig_map:
        port_sig = sig_map[param_type]
    if port_sig is None:
        # if no arg_type matches the pytypes that relate to VisTrails port sigs
        # raise a value error
        raise ValueError("The arg_type doesn't match any of the options.  Your "
                         "arg_type is: {0}.  See the sig_type dictionary in "
                         "userpackages/autowrap/wrap_lib.py".format(param_type))

    return port_sig


def _type_optional(type_str):
    """
    Helper function to sort out if a parameter is optional

    This assumes the type is given by a string that is compliant with
    the numpydoc format.

    Parameters
    ----------
    type_str : str
        The type specification from the docstring

    Returns
    -------
    type_str : str
        The type specification with out the optional flag

    is_optional : bool
        If the input is optional
    """
    type_str = type_str.strip()
    is_optional = type_str.endswith('optional')
    if is_optional:
        type_str = type_str[:-8].strip(', ')

    return type_str, is_optional


_ENUM_RE = re.compile('\{(.*)\}')
_ARRAY_SHAPE = re.compile('\(([A-Za-z0-9]+, *)+,?\) *array')


def _enum_type(type_str):
    """
    Helper function to check if the docstring enumerates options

    Parameters
    ----------
    type_str : str
        String specifying the input type. This string was stripped from the
        numpydoc string.

    Returns
    -------
    type_out : str
        The type of the input suitable for translation to VT types

    is_enum : bool
        Boolean switch specifying whether inputs include enumerated options.
    """
    m = _ENUM_RE.search(type_str)
    if bool(m):
        is_enum = True
        enum_list = [_.strip('\'\" ') for _ in m.group(1).split(',')]
        guessed_types = [_guess_type(_) for _ in enum_list]
        type_out = guessed_types[0]
        if not all(_ == type_out for _ in guessed_types[1:]):
            raise ValueError('mixed type enum, wtf mate')
        if type_out not in ('int', 'str'):
            raise ValueError('enum is not discrete, wtf mate')
    else:
        is_enum = False
        enum_list = None
        type_out = type_str

    return type_out, is_enum, enum_list


def _sized_array(type_str):
    if bool(_ARRAY_SHAPE.search(type_str)):
        return 'array'
    return type_str


def _check_alt_types(type_str):
    """
    This function checks for, and enables proper sorting of unique or
    atypical input types. The hierarchy devised thus far:
    1) input type strings stating float or int automatically cast to float,
        since most operations will interpret or convert a float input to an
        int if and when required. It is expected that type casting where
        float instead of int will cause problems will have been explicitly
        stipulated to be int, without any ambiguity.
    2) any complex type that includes the option to be a tuple will
        automatically be cast to tuple. Thus far most of these cases state
        that the input should be a scalar or a tuple, in which case the scalar
        input will simply need to be repeated for each array dimension
        (e.g. (x,x,x) for a isotropic 3D array type, or (x,x) for a 2D array
        type.
    3) the most unique type cast thus far 'scalar or sequence of scalars'
        will simply cast to scalar, unless we run into problems where this won't
        work.

    Parameters
    ----------
    type_str : str
        variable type stripped from original doc string

    Returns
    -------
    output : str
        corrected variable type for proper wrapping into vistrails

    Notes
    -----
    Record of Alternate Output Types
        'ndarray of bools' -- See: scipy.ndimage.morphology.binary_opening
    """
    if 'float' in type_str and 'int' in type_str:
        type_str = 'float'
    elif 'tuple' in type_str:
        type_str = 'tuple'
    elif 'int' in type_str and 'float' not in type_str and 'tuple' not in \
            type_str:
        type_str = 'int'
    elif 'sequence' in type_str:
        type_str = 'list'
    elif 'ndarray' in type_str:
        type_str = 'ndarray'
    return type_str


def _truncate_description(original_description, word_cnt_to_include):
    """
    This function will truncate the stripped doc string to a more manageable
    length for incorporation into wrapped vistrails functions

    Parameters
    ----------
    original_description : list
        This object is the original description stripped from the
        doc string. The object is actually a list of strings.

    word_cnt_to_include : int
        specify the number of words to trim the description down to

    Returns
    -------
    short_description : string
        truncated description that will be passed into vistrails
    """
    short_description = original_description[0]
    if len(original_description[0].split(' ')) > word_cnt_to_include:
        short_description = (
            original_description[0].split(' ')[0:word_cnt_to_include]
            )
    short_description = ' '.join(short_description)
    return short_description


def _guess_type(stringy_val):
    """
    Helper function to guess the type of values in an enum are.

    At this point it tries int, float, and complex and then assumes it is
    a string.

    Parameters
    ----------
    stringy_val : str
        The value to guess the type of

    Returns
    -------
    type_str : {'int', 'float', 'complex', 'str'}
        The guessed type as a string.
    """
    od = OrderedDict()
    od['int'] = int
    od['float'] = float
    od['complex'] = complex

    for k, v in six.iteritems(od):
        try:
            v(stringy_val)
            return k
        except ValueError:  # I think it's a value error
            pass
    # give up and assume it is a string
    return 'str'


def define_input_ports(docstring, func):
    """Turn the 'Parameters' fields into VisTrails input ports

    Parameters
    ----------
    docstring : NumpyDocString
        The scraped docstring from the

    func : function
        The actual python function

    Returns
    -------
    input_ports : list
        List of input_ports (Vistrails type IPort)
    """
    input_ports = []
    short_description_word_count = 4
    if 'Parameters' not in docstring:
        # raised if 'Parameters' is not in the docstring
        raise KeyError('Docstring is not formatted correctly. There is no '
                       '"Parameters" field. Your docstring: {0}'
                       ''.format(docstring))

    for (the_name, the_type, the_description) in docstring['Parameters']:
        if the_name == 'output':
            continue
        the_type, is_optional = _type_optional(the_type)
        the_type, is_enum, enum_list = _enum_type(the_type)
        the_type = _sized_array(the_type)

        # Accounts for extraneous notes or lines in doc string that are not
        # actually input or output parameters
        if the_type == '':
            continue
        # Finish checking for alternate, complicated, or unique doc types
        the_type = _check_alt_types(the_type)
        # Trim parameter descriptions for incorporation into vistrails
        short_description = _truncate_description(the_description,
                                                  short_description_word_count)

        logger.debug("the_name is {0}. \n\tthe_type is {1} and it is "
                     "optional: {3}. \n\tthe_description is {2}"
                     "".format(the_name, the_type,
                               ' '.join(short_description),
                               is_optional))

        for port_name in (_.strip() for _ in the_name.split(',')):
            if not port_name:
                continue
            port_type = the_type
            port_is_enum = is_enum
            port_enum_list = enum_list
            # start with the easy ones
            pdict = {'name': port_name,
                     'label': ' '.join(short_description),
                     'optional': is_optional,
                     'signature': pytype_to_vtsig(param_type=port_type,
                                                  param_name=port_name)}

            # deal with if the function as an enum attribute
            if hasattr(func, port_name):
                f_enums = getattr(func, port_name)
                if port_is_enum:
                    # if we already think this is an enum, make sure they
                    # match
                    if len(f_enums) != len(enum_list):
                        raise ValueError('Attempting to automatically create '
                                         'an enum port for the function named'
                                         ' {0}. The values for the enum port '
                                         'defined in the doc string are {1} '
                                         'with length {2} and there is a '
                                         'function attribute with values {3} '
                                         'and length {4}.  Please make sure '
                                         'the values in the docstring agree '
                                         'with the values in the function '
                                         'attribute, as I\'m not sure which '
                                         'to use.'.format(the_name,
                                                          enum_list,
                                                          len(enum_list),
                                                          f_enums,
                                                          len(f_enums)))
                port_enum_list = f_enums
                port_is_enum = True
            if port_is_enum:
                pdict['entry_type'] = 'enum'
                pdict['values'] = port_enum_list

            logger.debug('port_param_dict: {0}'.format(pdict))
            input_ports.append(IPort(**pdict))

    if len(input_ports) == 0:
        logger.debug('dir of input_ports[0]: {0}'.format(dir(input_ports[0])))
    return input_ports


def define_output_ports(docstring):
    """Turn the 'Returns' fields into VisTrails output ports

    Parameters
    ----------
    docstring : NumpyDocString
        The scraped docstring from the

    Returns
    -------
    input_ports : list
        List of input_ports (Vistrails type IPort)
    """

    output_ports = []
    short_description_word_count = 4
    if len(docstring['Returns']) == 0:
        for (the_name, the_type, the_description) in docstring['Parameters']:
            if the_name.lower() == 'output':
                the_type, is_optional = _type_optional(the_type)
                the_type, is_enum, enum_list = _enum_type(the_type)
                the_type = _sized_array(the_type)
                # Accounts for extraneous notes or lines in doc string that are not
                # actually input or output parameters
                if the_type == '':
                    continue
                # Finish checking for alternate, complicated, or unique doc types
                the_type = _check_alt_types(the_type)
                # Trim parameter descriptions for incorporation into vistrails
                short_description = _truncate_description(the_description,
                                                  short_description_word_count)
                output_ports.append(OPort(name=the_name,
                                          signature=pytype_to_vtsig(
                                              param_type=the_type,
                                              param_name=the_name)))
    elif 'Returns' not in docstring:
        # Verify that output was not included in the 'Parameters' section
        for (the_name, the_type, the_description) in docstring['Parameters']:
            if the_name.lower() == 'output':
                the_type, is_optional = _type_optional(the_type)
                the_type, is_enum, enum_list = _enum_type(the_type)
                the_type = _sized_array(the_type)
                if the_type == '':
                    continue
                the_type = _check_alt_types(the_type)
                short_description = _truncate_description(the_description,
                                                  short_description_word_count)
                output_ports.append(OPort(name=the_name,
                                          signature=pytype_to_vtsig(
                                              param_type=the_type,
                                              param_name=the_name)))
        # Now, if output_ports remains empty, then KeyError gets raised.
        if len(output_ports) == 0:
            raise KeyError('Docstring is not formatted correctly. '
                           'There is no "Returns" field. '
                           'Your docstring: {0}'.format(docstring))
    for (the_name, the_type, the_description) in docstring['Returns']:
        the_type, is_optional = _type_optional(the_type)
        the_type, is_enum, enum_list = _enum_type(the_type)
        the_type = _sized_array(the_type)
        if the_type == '':
            continue
        the_type = _check_alt_types(the_type)
        short_description = _truncate_description(the_description,
                                                  short_description_word_count)

        logger.debug("the_name is {0}. \n\tthe_type is {1}. "
                     "\n\tthe_description is {2}"
                     "".format(the_name, the_type, the_description))
        try:
            output_ports.append(OPort(name=the_name,
                                      signature=pytype_to_vtsig(
                                          param_type=the_type,
                                          param_name=the_name)))
        except ValueError as ve:
            logger.error('ValueError raised for Returns parameter with '
                         'name: {0}\n\ttype: {1}\n\tdescription: {2}'
                         ''.format(the_name, the_type, the_description))
            six.reraise(ValueError, ve, sys.exc_info()[2])
    return output_ports


def gen_module(input_ports, output_ports, docstring,
               module_name, library_func, module_namespace,
               dict_port=None):

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
                params_dict[opt] = self.get_input(opt)

        for mand in mandatory:
            if mand in dict_from_port:
                params_dict[mand] = dict_from_port[mand]
            try:
                params_dict[mand] = self.get_input(mand)
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
            print('name [{0}] has attribute value [{1}]'.format(name, val))
            if hasattr(val, 'value'):
                print('name [{0}] has attribute value [{1}]'.format(name, val))
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


def wrap_function(func_name, module_path, add_input_dict=False, namespace=None):
    """Perform the wrapping of functions into VisTrails modules

    Parameters
    ----------
    func_name : str
        Name of the function to wrap into VisTrails. Example 'grid3d'

    module_path : str
        Name of the module which contains the function. Example: 'nsls2.core'

    add_input_dict : bool, optional
        Flag that instructs the wrapping machinery to add a dictionary input
        port to the resultant VisTrails module. This dictionary port is
        solely a convenience function whose main purpose is to unpack the
        dictionary into the wrapped function

    namespace : str
        Path to the function in VisTrails.  This should be a string separated
        by vertical bars: |.  Example: 'vis|test' will put the new VisTrail
        module at the end of expandable lists vis -> test -> func_name
        currently supports separations by '|' and '.'
    """
    # list common separators for the namespace argument
    namespace_seps = ['.']
    vt_sep = '|'
    if namespace is None:
        namespace = vt_sep.join(module_path.split('.')[1:])
        if not namespace:
            namespace = module_path
    elif vt_sep in namespace:
        # do nothing, namespace is correctly formatted, yay!
        pass
    else:
        # loop over the namespace separators
        for sep in namespace_seps:
            # check for the presence of sep in the namespace input parameter
            if sep in namespace:
                # split the namespace so that it is separated by vertical bars
                namespace = vt_sep.join(module_path.split(sep))
                # dont let it iterate again
                break

    logger.debug('func_name {0} has import path {1} and should be placed in'
                 ' namespace {3}. It should include an '
                 'input dictionary as a port ({2})'
                 ''.format(func_name, module_path, add_input_dict, namespace))
    t1 = time.time()
    # func_name, mod_name = imp
    mod = importlib.import_module(module_path)
    func = getattr(mod, func_name)

    try:
        # get the source of the function
        src = obj_src(func)
    except IOError as ioe:
        # raised if the source cannot be found
        logger.debug("IOError raised when attempting to get the source"
                     "for function {0}".format(func))
        raise IOError(ioe)
    try:
        # get the docstring of the function
        doc = docstring_func(func)
    except ValueError as ve:
        err = ("ValueError raised when attempting to get docstring for "
               "function {0}\nOriginal error was: {1}").format(func, ve)
        logger.error(err)
        six.reraise(AutowrapError, err, sys.exc_info()[2])
    try:
        # create the VisTrails input ports
        input_ports = define_input_ports(doc._parsed_data, func)
        pprint.pprint(input_ports)
    except ValueError as ve:
        err = ("ValueError raised when attempting to format input_ports in "
               "function {0}\nOriginal error was: {1}").format(func, ve)
        logger.error(err)
        six.reraise(AutowrapError, err, sys.exc_info()[2])
    try:
        # create the VisTrails output ports
        output_ports = define_output_ports(doc._parsed_data)
    except ValueError as ve:
        err = ("ValueError raised when attempting to format output_ports in "
               "function {0}\nOriginal error was: {1}").format(func, ve)
        logger.error(err)
        six.reraise(AutowrapError, err, sys.exc_info()[2])
    if add_input_dict:
        # define a dictionary input port if necessary
        dict_port = IPort(name='input_dict', signature=('basic:Dictionary'),
                          label='Dictionary of input parameters.'
                                'Convienence port')
        input_ports.append(dict_port)
    else:
        dict_port = None

    # actually create the VisTrail module
    generated_module = gen_module(input_ports=input_ports,
                                  output_ports=output_ports,
                                  docstring=src, module_name=func_name,
                                  module_namespace=namespace,
                                  library_func=func,
                                  dict_port=dict_port)

    logger.info('func_name {0}, module_name {1}. Time: {2}'
                ''.format(func_name, module_path, format(time.time() - t1)))
    return generated_module


def wrap_class(class_name, module_path, add_input_dict=False, namespace=None):
    raise NotImplementedError("wrap_class is not implemented yet. "
                              "Go yell at Eric...")

if __name__ == "__main__":
    pass
