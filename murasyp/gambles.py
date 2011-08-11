from collections import Hashable
from itertools import repeat
from murasyp import _make_rational, RatValFunc
from murasyp.events import Event

class Gamble(RatValFunc, Hashable):
    """Gambles are immutable, hashable rational-valued functions

      :param: a mapping (such as a :class:`dict`) to Rational values,
          i.e., :class:`~numbers.Rational`, which includes the built-in type
          :class:`int`, but also :class:`~fractions.Fraction`. The fractions
          may be given as a :class:`float` or in their
          :class:`str`-representation.
      :type: :class:`~collections.Mapping`

    This class derives from :class:`~murasyp.RatValFunc`, so its methods
    apply here as well. This class's members are also hashable, which means
    they can be used as keys (in :class:`~collections.Set` and
    :class:`~collections.Mapping`, and their built-in variants :class:`set`
    and :class:`dict`). What has changed:

    * pointwise multiplication and scalar addition & subtraction
      has been added;
    * how domains are combined under pointwise operations;
    * unspecified values are assumed to be zero.

    >>> f = Gamble({'a': 1.1, 'b': '-1/2','c': 0})
    >>> f['d']
    0
    >>> f
    Gamble({'a': Fraction(11, 10), 'c': Fraction(0, 1), 'b': Fraction(-1, 2)})
    >>> g = Gamble({'b': '.6', 'c': -2, 'd': 0.0})
    >>> g
    Gamble({'c': Fraction(-2, 1), 'b': Fraction(3, 5), 'd': Fraction(0, 1)})
    >>> (.3 * f - g) / 2
    Gamble({'a': Fraction(33, 200), 'c': Fraction(1, 1), 'b': Fraction(-3, 8), 'd': Fraction(0, 1)})
    >>> f * g
    Gamble({'a': Fraction(0, 1), 'c': Fraction(0, 1), 'b': Fraction(-3, 10), 'd': Fraction(0, 1)})
    >>> -3 - f
    Gamble({'a': Fraction(-41, 10), 'c': Fraction(-3, 1), 'b': Fraction(-5, 2)})

    .. note::

      Notice that the domain of results of sums and differences is the
      union of the respective domains.

    Furthermore, gambles can be combined with events:

    * for restriction and extension of their domain;
    * for cylindrical extension to a cartesian-product domain.

    >>> f = Gamble({'a': 1.1, 'b': '-1/2','c': 0})
    >>> f | Event({'a', 'b'})
    Gamble({'a': Fraction(11, 10), 'b': Fraction(-1, 2)})
    >>> f | Event({'a', 'd'})
    Gamble({'a': Fraction(11, 10), 'd': Fraction(0, 1)})
    >>> f ^ Event({'e', 'f'})
    Gamble({('c', 'f'): Fraction(0, 1), ('a', 'f'): Fraction(11, 10), ('a', 'e'): Fraction(11, 10), ('b', 'f'): Fraction(-1, 2), ('b', 'e'): Fraction(-1, 2), ('c', 'e'): Fraction(0, 1)})

    Additionally, gambles' properties and related gambles are computed by
    calling the appropriate methods. Their possibility spaces coincide with
    their domain.

    """

    def __init__(self, data):
        """Create a gamble"""
        if isinstance(data, Event):
            data = dict(zip(data, repeat(1)))
        RatValFunc.__init__(self, data)

    __getitem__ = lambda self, x: self._mapping[x] if x in self else 0
    __hash__ = lambda self: hash(self._mapping)

    def pspace(self):
        """The gamble's possibility space

          :returns: the gamble's possibility space
          :rtype: :class:`frozenset`

        >>> h = Gamble({'a': 1, 'b': 3, 'c': 4})
        >>> h.pspace()
        frozenset(['a', 'c', 'b'])

        """
        return self.domain()

    def __add__(self, other):
        """Also allow addition of rational-valued functions and scalars"""
        if isinstance(other, Gamble):
            return RatValFunc.__add__(self, other)
        else:
            other = _make_rational(other)
            return type(self)(dict((arg, value + other) for arg, value
                                                        in self.items()))

    __radd__ = __add__
    __rsub__ = lambda self, other: -(self - other)

    def __mul__(self, other):
        """Pointwise multiplication of rational-valued functions"""
        if isinstance(other, Gamble):
            return type(self)(dict((x, self[x] * other[x])
                                   for x in self._domain_joiner(other)))
        else:
            return RatValFunc.__mul__(self, other)

    def _domain_joiner(self, other):
        if type(self) == type(other):
            return iter(self.domain() | other.domain())
        else:
            raise TypeError("cannot combine domains of objects with different"
                            "types: '" + type(self).__name__ + "' and '"
                                       + type(other).__name__ + "'")

    def __or__(self, other):
        """Restriction or extension with zero"""
        if isinstance(other, Event):
            return type(self)(dict((x, self[x]) for x in other))
        else:
            raise("the argument must be an Event")

    def __xor__(self, other):
        """Cylindrical extension"""
        if isinstance(other, Event):
            return type(self)(dict(((x, y), self[x])
                                   for x in self for y in other))
        else:
            raise TypeError("the argument must be an Event")

    def bounds(self):
        """The minimum and maximum values of the gamble

          :returns: the minimum and maximum values of the gamble
          :rtype: a pair (:class:`tuple`) of :class:`~numbers.Rational`

        >>> h = Gamble({'a': 1, 'b': 3, 'c': 4})
        >>> h.bounds()
        (Fraction(1, 1), Fraction(4, 1))

        """
        values = self.range()
        return (min(values), max(values))

    def scaled_shifted(self):
        """Shifted and scaled version of the gamble

          :returns: a scaled and shifted version
                    :math:`(f-\min f)/(\max f-\min f)` of the gamble :math:`f`
          :rtype: :class:`~murasyp.Gamble`

        >>> h = Gamble({'a': 1, 'b': 3, 'c': 4})
        >>> h.scaled_shifted()
        Gamble({'a': Fraction(0, 1), 'c': Fraction(1, 1), 'b': Fraction(2, 3)})

        .. note::

          The zero gamble is returned in case the gamble is constant.

        """
        minval, maxval = self.bounds()
        shift = minval
        scale = maxval - minval
        return (self - shift) if scale == 0 else (self - shift) / scale

    def norm(self):
        """The max-norm of the gamble

          :returns: the max-norm
                    :math:`\|f\|_\infty=\max_{x\in\mathcal{X}}|f(x)|` of the
                    gamble :math:`f`
          :rtype: :class:`~numbers.Rational`

        >>> h = Gamble({'a': 1, 'b': 3, 'c': 4})
        >>> h.norm()
        Fraction(4, 1)

        """
        minval, maxval = self.bounds()
        return max(-minval, maxval)

    def normalized(self):
        """Max-norm normalized version of the gamble

          :returns: a normalized version :math:`f/\|f\|_\infty` of the gamble
                    :math:`f`
          :rtype: :class:`~murasyp.Gamble`

        >>> h = Gamble({'a': 1, 'b': 3, 'c': 4})
        >>> h.normalized()
        Gamble({'a': Fraction(1, 4), 'c': Fraction(1, 1), 'b': Fraction(3, 4)})

        .. note::

          The gamble itself is returned in case it is identically zero.

        """
        norm = self.norm()
        return self if norm == 0 else self / norm
