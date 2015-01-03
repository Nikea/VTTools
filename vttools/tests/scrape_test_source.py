"""
Module for testing the scraping infrastructurescrapin
"""


# Demo enum test function
def eat_porridge(this_sucks, temperature, wtf):
    """
    Should we eat the porridge?

    Parameters
    ----------
    temperature, porridge : {'too hot', 'too cold', 'just right'}
        The temperature of the porridge

    output : bool
        If we should eat the porridge
    """
    if temperature not in {'too hot', 'too cold', 'just right'}:
        raise ValueError("That isn't porridge!")
    return temperature == 'just right'


def porridge_for_the_bears(were_you_robbed):
    """
    Did Goldie Locks break in and rob you?

    Parameters
    ----------
    were_you_robbed : bool
        The question is in the title

    Returns
    -------
    p_bear_emo, m_bear_emo, b_bear_emo : string
        The emotional status of the three bears
    """
    if were_you_robbed:
        p_bear_emo = 'angry'
        m_bear_emo, b_bear_emo = 'sad', 'sad'
    else:
        p_bear_emo, m_bear_emo, b_bear_emo = 'angry', 'happy', 'happy'
    return p_bear_emo, m_bear_emo, b_bear_emo


def has_defaults(a=None, b=1, c='str', d=(),
                 e=None):
    """
    A silly no-op function

    Parameters
    ----------
    a : object, optional
        defaults to None
    b : int, optional
        defaults to 1
    c : str, optional
        Defaults to 'str'
    d : tuple, optional
        Defaults to ()
    e : {'a', 'b', 'c'}
        An enum
    """
    pass
has_defaults.e = ['a', 'b', 'c']


def _private():
    pass


class DontWrapMe(object):
    pass
