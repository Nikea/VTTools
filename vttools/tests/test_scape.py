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
                        unicode_literals)
from itertools import product
import six
import logging
logger = logging.getLogger(__name__)

from vttools import scrape


from numpy.testing import assert_string_equal, assert_equal, assert_raises
from nose.tools import assert_true

from vttools.tests.scrape_test_source import (
    eat_porridge, porridge_for_the_bears, has_defaults)


def test_scrape():
    res = scrape.scrape_function('porridge_for_the_bears', __name__)
    for k in ('input_ports', 'output_ports', 'doc_string',
              'f_type', 'func_name', 'module_path'):
        assert_true(k in res)


def test_enum():
    res = scrape.scrape_function('has_defaults', __name__)
    assert_equal(res['input_ports'][-1]['values'], has_defaults.e)


def test_obj_src():
    string_result = scrape.obj_src(eat_porridge)
    initial_txt_should_be = str(
        'def eat_porridge(this_sucks, temperature, wtf):')
    initial_txt_actual = str(string_result.split('\n')[0])
    assert_string_equal(initial_txt_actual, initial_txt_should_be)


def _optional_test_helper(tst, tar):
    assert_equal(scrape._type_optional(tst)[1], tar)


def test_type_optional():
    test_string = ('array, optional', 'array', 'array (optional)')
    targets = (True, False, True)

    for tst, tar in zip(test_string, targets):
        yield _optional_test_helper, tst, tar


def test_stacked_output_port():
    res = scrape.scrape_function('porridge_for_the_bears', __name__)
    assert_equal(3, len(res['output_ports']))


def test_enum_type():
    """
    Example function docstrings:
    1) numpy.linalg.svd()
        Parameters :
            a : (..., M, N) array_like
                A real or complex matrix of shape (M, N) .
            full_matrices : bool, optional
                If True (default), u and v have the shapes (M, M) and (N, N),
                respectively. Otherwise, the shapes are (M, K) and (K, N),
                respectively, where K = min(M, N).
            compute_uv : bool, optional
                Whether or not to compute u and v in addition to s. True by
                default.
        Returns :
            u : { (..., M, M), (..., M, K) } array
                Unitary matrices. The actual shape depends on the value of
                full_matrices. Only returned when compute_uv is True.
            s : (..., K) array
                The singular values for every matrix, sorted in descending
                order.
            v : { (..., N, N), (..., K, N) } array
                Unitary matrices. The actual shape depends on the value of
                full_matrices. Only returned when compute_uv is True.
    """
    test_str1 = '{True, False, Maybe}'
    test_str2 = 'array'
    test_str3 = '{true, FALSE, 452}'
    test_str4 = '{12.5, 5.3}'
    test_str5 = '{ (..., M, M), (..., M, K) } array'
    test_str6 = '{ (..., N, N), (..., K, N) } array'
    assert_equal(scrape._enum_type(test_str1)[1], True)
    assert_equal(scrape._enum_type(test_str1)[2], ['True', 'False',
                                                    'Maybe'])
    assert_equal(scrape._enum_type(test_str2)[1], False)
    assert_raises(ValueError, scrape._enum_type, test_str3)
    assert_raises(ValueError, scrape._enum_type, test_str4)
    assert_equal(scrape._enum_type(test_str5)[1], True)
    assert_equal(scrape._enum_type(test_str6)[1], True)


object_type_strings = ('any', 'object')

array_type_strings = ('array', 'array-like', 'array_like', 'array like',
                      'Array', 'ndarray', 'ndarray-like', '(N, ) array',
                      '(N, Maoeu, 8) array', '(,) array', '(, ) array',
                      'np.array', 'np.ndarray', '(N, M, P) array',
                      '(..., K) array',
                      '(..., M, N) array_like', '(N, M, P) ndarray',
                      '(M,) array_like', '(M) array_like', 'MxN array',
                      'array_like, shape (M, N)', 'ndarray, float', 'ndarrays',
                      '2D array', '2-D array',
                      'array_like (1-D)', 'array_like (1D or 2D)',
                      'array_like (cast to booleans)',
                      'int or [int, int] or array-like or [array, array]',
                      'array_likes')
matrix_type_strings = (tuple('{}matrix'.format(p)
                             for p in ('np.', 'numpy.', '')) +
                       ('(N, M) matrix', ))
list_type_strings = ('list', 'List', 'list-like', 'list_like',
                     'list like', 'listlike')


tuple_type_strings = ('tuple'),
seq_type_strings = ('sequence', '1D sequence', '1-D sequence')
dtype_type_strings = ('dtype', 'dtype like', 'np.dtype', 'numpy.dtype',
                      'data-type', 'data type', 'data type code',
                      'dtype specifier',
                      'numpy dtype')
bool_type_strings = ('bool', 'boolean')
file_type_strings = ('file', 'filename', 'file handle',
                     'file object', 'file handle object')
scalar_type_strings = ('scalar', 'number')

float_type_strings = (tuple('{}float{}'.format(prefix, n)
                            for prefix, n in product(('np.', 'numpy.', ''),
                                                     (16, 32, 64, 128)))
                            + ('double', 'single', 'float', 'float (only if)'))

# known fails 'int (cast to 0 or 1)',
int_type_strings = (('integer', 'InTeGeR',) +
                            tuple('{}{}int{}'.format(prefix, u, n)
                                  for prefix, u, n
                                  in product(('np.', 'numpy.', ''),
                                             ('u', ''),
                                             (8, 16, 32, 64))))

complex_type_strings = ('complex', )
dict_type_strings = ('dict', 'dictionary')
str_type_strings = ('str', 'string', 'str-like')
callable_type_strings = ('function', 'func', 'callable',
                         'callable f(x,*args)', 'function(x) -> f')


def test_normalize_simple():

    # Example function docstrings:
    # 1)  numpy.outer()
    #    Parameters :
    #     a : (M,) array_like
    #         First input vector. Input is flattened if not already
    #         1-dimensional.
    #     b : (N,) array_like
    #         Second input vector. Input is flattened if not already
    #         1-dimensional.
    #     Returns :
    #     out : (M, N) ndarray
    # 2) numpy.linalg.svd()
    #     Parameters :
    #         a : (..., M, N) array_like
    #             A real or complex matrix of shape (M, N) .
    #         full_matrices : bool, optional
    #             If True (default), u and v have the shapes (M, M) and (N, N),
    #             respectively. Otherwise, the shapes are (M, K) and (K, N),
    #             respectively, where K = min(M, N).
    #         compute_uv : bool, optional
    #             Whether or not to compute u and v in addition to s. True by
    #             default.
    #     Returns :
    #         u : { (..., M, M), (..., M, K) } array
    #             Unitary matrices. The actual shape depends on the value of
    #             full_matrices. Only returned when compute_uv is True.
    #         s : (..., K) array
    #             The singular values for every matrix, sorted in descending
    #             order.
    #         v : { (..., N, N), (..., K, N) } array
    #             Unitary matrices. The actual shape depends on the value of
    #             full_matrices. Only returned when compute_uv is True.
    test_dict = {
                 'object': object_type_strings,
                 'array': array_type_strings,
                 'matrix': matrix_type_strings,
                 'list': list_type_strings,
                 'tuple': tuple_type_strings,
                 'seq': seq_type_strings,
                 'dtype': dtype_type_strings,
                 'bool': bool_type_strings,
                 'file': file_type_strings,
                 'scalar': scalar_type_strings,
                 'float': float_type_strings,
                 'int': int_type_strings,
                 'complex': complex_type_strings,
                 'dict': dict_type_strings,
                 'str': str_type_strings,
                 'callable': callable_type_strings,
                 }

    # make sure we test everything!
    test_keys = set(six.iterkeys(test_dict))
    sig_keys = set(six.iterkeys(scrape.sig_map))
    assert_equal(test_keys, sig_keys)
    for k, v in six.iteritems(test_dict):
        for ts in v:
            yield _normalize_test_helper, ts, k


def _normalize_test_helper(tst, targ):
    assert_equal(scrape._normalize_type(tst), targ)


def test_check_alt_types():
    test_strings = ('float or int',
                    'scalar or tuple of scalars',
                    'int or scalar',
                    'scalar or sequence of scalars',
                    'MxN ndarray',
                    'integer value',
                    'aardvark',
                    'aardvark of doom',
                    'list or aardavrk',
                    'aardvark or integer'
                    )

    targets = ('float',
    'tuple',
    'scalar',
    'seq',
    'array',
    'int',
    None,
    None,
    'list',
    'int')

    for ts, tar in zip(test_strings, targets):
        yield _normalize_test_helper, ts, tar,


def test_truncate_description():
    original_description1 = ['length of three']
    original_description2 = ['This object is the original description '
                           'stripped from the doc string. The object is ',
                           'actually a list of strings.']
    word_count = 6
    # Test to make sure descriptions that are smaller than the
    # specified word count pass through correctly
    assert_equal(scrape._truncate_description(original_description1,
                                                word_count),
                 'length of three')
    # Test that function descriptions less than word_count are cropped and
    # passed through correctly
    assert_equal(scrape._truncate_description(original_description2,
                                                word_count),
                 'This object is the original description')


def _func_helper(func, test_string, expected_string):
    assert_equal(func(test_string), expected_string)


def test_guess_type():
    """
    The function _guess_type() is used in the function _enum_type(). The
    initial input is the stripped type string.
    e.g. {14, 0.333, 5j, True, False, Maybe}
    The input string is then checked to make sure that there are enclosing
    curly braces, after which the enum string is separated out using the
    commas, any string declarations are then removed (i.e. ' or "), and each
    element of the original enum string is converted to an element of a list
    of strings. Each of these separated elements are then entered into the
    _guess_type() function.

    All of these test strings are parameter types that should be caught and
    evaluated using the _guess_type() function.
    """
    test_strting = ('0.333', '14', '5j', 'Volume')
    target_strings = ('float', 'int', 'complex', 'str')

    for tst, tar in zip(test_strting, target_strings):
        yield _func_helper, scrape._guess_enum_val_type, tst, tar


def test_dicts_match():
    RE_keys = set(six.iterkeys(scrape._RE_DICT))
    sig_keys = set(six.iterkeys(scrape.sig_map))

    p_keys = set(scrape.precedence_list)

    assert_equal(RE_keys, sig_keys)
    assert_equal(RE_keys, p_keys)


def _default_tester_helper(func, expect_dict):
    res = scrape._extract_default_vals(func)
    assert_equal(res, expect_dict)


def test_default():
    test_data = ((eat_porridge, {}),
                 (has_defaults, {'a': None, 'b': 1,
                                 'c': 'str', 'd': (),
                                 'e': None}))

    for func, res in test_data:
        yield _default_tester_helper, func, res


def test_module_scrape():

    tests = (({}, {'black_list': ['has_defaults']}, ['has_defaults']),
             ({}, {'exclude_markers': ['porridge']},
              ['eat_porridge', 'porridge_for_the_bears']),
             ({'exclude_private': False}, {}, ['_private']))

    for pre, post, tst_lst in tests:
        yield (_mod_scrape_test_helper,
               'vttools.tests.scrape_test_source',
               pre, post, tst_lst)


def _mod_scrape_test_helper(mod_name, kwargs_with, kwargs_without,
                            test_members):
    res = scrape.scrape_module(mod_name, **kwargs_with)

    for n in test_members:
        assert_true(n in res)

    res = scrape.scrape_module(mod_name, **kwargs_without)
    for n in test_members:
        assert_true(n not in res)
