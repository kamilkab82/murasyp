from collections import Set, MutableSet
from cdd import Matrix, RepType
from murasyp.massfuncs import PMFunc
from murasyp.gambles import Gamble

class CredalSet(MutableSet):
    """A mutable set of probability mass functions

      :param: a :class:`~collections.Set` of
          :class:`~murasyp.probmassfuncs.PMFunc` or a
          :class:`~collections.Set`; in the latter case, a relative vacuous
          credal set is generated.
      :type: :class:`~collections.MutableSet`

    Members behave like any :class:`set`, Moreover, they can be conditioned
    just as :class:`~murasyp.probmassfuncs.PMFunc` are and lower and
    upper expectations can be calculated, using the ``*`` and ``**`` operators,
    respectively.

    >>> p = PMFunc({'a': .03, 'b': .07, 'c': .9})
    >>> q = PMFunc({'a': .07, 'b': .03, 'c': .9})
    >>> K = CredalSet({p, q})
    >>> K
    CredalSet(set([PMFunc({'a': '7/100', 'c': '9/10', 'b': '3/100'}), PMFunc({'a': '3/100', 'c': '9/10', 'b': '7/100'})]))
    >>> f = Gamble({'a': -1, 'b': 1})
    >>> K * f
    Fraction(-1, 25)
    >>> K ** f
    Fraction(1, 25)
    >>> A = {'a','b'}
    >>> (K | A) * f
    Fraction(-2, 5)
    >>> (K | A) ** f
    Fraction(2, 5)

    """

    def __init__(self, data=set([])):
        """Create a credal set"""
        if isinstance(data, Set):
            if all(isinstance(p, PMFunc) for p in data):
                self._set = set(data)
            else:
                self._set = set(PMFunc({x}) for x in data) # vacuous
        else:
            raise TypeError("specify an event or a set "
                            + "of probability mass functions")

    __len__ = lambda self: self._set.__len__()
    __iter__ = lambda self: self._set.__iter__()
    __contains__ = lambda self: self._set.__contains__()
    __repr__ = lambda self: type(self).__name__ + '(' + repr(self._set) + ')'

    def add(self, p):
        """Add a probability mass function to the credal set

          :param: a mapping (such as a :class:`dict`) to *nonnegative* Rational
              values, i.e., :class:`~fractions.Fraction`. The fractions
              may be specified by giving an :class:`int`, a :class:`float` or in
              their :class:`str`-representation. Sum-normalization is applied.
          :type: :class:`~collections.Mapping`

        >>> K = CredalSet()
        >>> K
        CredalSet(set([]))
        >>> p = PMFunc({'a': .06, 'b': .14, 'c': 1.8, 'd': 0})
        >>> K.add(p)
        >>> K
        CredalSet(set([PMFunc({'a': '3/100', 'c': '9/10', 'b': '7/100'})]))

        """
        self._set.add(PMFunc(p))

    def discard(self, p):
        """Remove a probability mass function from the credal set

          :param: a probability mass function
          :type: :class:`~murasyp.PMFunc`

        >>> K = CredalSet({'a','b'})
        >>> K
        CredalSet(set([PMFunc({'a': 1}), PMFunc({'b': 1})]))
        >>> K.discard(PMFunc({'a'}))
        >>> K
        CredalSet(set([PMFunc({'b': 1})]))

        """
        self._set.discard(p)

    def __or__(self, other):
        """Credal set conditional on the given event"""
        if not isinstance(other, Set):
            raise TypeError(str(other) + " is not an Set")
        else:
            K = {p | other for p in self}
            if any(p == None for p in K):
                return type(self)({PMFunc({x}) for x in other})
            else:
                return type(self)(K)

    def __mul__(self, other):
        """Lower expectation of a gamble"""
        if isinstance(other, Gamble):
            if len(self) == 0:
                raise Error("Empty credal sets have no expectations")
            else:
                return min(p * other for p in self)
        else:
            raise TypeError(str(other) + " is not a gamble")

    def __pow__(self, other):
        """Upper expectation of a gamble"""
        if isinstance(other, Gamble):
            if len(self) == 0:
                raise Error("Empty credal sets have no expectations")
            else:
                return max(p * other for p in self)
        else:
            raise TypeError(str(other) + " is not a gamble")

    def pspace(self):
        """The possibility space of the credal set

        >>> p = PMFunc({'a': .03, 'b': .07})
        >>> q = PMFunc({'a': .07, 'c': .03})
        >>> K = CredalSet({p, q})
        >>> K.pspace()
        frozenset(['a', 'c', 'b'])

        """
        return frozenset.union(*(p.domain() for p in self))

    def discard_redundant(self):
        """Remove redundant elements from the credal set

        Redundant elements are those that are not vertices of the credal set's
        convex hull.

        >>> K = CredalSet(set('abc'))
        >>> K
        CredalSet(set([PMFunc({'a': 1}), PMFunc({'b': 1}), PMFunc({'c': 1})]))
        >>> K.add({'a': '1/3', 'b': '1/3', 'c': '1/3'})
        >>> K
        CredalSet(set([PMFunc({'a': 1}), PMFunc({'b': 1}), PMFunc({'c': 1}), PMFunc({'a': '1/3', 'c': '1/3', 'b': '1/3'})]))
        >>> K.discard_redundant()
        >>> K
        CredalSet(set([PMFunc({'a': 1}), PMFunc({'b': 1}), PMFunc({'c': 1})]))

        """
        pspace = list(self.pspace())
        K = list(self)
        mat = Matrix(list(list(p[x] for x in pspace) for p in K),
                     number_type='fraction')
        mat.rep_type = RepType.GENERATOR
        lin, red = mat.canonicalize()
        for i in red:
            self.discard(K[i])
