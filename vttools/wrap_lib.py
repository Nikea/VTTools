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
import inspect
import importlib
import time
import sys
import logging
import re
from collections import OrderedDict
from numpydoc.docscrape import FunctionDoc, ClassDoc
from vistrails.core.modules.vistrails_module import (Module, ModuleSettings,
                                                     ModuleError)
from vistrails.core.modules.config import IPort, OPort

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
        raise ValueError("The arg_type doesn't match any of the options.  "
                         "Your "
                         "arg_type is: \n\n\t{0}\n\nSee the sig_type "
                         "dictionary in "
                         "VTTools/vttools/wrap_lib.py".format(param_type))

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
    type_str = type_str.strip(' .')
    is_optional = type_str.endswith('optional')
    if is_optional:
        type_str = type_str[:-8].strip(', ')

    return type_str, is_optional

_ENUM_RE = re.compile('\{(.*)\}')
_RE_DICT = {
    "object": re.compile('^(?i)(any|object)$'),
    "array": re.compile('^(?i)(\(((([A-Z0-9.]+,? *)+)|, ?)\))? *(((np|numpy)\.)?(nd)?array(_|-| )?(like)?)$'),  # noqa,
    "matrix": re.compile('^(?i)(\((([A-Z0-9.]+,? *){2} ?)\))? *(((np|numpy)\.)?matrix(_|-| )?(like)?)$'),  # noqa,
    # note these three do not match end so 'list of ... ' matches
    "list": re.compile('^(?i)list(-|_| )?(like)?'),
    "tuple": re.compile('^(?i)tuple(-|_| )?(like)?'),
    "seq": re.compile('^(?i)sequence(-|_| )?(like)?'),
    "dtype": re.compile('^(?i)((np|numpy)\.)?dtype(-|_| )?(like)?$'),
    "bool": re.compile('^(?i)bool(ean)?$'),
    "file": re.compile('^(?i)file?$'),
    "scalar": re.compile('^(?i)scalar?$'),
    "float": re.compile('^(?i)(((np|numpy)\.)?float(16|32|64|128)?|double|single)$'),  # noqa,
    "int": re.compile('^(?i)((np|numpy)\.)?u?int(eger)?(8|16|32|64)?$'),
    "complex": re.compile('^(?i)complex$'),
    "dict": re.compile('^(?i)dict(ionary)?$'),
    "str": re.compile('^(?i)str(ing)?$'),
    'callable': re.compile('^(?i)(func(tion)?|callable)$'),
}

sig_map = {
    'object': 'basic:Variant',
    'array': 'basic:Variant',
    'matrix': 'basic:Variant',
    'list': 'basic:List',
    'tuple': 'basic:Tuple',
    'seq': 'basic:List',
    'dtype': 'basic:String',
    'bool': 'basic:Boolean',
    'file': 'basic:File',
    'scalar': 'basic:Float',
    'float': 'basic:Float',
    'int': 'basic:Integer',
    'complex': 'basic:Complex',
    'dict': 'basic:Dictionary',
    'str': 'basic:String',
    'callable': 'basic:Variant'
}


precedence_list = ('list',
                       'tuple',
                       'seq',
                       'dict',
                       'array',
                       'matrix',
                       'dtype',
                       'str',
                       'scalar',
                       'complex',
                       'float',
                       'int',
                       'bool',
                       'file',
                       'callable',
                       'object')


#   RE Details:
#   WORKS: test_str5 = "(your, mother, was, a, hampster) array"
#   WORKS: test_str5 = "(your, mother, was, a, hampster,) array"
# TODO: We may want to make more thorough use of this RE by using the
#   specified values inside the parentheses as an additional input or output
#   port key (e.g. 2D, 3D, 1xN, NxN, NxM, LxMxN, etc.)


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
            raise ValueError('Mixed type enum, docstring parameters are '
                             'improperly defined. Please fix and create pull '
                             'request, or report this error to the Software '
                             'Development Team.')
        if type_out not in ('int', 'str'):
            raise ValueError('Enum is not discrete, docstring parameters are '
                             'improperly defined. Please fix and create pull '
                             'request, or report this error to the Software '
                             'Development Team.')
    else:
        is_enum = False
        enum_list = None
        type_out = type_str

    return type_out, is_enum, enum_list


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
    # need this twice, might as well stash it
    sd_words = short_description.split(' ')
    # if it's too long, drop some words
    if len(sd_words) > word_cnt_to_include:
        short_description = ' '.join(sd_words[:word_cnt_to_include])

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
        except ValueError:
            pass
    # give up and assume it is a string
    return 'str'

_OR_REGEX = re.compile(r'\bor\b')
_OF_REGEX = re.compile(r'\bof\b')


def _normalize_type(the_type):
    """
    A single entry point for parsing the type.

    This assumes that enums and optional properties have been
    taken care of.

    Parameters
    ----------
    the_type : str
        The type string extracted from the docs

    Returns
    -------
    norm_type : str
        The normalized type
    """
    # get rid of all leading and trailing junk
    the_type = the_type.strip(' .!?-_\t')
    # if 'or'
    if _OR_REGEX.search(the_type):
        left, right = the_type.split('or', 1)
        return _type_precedence(left, right)

    if _OF_REGEX.search(the_type):
        left, right = the_type.split('of', 1)
        return _of_proc(left, right)

    # Walk the precedence list to see what we get
    for n_type in precedence_list:
        if bool(_RE_DICT[n_type].search(the_type)):
            return n_type

    # of no patterns matched, return None to signal
    # failure and let down-stream sort it out.
    return None


def _of_proc(left, right):
    """

    """
    return _normalize_type(left)


def _type_precedence(left, right):
    """
    Reduce a pair of types to a single type by picking
    which one to return.


    """
    left = _normalize_type(left)
    right = _normalize_type(right)
    if left is None:
        return right
    elif right is None:
        return left

    left_i = precedence_list.index(left)
    right_i = precedence_list.index(right)
    return left if left_i < right_i else right


def define_input_ports(docstring, func):
    """Turn the 'Parameters' fields into VisTrails input ports

    Parameters
    ----------
    docstring : List of strings?
        The scraped docstring from the NumpyDocString. This is the output of
        docstring_func()

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
        the_type = _normalize_type(the_type)
        if the_type is None:
            raise ValueError("")
        # Trim parameter descriptions for incorporation into vistrails
        short_description = _truncate_description(the_description,
                                                  short_description_word_count)

        logger.debug("the_name is {0}. \n\tthe_type is {1} and it is "
                     "optional: {3}. \n\tthe_description is {2}"
                     "".format(the_name, the_type,
                               short_description,
                               is_optional))

        for port_name in (_.strip() for _ in the_name.split(',')):
            if not port_name:
                continue
            port_type = the_type
            port_is_enum = is_enum
            port_enum_list = enum_list
            # start with the easy ones
            pdict = {'name': str(port_name),
                     'label': str(short_description),
                     'optional': is_optional,
                     'signature': str(pytype_to_vtsig(param_type=port_type,
                                                  param_name=port_name))}

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
                pdict['entry_type'] = str('enum')
                pdict['values'] = [str(x) for x in port_enum_list]

            logger.debug('port_param_dict: {0}'.format(pdict))
            input_ports.append(IPort(**pdict))

    if len(input_ports) == 0:
        logger.debug('dir of input_ports[0]: {0}'.format(dir(input_ports[0])))
    return input_ports


def define_output_ports(docstring):
    """
    Turn the 'Returns' fields into VisTrails output ports

    Parameters
    ----------
    docstring : NumpyDocString #List of strings?
        The scraped docstring from the function being autowrapped into
        vistrails

    Returns
    -------
    input_ports : list
        List of input_ports (Vistrails type IPort)
    """

    output_ports = []
    # Check to make sure that there is a 'Returns' section in the docstring
    if 'Returns' not in docstring or len(docstring['Returns']) == 0:
        # If the 'Returns' section is included, but does not have any
        # parameters listed, then check the 'Parameters' section to see
        # whether the output is actually included as an optional input
        for (the_name, the_type, the_description) in docstring['Parameters']:
            # Accounts for extraneous notes or lines in doc string that are not
            # actually input or output parameters
            if the_type == '':
                continue

            if the_name.lower() == 'output':
                the_type = _normalize_type(the_type)

                output_ports.append(OPort(name=the_name,
                                          signature=pytype_to_vtsig(
                                              param_type=the_type,
                                              param_name=the_name)))
    else:
        for (the_name, the_type, the_description) in docstring['Returns']:
            if the_type == '':
                continue
            the_type = _normalize_type(the_type)

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


def wrap_function(func_name, module_path,
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
        # pprint.pprint(input_ports)
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
