#################################################################################
#
# (c) Copyright 2011 William Stein
#
#  This file is part of PSAGE.
#
#  PSAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
# 
#  PSAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

r"""


"""

import math, os, sys

from sage.all import (
    arrow,
    bar_chart,
    cached_function, cached_method,
    CDF,
    ceil,
    divisors,
    e,
    Ei,
    ellipsis_range as erange,
    exp,
    factor,
    fast_callable,
    finance,
    floor,
    gcd,
    Graphics,
    graphics_array,
    is_prime, is_prime_power, is_pseudoprime, nth_prime,
    latex,
    Li,
    line,
    log, sin, cos,
    maxima,
    moebius,
    parallel,
    pi,
    plot,
    point,
    points,
    polygon,
    prime_divisors,
    prime_range,
    prime_pi,
    prime_powers,
    primes,
    prod,
    randint,
    random,
    save,
    set_random_seed,
    spline,
    sqrt,
    SR,
    text,
    var,
    walltime,
    zeta,
    zeta_zeros,
    ZZ
    )

TimeSeries = finance.TimeSeries


##############################################################
# Drawing figures (one or all)
##############################################################

def draw(fig=None, dir='illustrations/',ext='pdf', in_parallel=True):
    if not os.path.exists(dir):
        os.makedirs(dir)
        
    if isinstance(fig, str):
        print "Drawing %s... "%fig,
        sys.stdout.flush()
        t = walltime()
        G = eval('fig_%s(dir,ext)'%fig)
        print " (time = %s seconds)"%walltime(t)
        return G
    
    if fig is None:
        figs = ['_'.join(x.split('_')[1:]) for x in globals() if x.startswith('fig_')]
    elif isinstance(fig, list):
        figs = fig
    if in_parallel:
        @parallel
        def f(x):
            return draw(x, dir=dir, ext=ext, in_parallel=False)
        for x in f(figs):
            print x
    else:
        for fig in figs:
            draw(fig)
    return

##############################################################
# Factorization trees
##############################################################
def fig_factor_tree(dir, ext):
    g = FactorTree(6).plot(labels={'fontsize':60},sort=True)
    g.save(dir + '/factor_tree_6.%s'%ext, axes=False, axes_pad=0.1)
    
    g = FactorTree(12).plot(labels={'fontsize':50},sort=True)
    g.save(dir + '/factor_tree_12.%s'%ext, axes=False, axes_pad=0.1)
    
    set_random_seed(3)    
    g = FactorTree(12).plot(labels={'fontsize':50},sort=False)
    g.save(dir + '/factor_tree_12b.%s'%ext, axes=False,axes_pad=0.1)

    set_random_seed(0)
    for w in ['a', 'b']:
        g = FactorTree(300).plot(labels={'fontsize':40},sort=False)
        g.save(dir + '/factor_tree_300_%s.%s'%(w,ext), axes=False, axes_pad=0.1)

    set_random_seed(0)
    g = FactorTree(6469693230).plot(labels={'fontsize':14},sort=False)
    g.save(dir + '/factor_tree_big.%s'%ext, axes=False, axes_pad=0.1)
    

class FactorTree:
    """
    A factorization tree.

    EXAMPLES::
    
        sage: FactorTree(100)
        Factorization trees of 100
        sage: R.<x> = QQ[]
        sage: FactorTree(x^3-1)
        Factorization trees of x^3 - 1
    """
    def __init__(self, n):
        """
        INPUT:

            - `n` -- number of element of polynomial ring
        """
        self.__n = n

    def value(self):
        """
        Return the n such that self is FactorTree(n).

        EXAMPLES::

            sage: FactorTree(100).value()
            100
        """
        return self.__n

    def __repr__(self):
        """
        EXAMPLES::
        
            sage: FactorTree(100).__repr__()
            'Factorization trees of 100'
        """
        return "Factorization trees of %s"%self.__n

    def plot(self, lines=None, labels=None, sort=False):
        """
        INPUT:

            - ``lines`` -- optional dictionary of options passed
              to the line command

            - ``labels`` -- optional dictionary of options passed to
              the text command for the divisor labels

            - ``sort`` -- bool (default: False); if True, the primes
              divisors are found in order from smallest to largest;
              otherwise, the factor tree is draw at random

        EXAMPLES::

            sage: FactorTree(2009).plot(labels={'fontsize':30},sort=True)

        We can make factor trees of polynomials in addition to integers::
        
            sage: R.<x> = QQ[]
            sage: F = FactorTree((x^2-1)*(x^3+2)*(x-5)); F
            Factorization trees of x^6 - 5*x^5 - x^4 + 7*x^3 - 10*x^2 - 2*x + 10
            sage: F.plot(labels={'fontsize':15},sort=True)
        """
        if lines is None:
            lines = {'rgbcolor':(.5,.5,1)}
        if labels is None:
            labels = {'fontsize':16}
        n = self.__n
        rows = []
        v = [(n,None,0)]
        self._ftree(rows, v, sort=sort)
        return self._plot_ftree(rows, lines, labels)

    def _ftree(self, rows, v, sort):
        """
        A function that is used recurssively internally by the plot function.

        INPUT:

            - ``rows`` -- list of lists of integers

            - ``v`` -- list of triples of integers

            - ``sort`` -- bool (default: False); if True, the primes
              divisors are found in order from smallest to largest;
              otherwise, the factor tree is draw at random

        EXAMPLES::

            sage: F = FactorTree(100)
            sage: rows = []; v = [(100,None,0)]; F._ftree(rows, v, True)
            sage: rows
            [[(100, None, 0)],
             [(2, 100, 0), (50, 100, 0)],
             [(None, None, None), (2, 50, 1), (25, 50, 1)],
             [(None, None, None), (None, None, None), (5, 25, 2), (5, 25, 2)]]
            sage: v
            [(100, None, 0)]
        """
        if len(v) > 0:
            # add a row to g at the ith level. 
            rows.append(v)
        w = []
        for i in range(len(v)):
            k, _,_ = v[i]
            if k is None or ZZ(k).is_irreducible():
                w.append((None,None,None))
            else:
                div = divisors(k)
                if sort:
                    d = div[1]
                else:
                    z = divisors(k)[1:-1]
                    d = z[randint(0,len(z)-1)]
                w.append((d,k,i))
                e = k//d
                if e == 1:
                    w.append((None,None))
                else:
                    w.append((e,k,i))
        if len(w) > len(v):
            self._ftree(rows, w, sort=sort)

    def _plot_ftree(self, rows, lines, labels):
        """
        Used internally by the plot method.

        INPUT:

            - ``rows`` -- list of lists of triples

            - ``lines`` -- dictionary of options to pass to lines commands

            - ``labels`` -- dictionary of options to pass to text command to label factors

        EXAMPLES::

            sage: F = FactorTree(100)
            sage: rows = []; v = [(100,None,0)]; F._ftree(rows, v, True)
            sage: F._plot_ftree(rows, {}, {})
        """
        g = Graphics()
        for i in range(len(rows)):
            cur = rows[i]
            for j in range(len(cur)):
                e, f, k = cur[j]
                if not e is None:
                    if ZZ(e).is_irreducible():
                         c = (1,0,0)
                    else:
                         c = (0,0,.4)
                    g += text("$%s$"%latex(e), (j*2-len(cur),-i), rgbcolor=c, **labels)
                    if not k is None and not f is None:
                        g += line([(j*2-len(cur),-i), (k*2-len(rows[i-1]),-i+1)], axes=False, **lines) 
        return g


##############################################################
# Bag of primes
##############################################################        

def bag_of_primes(steps):
    """
    This works up to 9.  It took a day using specialized factoring
    (via GMP-ECM) to get step 10.

    EXAMPLES::
    
        sage: bag_of_primes(5)
        [2, 3, 7, 43, 13, 139, 3263443]
    """
    bag = [2]
    for i in range(steps):
        for p in prime_divisors(prod(bag)+1):
            bag.append(p)
    print bag


##############################################################
# Questions about numbers
##############################################################
def fig_questions(dir, ext):
    g = questions(100,17,20)
    g.save(dir + '/questions.%s'%ext, axes=False)

def questions(n=100,k=17,fs=20):
    set_random_seed(k)
    g = text("?",(5,5),rgbcolor='grey', fontsize=200)
    g += sum(text("$%s$"%p,(random()*10,random()*10),rgbcolor=(p/(2*n),p/(2*n),p/(2*n)),fontsize=fs) 
             for p in primes(n))
    return g


##############################################################
# Sieve of Eratosthenes
##############################################################        

def fig_erat(dir,ext):
    # sieving out 2,3,5,7
    for p in [2,3,5,7]:
        sieve_step(p,100).save(dir+'/sieve100-%s.%s'%(p,ext))

    sieve_step(13,200).save(dir+'/sieve200.%s'%ext)
        
        
def number_grid(c, box_args=None, font_args=None, offset=0):
    """
    INPUT:  
        c -- list of length n^2, where n is an integer.
             The entries of c are RGB colors.
        box_args -- additional arguments passed to box.
        font_args -- all additional arguments are passed
                to the text function, e.g., fontsize.
        offset -- use to fine tune text placement in the squares
        
    OUTPUT:
        Graphics -- a plot of a grid that illustrates 
             those n^2 numbers colored according to c.
    """
    if box_args is None: box_args = {}
    if font_args is None: font_args = {}
    
    try:
        n = sqrt(ZZ(len(c)))
    except ArithmeticError:
        raise ArithmeticError, "c must have square length"
    G = Graphics()
    k = 0
    for j in reversed(range(n)):
        for i in range(n):
            col = c[int(k)]
            R = line([(i,j),(i+1,j),(i+1,j+1),(i,j+1),(i,j)],
                     thickness=.2, **box_args)
            d = dict(box_args)
            if 'rgbcolor' in d.keys():
                del d['rgbcolor']
            P = polygon([(i,j),(i+1,j),(i+1,j+1),(i,j+1),(i,j)],
                        rgbcolor=col, **d)
            G += P + R
            if col != (1,1,1):
                G += text(str(k+1), (i+.5+offset,j+.5), **font_args)
            k += 1
    G.axes(False)
    G.xmin(0); G.xmax(n); G.ymin(0); G.ymax(n)
    return G

def sieve_step(p, n, gone=(1,1,1), prime=(1,0,0), \
               multiple=(.6,.6,.6), remaining=(.9,.9,.9), 
               fontsize=11,offset=0):
    """
    Return graphics that illustrates sieving out multiples of p.
    Numbers that are a nontrivial multiple of primes < p are shown in
    the gone color.  Numbers that are a multiple of p are shown in a
    different color.  The number p is shown in yet a third color.
  
    INPUT:
        p -- a prime (or 1, in which case all points are colored "remaining")
        n -- a SQUARE integer
        gone -- rgb color for integers that have been sieved out
        prime -- rgb color for p
        multiple -- rgb color for multiples of p
        remaining -- rgb color for integers that have not been sieved out yet
                     and are not multiples of p.
    """
    if p == 1:
        c = [remaining]*n
    else:
        exclude = prod(prime_range(p))  # exclude multiples of primes < p
        c = []
        for k in range(1,n+1):
            if k <= p and is_prime(k):
                c.append(prime)
            elif k == 1 or (gcd(k,exclude) != 1 and not is_prime(k)):
                c.append(gone)
            elif k%p == 0:
                c.append(multiple)
            else:
                c.append(remaining) 
        # end for
    # end if
    return number_grid(c,{'rgbcolor':(0.2,0.2,0.2)},{'fontsize':fontsize, 'rgbcolor':(0,0,0)},offset=offset)


##############################################################
# Similar rates of growth
##############################################################        

def fig_simrates(dir,ext):
    # similar rates 
    G = similar_rates()
    G.save(dir + "/similar_rates.%s"%ext,figsize=[8,3])

def similar_rates():
    """
    Draw figure fig:simrates illustrating similar rates.

    EXAMPLES::

        sage: similar_rates()
    """
    X = var('X')
    A = 2*X**2 + 3*X - 5
    B = 3*X**2 - 2*X + 1
    G = plot(A/B, (1,100))
    G += text("$A(X)/B(X)$", (70,.58), rgbcolor='black', fontsize=14)
    H = plot(A, (X,1,100), rgbcolor='red') + plot(B, (X,1,100))
    H += text("$A(X)$", (85,8000), rgbcolor='black',fontsize=14)
    H += text("$B(X)$", (60,18000), rgbcolor='black',fontsize=14)    
    a = graphics_array([[H,G]]) 
    return a

def same_rates():
    """
    Draw figure fig:samerates illustrating same rates.

    EXAMPLES::

        sage: similar_rates()
    """
    X = var('X')
    A = X**2 + 3*X - 5
    B = X**2 - 2*X + 1
    G = plot(A/B, (1,100))
    G += text("$A(X)/B(X)$", (70,.58), rgbcolor='black', fontsize=14)
    H = plot(A, (X,1,100), rgbcolor='red') + plot(B, (X,1,100))
    H += text("$A(X)$", (70,8500), rgbcolor='black',fontsize=14)
    H += text("$B(X)$", (90,5000), rgbcolor='black',fontsize=14)    
    a = graphics_array([[H,G]]) 
    return a

def fig_same_rates(dir,ext):
    # similar rates 
    G = same_rates()
    G.save(dir + "/same_rates.%s"%ext,figsize=[8,3])


##############################################################
# Proportion of Primes to to X
##############################################################

def fig_log(dir, ext):
    g = plot(log, 1/3.0, 100, thickness=2)
    g.save(dir + '/log.%s'%ext, figsize=[8,3], gridlines=True)

def fig_proportion_primes(dir,ext):
    for bound in [100,1000,10000]:
        g = proportion_of_primes(bound)
        g.save(dir + '/proportion_primes_%s.%s'%(bound,ext))

def plot_step_function(v, vertical_lines=True, **args):
    r"""
    Return the line that gives the plot of the step function f defined
    by the list v of pairs (a,b).  Here if (a,b) is in v, then f(a) = b.

    INPUT:

        - `v` -- list of pairs (a,b)

    EXAMPLES::

        sage: plot_step_function([(i,sin(i)) for i in range(5,20)])
    """
    # make sorted copy of v (don't change in place, since that would be rude).
    v = list(sorted(v))
    if len(v) <= 1:
        return line([]) # empty line
    if vertical_lines:
        w = []
        for i in range(len(v)):
            w.append(v[i])
            if i+1 < len(v):
                w.append((v[i+1][0],v[i][1]))
        return line(w, **args)
    else:
        return sum(line([v[i],(v[i+1][0],v[i][1])], **args) for i in range(len(v)-1))
        

def proportion_of_primes(bound, **args):
    """
    Return a graph of the step function that assigns to X the
    proportion of numbers between 1 and X of primes.

    INPUTS:
    
        - `bound` -- positive integer

        - additional arguments are passed to the line function.

    EXAMPLES::

        sage: proportion_of_primes(100)
    """
    v = []
    k = 0.0
    for n in range(1,bound+1):
        if is_prime(n):
            k += 1
        v.append((n,k/n))
    return plot_step_function(v, **args)


##############################################################
# Prime Gaps
##############################################################        

@cached_function
def prime_gaps(maxp):
    """
    Return the sequence of prime gaps obtained using primes up to maxp.
    
    EXAMPLES::
    
        sage: prime_gaps(100)
        [1, 2, 2, 4, 2, 4, 2, 4, 6, 2, 6, 4, 2, 4, 6, 6, 2, 6, 4, 2, 6, 4, 6, 8]        
    """
    P = prime_range(maxp+1)
    return [P[i+1] - P[i] for i in range(len(P)-1)]

@cached_function
def prime_gap_distribution(maxp):
    """
    Return list v such that v[i] is how many times i is a prime gap
    among the primes up to maxp.

    EXAMPLES::
    
        sage: prime_gap_distribution(100)
        [0, 1, 8, 0, 7, 0, 7, 0, 1]
        sage: prime_gap_distribution(1000)
        [0, 1, 35, 0, 40, 0, 44, 0, 15, 0, 16, 0, 7, 0, 7, 0, 0, 0, 1, 0, 1]
    """
    h = prime_gaps(maxp)
    v = [0]*(max(h)+1)
    for gap in h: v[gap] += 1
    return v    

def fig_primegapdist(dir,ext):
    v = prime_gap_distribution(10**7)[:50]
    bar_chart(v).save(dir+"/primegapdist.%s"%ext, figsize=[9,3])


def prime_gap_plots(maxp, gap_sizes):
    """
    Return a list of graphs of the functions Gap_k(X) for 0<=X<=maxp,
    for each k in gap_sizes.  The graphs are lists of pairs (X,Y) of
    integers.

    INPUT:
        - maxp -- positive integer
        - gap_sizes -- list of integers 
    """
    P = prime_range(maxp+1)
    v = [[(0,0)] for i in gap_sizes]
    k = dict([(g,i) for i, g in enumerate(gap_sizes)])
    for i in range(len(P)-1):
        g = P[i+1] - P[i]
        if g in k:
            w = v[k[g]]
            w.append( (P[i+1],w[-1][1]) )
            w.append( (P[i+1],w[-1][1]+1) )
    return v


def fig_primegap_race(dir, ext):
    """
    Draw plots showing the race for gaps of size 2, 4, 6, and 8.
    """
    X = 7000
    gap_sizes = [2,4,6,8]
    #X = 100000
    #gap_sizes = [i for i in range(2,50) if i%2==0]
    v = prime_gap_plots(X, gap_sizes)

    P = sum(line(x) for x in v)
    P += sum( text( "Gap %s"%gap_sizes[i], (v[i][-1][0]*1.04, v[i][-1][1]), color='black', fontsize=8)
              for i in range(len(v)))

    P.save(dir + '/primegap_race.%s'%ext, figsize=[9,3], gridlines=True)
    return P



##############################################################
# Multiplicatively even and odd table
##############################################################
def mult_even_odd_count(bound):
    """
    Return list v of length bound such that v[n] is a pair (a,b) where
    a is the number of multiplicatively even positive numbers <= n and b is the
    number of multiplicatively odd positive numbers <= n.

    INPUT:
    
        - ``bound`` -- a positive integer

    EXAMPLES::

    We make the table in the paper::

        sage: mult_even_odd_count(17)
        [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4), (3, 5), (4, 5), (5, 5), (5, 6), (5, 7), (5, 8), (6, 8), (7, 8), (8, 8)]
    """
    par = mult_parities(bound)
    a = 0; b = 0
    v = [(a,b)]
    for n in range(1,bound):
        if par[n] == 0:  # mult even
            a += 1
        else:
            b += 1
        v.append((a,b))
    return v

def fig_multpar(dir,ext):
    for n in [10**k for k in reversed([1,2,3,4,5,6])]:
        file = dir + '/liouville-%s.%s'%(n,ext)
        if n >= 1000:
            time_series = True
        else:
            time_series = False
        g = race_mult_parity(n, time_series=time_series)
        g.save(file, frame=True)

def race_mult_parity(bound, time_series=False, **kwds):
    """
    Return a plot that shows race between multiplicatively even and
    odd numbers.  More precisely it shows the function f(X) that
    equals number of even numbers >= 2 and <=X minus the number of odd
    numbers >= 2 and <= X.

    EXAMPLES::

        sage: race_mult_parity(10^5,time_series=True)
        sage: race_mult_parity(10^5)
    """
    par = mult_parities(bound)[2:]
    if not time_series:
        v = [(2,0)]
        for n in range(bound-2):
            if par[n] == 0:
                b = v[-1][1]+1
            else:
                b = v[-1][1]-1
            v.append((v[-1][0], b))
            v.append((v[-1][0]+1, b))
        return line(v, **kwds)
    else:
        v = [0,0,0]
        for n in range(bound-2):
            if par[n] == 0:
                v.append(v[-1]+1)
            else:
                v.append(v[-1]-1)
        return TimeSeries(v).plot()


def mult_parities_python(bound, verbose=False):
    """
    Return list v of length bound such that v[n] is 0 if n is
    multiplicative even, and v[n] is 1 if n is multiplicatively odd.
    Also v[0] is None.

    This goes up to bound=`10^7` in about 30 seconds.
    """
    v = [None]*bound
    v[0] = None
    v[1] = int(0)
    P = [int(p) for p in prime_range(bound)]
    for p in P:
        v[p] = int(1)
    last = P
    last_parity = int(1)
    loops = floor(log(bound,2))+1
    bound = int(bound)
    for k in range(loops):
        cur = []
        cur_parity = (last_parity+int(1))%int(2)
        if verbose:
            print "loop %s (of %s);  last = %s"%(k,loops, len(last))
        for n in last:
            for p in P:
                m = n * p
                if m >= bound:
                    break
                if v[m] is None:
                    v[m] = cur_parity
                    cur.append(m)
        last_parity = cur_parity
        last = cur
    return v

##############################################################
# LogX over X in "Probabilistic first guess" chapter
##############################################################
def fig_logXoverX(dir, ext):
    file = dir + '/logXoverX.%s'%ext
    x = var('x')
    xmax = 250
    G = plot(x/(log(x)-1), 4, xmax, color='blue')
    G += prime_pi.plot(4, xmax, color='red')
    G.save(file, figsize=[7,3])

##############################################################
# The devil is in the details.
##############################################################

def committee_pi(X, error_prob=0.1):
    num_primes = 0
    for N in range(1, X+1):
        N_is_prime = is_pseudoprime(N)
        if random() < error_prob:
            # make a mistake
            if not N_is_prime:
                # incorrectly count it
                num_primes += 1
        else:
            # do not make a mistake
            if N_is_prime:
                num_primes += 1
    return num_primes
            
            
    


##############################################################
# Prime pi plots
##############################################################

def fig_prime_pi_aspect1(dir,ext):
    for n in [25, 100]:
        p = plot(lambda x: prime_pi(floor(x)), 1,n,
                 plot_points=10000,rgbcolor='red',
                 fillcolor=(.9,.9,.9),fill=True)
        file = dir + '/prime_pi_%s_aspect1.%s'%(n,ext)
        p.save(file, aspect_ratio=1, gridlines=True)
        
def fig_prime_pi(dir,ext):
    for n in [1000, 10000, 100000]:
        p = plot(lambda x: prime_pi(floor(x)), 1,n,
                 plot_points=10000,rgbcolor='red',
                 fillcolor=(.9,.9,.9),fill=True)
        file = dir + '/prime_pi_%s.%s'%(n,ext)
        p.save(file)

def fig_prime_pi_nofill(dir,ext):
    for n in [25,38,100,1000,10000,100000]:
        g = plot_prime_pi(n, rgbcolor='red', thickness=2)
        g.save(dir + '/PN_%s.%s'%(n,ext))

def plot_prime_pi(n = 25, **args):
    v = [(0,0)]
    k = 0
    for p in prime_range(n+1):
        k += 1
        v.append((p,k))
    v.append((n,k))
    return plot_step_function(v, **args)
        
##############################################################
# Sieving
##############################################################

def fig_sieves(dir,ext):
    plot_three_sieves(100, shade=False).save(dir + '/sieve_2_100.%s'%ext, figsize=[9,3])
    plot_all_sieves(1000, shade=True).save(dir + '/sieve1000.%s'%ext,figsize=[9,3])

    m=100
    for z in [3,7]:
        save(plot_multiple_sieves(m,k=[z]) ,dir+'/sieves%s_100.%s'%(z,ext), xmax=m, figsize=[9,3])

def plot_sieve(n, x, poly={}, lin={}, label=True, shade=True):
    """
    Return a plot of the number of integer up to x that are coprime to n.
    These are the integers that are sieved out using the primes <= n.

    In n is 0 draw a graph of all primes. 
    """
    v = range(x+1)         # integers 0, 1, ..., x
    if n == 0:
        v = prime_range(x)
    else:
        for p in prime_divisors(n):
           v = [k for k in v if k%p != 0 or k==p]   
           # eliminate non-prime multiples of p
    v = set(v)
    j = 0 
    w = [(0,j)]
    for i in range(1,x+1):
        w.append((i,j))
        if i in v:
            j += 1
        w.append((i,j))
    w.append((i,0))
    w.append((0,0))
    if n == 0:
        t = "Primes"
        pos = x,.7*j
    elif n == 1:
        t = "All Numbers"
        pos = x, 1.03*j
    else:
        P = prime_divisors(n)
        if len(P) == 1:
            t = "Sieve by %s"%P[0]
        else:
            t = "Sieve by %s"%(', '.join([str(_) for _ in P]))
        pos = x,1.05*j
    F = line(w[:-2], **lin)
    if shade:
        F += polygon(w, **poly)
    if label:
        F += text(t, pos, horizontal_alignment="right", rgbcolor='black')
    return F

def plot_three_sieves(m, shade=True):
    s1 = plot_sieve(1, m, poly={'rgbcolor':(.85,.9,.7)},
                    lin={'rgbcolor':(0,0,0), 'thickness':1}, shade=shade)
    s2 = plot_sieve(2, m, poly={'rgbcolor':(.75,.8,.6)},
                    lin={'rgbcolor':(0,0,0),'thickness':1}, shade=shade)
    s3 = plot_sieve(0, m, poly={'rgbcolor':(1,.7,.5)},
                    lin={'rgbcolor':(1,0,0), 'thickness':1}, shade=shade)
    return s1+s2+s3

def plot_multiple_sieves(m=100, k = [2,3,5], shade=True):
    g = Graphics()
    n = len(k)
    for i in range(n):
        c = (1-float(i+1)/n)*0.666
        if k[i] == 0:
            z = 0
        else:
            z = prod(prime_range(k[i]+1))
        r = float(i)/n
        clr = (.85 + 0.15*r,0.9 -0.2*r, 0.9 -0.4*r)  
        if z == 0:
            clrlin=(1,0,0)
        else:
            clrlin=(0,0,0)
        s = plot_sieve(z, m, 
             poly={'rgbcolor':clr}, 
             lin={'rgbcolor':clrlin, 'thickness':1}, 
             label=(i==0 or i==n-1), shade=shade)
        g += s
    return g

def plot_all_sieves(x, shade=True):
    P = [1] + prime_range(int(sqrt(x))+1) + [0]
    G = plot_multiple_sieves(x, P, shade=shade)
    return G


##############################################################
# Area under plot of 1/log(x)
##############################################################

#auto
def area_under_inverse_log(m, **args):
    r"""
    This function returns a graphical illustration of `Li(x)` for `x
    \leq m` viewed as the integral of `1/\log(t)` from 2 to `t`.  We
    also plot primes on the `x`-axis and display the area as text.

    EXAMPLES::

    
    """
    f = plot(lambda x: 1/math.log(x), 2, m)  # TODO: weird.
    P = polygon([(2,0)]+list(f[0])+[(m,0)], hue=0.1,alpha=0.4)
    if False:
        T = sum([text(str(p),(p,-0.08),vertical_alignment="top",\
               horizontal_alignment="center", fontsize=6, rgbcolor=(.6,0,0)) \
            for p in prime_range(m+1)])
    else:
        T = Graphics()
    pr = sum([point((p,0), rgbcolor=(.6,0,0), pointsize=100/log(p)) for p in prime_range(m+1)])
    L = 'quad_qag(1/log(x), x, 2,%s, 0)'%m
    fs = 36
    area = text('Area ~ %f'%(float(maxima(L)[0])),(.5*m,.75),fontsize=fs,rgbcolor='black')
    primes = text('%s Primes'%len(prime_range(m+1)), (.5*m,-0.3),fontsize=fs,rgbcolor='black')
    fun = text('1/log(x)',(m/8.0,1.4),fontsize=fs,rgbcolor='black', horizontal_alignment='left')
    G = pr + f+P+area+T+primes +fun
    G.xmax(m+1)
    return G

def fig_inverse_of_log(dir,ext):
    for m in [30, 100, 1000]:
        area_under_inverse_log(m).save(dir+'/area_under_log_graph_%s.%s'%(m,ext), figsize=[7,7])

        
##############################################################
# Comparing Li, pi, and x/log(x)
##############################################################
def fig_li_pi_loginv(dir,ext):
    plot_li_pi_loginv(xmax=200).save(dir+'/three_plots.%s'%ext,figsize=[8,3])

def plot_li_pi_loginv(xmax=200):
    x = var('x')
    P = plot(x/log(x), (2, xmax))
    P+= plot(Li, (2, xmax), rgbcolor='black')
    P+= plot(prime_pi, 2, xmax, rgbcolor='red')
    return P


##############################################################
# Perspective
##############################################################

def fig_primes_line(dir,ext):
    xmin=1; xmax=38; pointsize=90
    g = points([(p,0) for p in prime_range(xmax+1)], pointsize=pointsize, rgbcolor='red')
    g += line([(xmin,0), (xmax,0)], rgbcolor='black')
    eps = 1/2.0
    for n in range(xmin, xmax+1):
        g += line([(n,eps), (n,-eps)], rgbcolor='black', thickness=0.5)
        g += text("$%s$"%n, (n,-6), rgbcolor='black')
    g.save(dir + '/primes_line.%s'%ext, axes=False,figsize=[9,.7], ymin=-10, ymax=2)

##############################################################
# Plots of Psi function
##############################################################

def psi_data(xmax):
    from math import log, pi
    v = [(0,0), (1,0), (1,log(2*pi))]
    y = v[-1][1]
    for pn in prime_powers(2,xmax+1):
        y += log(factor(pn)[0][0])
        v.append( (pn,y) )
    v.append((xmax,y))
    return v

def plot_psi(xmax, **kwds):
    v = psi_data(xmax)
    return plot_step_function(v, **kwds)

def fig_psi(dir,ext):
    for m in [9,38,100,200]:
        g = plot_psi(m, thickness=2)
        g.save(dir+'/psi_%s.%s'%(m,ext), aspect_ratio=1, gridlines=True,
               fontsize=20)
    g = plot(lambda x:x,1,1000,rgbcolor='red')+plot_psi(1000,alpha=0.8)
    g.save(dir+'/psi_diag_%s.%s'%(1000,ext),aspect_ratio=1, fontsize=20, gridlines=True)

def plot_Psi(xmax, **kwds):
    v = psi_data(xmax)
    v = [(log(a),b) for a, b in v if a]
    return plot_step_function(v, **kwds)

def fig_Psi(dir, ext):
    m = 38
    g = plot_Psi(m, thickness=2)
    g.save(dir+'/bigPsi_%s.%s'%(m,ext), gridlines=True,
           fontsize=20, figsize=[6.1,6.1])

def fig_Psiprime(dir, ext):
    g = line([(0,0),(0,100)], rgbcolor='black')
    xmax = 20
    ymax = 50 
    for n in range(1, xmax+1):
        if is_prime_power(n):
            if n == 1:
                h = log(2*pi)
            else: 
                h = log(factor(n)[0][0])
            c = (float(h)/log(xmax), 0, 1-float(h)/log(xmax))
            g += arrow((log(n),-1),(log(n),ymax), width=2, rgbcolor=c)
            if n <= 3 or n in [5, 8, 13, 19]:
               g += text("log(%s)"%n, (log(n),-5), rgbcolor='black', fontsize=12)
               g += line([(log(n),-2), (log(n),0)], rgbcolor='black')
    g += line([(-1/2.0,0), (xmax+1,0)], thickness=2)
    g.save(dir+'/bigPsi_prime.%s'%ext,
           xmin=-1/2.0, xmax=log(xmax), ymax=ymax,
             axes=False, gridlines=True, figsize=[8,3])    

def fig_Phi(dir=0, ext=0):
    g = line([(0,0),(0,100)], rgbcolor='black')
    xmax = 20
    ymax = 50 
    for n in range(1, xmax+1):
        if is_prime_power(n):
            if n == 1:
                h = log(2*pi)
            else: 
                h = log(factor(n)[0][0])
            h *= exp(-log(n)/2)
            c = (float(h)/log(xmax), 0, 1-float(h)/log(xmax))
            g += arrow((log(n),-1),(log(n),ymax), width=2, rgbcolor=c)
            g += arrow((-log(n),-1),(-log(n),ymax), width=2, rgbcolor=c)
            if n in [2, 5, 16]:
               g += text("log(%s)"%n, (log(n),-5), rgbcolor='black', fontsize=12)
               g += line([(log(n),-2), (log(n),0)], rgbcolor='black')
               g += text("log(%s)"%n, (-log(n),-5), rgbcolor='black', fontsize=12)
               g += line([(-log(n),-2), (-log(n),0)], rgbcolor='black')
    g += line([(-log(xmax)-1,0), (log(xmax)+1,0)], thickness=2)
    g.save(dir+'/bigPhi.%s'%ext,
           xmin=-log(xmax), xmax=log(xmax), ymax=ymax,
             axes=False, gridlines=True, figsize=[8,3])    


##############################################################
# Sin, etc. waves
##############################################################

def fig_waves(dir,ext):
    g = plot(sin, -2.1*pi, 2.1*pi, thickness=2)
    g.save(dir+'/sin.%s'%ext)

    x = var('x')
    c = 5
    # See for why this is right http://www.phy.mtu.edu/~suits/notefreqs.html
    g = plot(sin(x), 0, c*pi) + plot(sin(329.0/261*x), 0, c*pi, color='red')
    g.save(dir+'/sin-twofreq.%s'%ext)

    g = plot(sin(x) + sin(329.0/261*x), 0, c*pi) 
    g.save(dir+'/sin-twofreq-sum.%s'%ext)

    c=5
    g = plot(sin(x), -2, c*pi) + plot(sin(x + 1.5), -2, c*pi, color='red')
    g += text("Phase", (-3,.5), fontsize=14, rgbcolor='black')
    g += arrow((-2.5,.4), (-1.5,0), width=1, rgbcolor='black')
    g += arrow((-2,.4), (0,0), width=1, rgbcolor='black')
    g.save(dir+'/sin-twofreq-phase.%s'%ext, xmin=-5)

    g = plot(sin(x) + sin(329.0/261*x + 0.4), 0, c*pi)
    g.save(dir+'/sin-twofreq-phase-sum.%s'%ext)

    f = (sin(x) + sin(329.0/261*x + 0.4)).function(x)
    g = points([(i,f(i)) for i in erange(0,0.1,Ellipsis,5*pi)])
    g.save(dir+'/sin-twofreq-phase-sum-points.%s'%ext)

    g = points([(i,f(i)) for i in erange(0,0.1,Ellipsis,5*pi)])
    g += plot(f, (0, 5*pi), rgbcolor='black')
    g.save(dir+'/sin-twofreq-phase-sum-fill.%s'%ext)

    f = (0.7*sin(x) + sin(329.0/261*x + 0.4)).function(x)
    g = plot(f, (0, 5*pi))
    g.save(dir+'/sound-ce-general_sum.%s'%ext)

    B = bar_chart([0,0,0,0.7, 0, 1])
    B += text("C", (3.2,-0.05), rgbcolor='black', fontsize=18)
    B += text("D", (4.2,-0.05), rgbcolor='black', fontsize=18)
    B += text("E", (5.2,-0.05), rgbcolor='black', fontsize=18)
    B.save(dir+'/sound-ce-general_sum-blips.%s'%ext, axes=False, xmin=0)
    
    f = (0.7*sin(x) + sin(329.0/261*x + 0.4) +  0.5*sin(300.0/261*x + 0.7) + 0.3*sin(1.5*x + 0.2) + 1.1*sin(4*x+0.1)).function(x)
    g = plot(f, (0, 5*pi))
    g.save(dir + '/complicated-wave.%s'%ext)

##############################################################
# Pure Tone
##############################################################
def pure_tone(a=2, b=1, theta=1/2.0, tmin=-15, tmax=15):
    t = var('t')
    return plot(a*cos(b+theta*t), (t,tmin,tmax))

def fig_pure_tone(dir,ext):
    g = pure_tone()
    g.save(dir + '/pure_tone.%s'%ext, figsize=[8,2])


def mixed_tone3(a=[2,3,5], b=[1,4,-2], theta=[1/2.0,2,-1], tmin=-15, tmax=15):
    t = var('t')
    f = sum(a[i]*cos(b[i]+theta[i]*t) for i in range(3))
    return plot(f, (t,tmin,tmax)), f

def fig_mixed_tone3(dir,ext):
    g, f = mixed_tone3()
    g.save(dir + '/mixed_tone3.%s'%ext, figsize=[8,2])

    


##############################################################
# Sawtooth
##############################################################

def fig_sawtooth(dir,ext):
    g = plot_sawtooth(3)
    g.save(dir+'/sawtooth.%s'%ext, figsize=[10,2])
    
    g = plot_sawtooth_spectrum(18)
    g.save(dir+'/sawtooth-spectrum.%s'%ext, figsize=[8,3])

def plot_sawtooth(xmax):
    v = []
    for x in range(xmax+1):
        v += [(x,0), (x+1,1), (x+1,0)]
    return line(v)

def plot_sawtooth_spectrum(xmax):
    # the spectrum is a spike of height 1/k at k
    return sum([line([(k,0),(k,1.0/k)],thickness=3) for k in range(1,xmax+1)])

##############################################################
# Fourier Transforms: second visit 
##############################################################
def fig_even_function(dir, ext):
    x = var('x')
    f = cos(x) + sin(x**2) + sqrt(x)
    def g(z):
        return f(x=abs(z))
    h = plot(g,-4,4)
    h.save(dir + '/even_function.%s'%ext, figsize=[9,3])

def fig_even_pi(dir, ext):
    g1 = prime_pi.plot(0,50, rgbcolor='red')
    g2 = prime_pi.plot(0,50, rgbcolor='red')
    g2[0].xdata = [-a for a in g2[0].xdata]
    g = g1 + g2
    g.save(dir + '/even_pi.%s'%ext, figsize=[10,3],xmin=-49,xmax=49)

def fig_oo_integral(dir, ext):
    t = var('t')
    f = (1/(t**2+1)*cos(t)).function(t)
    a = f.find_root(1,2.5)
    b = f.find_root(4,6)
    c = f.find_root(7,8)
    g = plot(f,(t,-13,13), fill='axis', fillcolor='yellow', fillalpha=1, thickness=2)
    g += plot(f,(t,-a,a), fill='axis', fillcolor='grey', fillalpha=1, thickness=2)
    g += plot(f,(t,-c,-b), fill='axis', fillcolor='grey', fillalpha=1, thickness=2)
    g += plot(f,(t,b,c), fill='axis', fillcolor='grey', fillalpha=1, thickness=2)
    g += text(r"$\int_{-\infty}^{\,\infty} f(x) dx$", (-7,0.5), rgbcolor='black', fontsize=30)
    #g.show(figsize=[9,3], xmin=-10,xmax=10)
    g.save(dir+'/oo_integral.%s'%ext, figsize=[9,3], xmin=-10,xmax=10)

def fig_fourier_machine(dir, ext):
    g  = text("$f(t)$", (-1/2.0, 1/2.0), fontsize=20, rgbcolor='black')
    g += text(r"$\hat{f}(\theta)$", (3/2.0, 1/2.0), fontsize=20, rgbcolor='black')
    g += line([(0,0),(0,1),(1,1),(1,0),(0,0)],rgbcolor='black',thickness=3)
    g += arrow((-1/2.0 + 1/9.0, 1/2.0), (-1/16.0, 1/2.0), rgbcolor='black')
    g += arrow((1 + 1/16.0, 1/2.0), (1 + 1/2.0 - 1/9.0, 1/2.0), rgbcolor='black')
    t = var('t')
    g += plot((1/2.0)*t*cos(14*t) + 1/2.0, (t,0,1), fill='axis', thickness=0.8)
    g.save(dir+'/fourier_machine.%s'%ext, axes=False, axes_pad=0.1)
    

##############################################################
# Distribution section
##############################################################

def fig_simple_staircase(dir,ext):
    v = [(-1,0), (0,1), (1,3), (2,3)]
    g = plot_step_function(v, thickness=3, vertical_lines=True)
    g.save(dir+'/simple_staircase.%s'%ext)


##############################################################
# Plots of Fourier transform Phihat_even.
##############################################################

def fig_mini_phihat_even(dir,ext):
    G = plot_symbolic_phihat(5, 1, 100, 10000, zeros=False)
    G.save(dir + "/mini_phihat_even.%s"%ext, figsize=[9,3], ymin=0)

def fig_phihat_even(dir,ext):
    for bound in [5, 20, 50, 500]:
        G = plot_symbolic_phihat(bound, 2, 100,
                            plot_points=10**5)
        G.save(dir+'/phihat_even-%s.%s'%(bound,ext), figsize=[9,3], ymin=0)

def fig_phihat_even_all(dir, ext):
    p = [plot_symbolic_phihat(n, 2,100) for n in [5,20,50,500]]    
    [a.ymin(0) for a in p]
    g = graphics_array([[a] for a in p],4,1)
    g.save(dir+'/phihat_even_all.%s'%ext)

def symbolic_phihat(bound):
    t = var('t')
    f = SR(0)
    for pn in prime_powers(bound+1):
        if pn == 1: continue
        p, e = factor(pn)[0]
        f += - log(p)/sqrt(pn) * cos(t*log(pn))
    return f

def plot_symbolic_phihat(bound, xmin, xmax, plot_points=1000, zeros=True):
    f = symbolic_phihat(bound)
    P = plot(f, (t,xmin, xmax), plot_points=plot_points)
    if not zeros:
        return P
    ym = P.ymax()
    Z = []
    for y in zeta_zeros():
        if y > xmax: break
        Z.append(y)
    zeros = sum([arrow((x,ym),(x,0),rgbcolor='red',width=0.5,arrowsize=2)
                 for i, x in enumerate(Z)])
    return P + zeros

##############################################################
# Cesaro sums of Phi
##############################################################
def cesaro_sum(s):
    """
    INPUT:
        - s -- sequence of partial sums of an infinite series
    OUTPUT:
        - the sequences of Cesaro sums: 
              1/n * sum(s[k] for k from 0 up to n-1)      
    """
    ps = TimeSeries(s).sums()
    return TimeSeries([ps[i]/(i+1) for i in range(len(ps))])

def T_function():
    # Return the function T_C(theta) as fast float callable function.
    C, t = var('C, t')
    T = sqrt(C)/(ZZ(1)/4 + t**2) * (cos(t*log(C)) + 2*t*sin(t*log(C)))
    return fast_callable(T, vars=[C, t], domain=float)

def A_C_theta(Cmax):
    """
    Return the function denoted A_C(theta) in the book.
    This is Phi_hat_{<=C}(theta) + T_C(theta).
    """
    Z = [float(z) for z in zeta_zeros()]
    Cmax = int(Cmax)
    from math import log, sqrt
    P = [log(p) for p in prime_range(Cmax)]
    PP = prime_powers(Cmax)[1:]
    logPP = [log(pn) for pn in PP]
    logPP1 = [log(factor(pn)[0][0]) for pn in PP]
    PP2 = [sqrt(pn) for pn in PP]

    t = var('t')
    v = [(PP[i], fast_callable(-2*logPP1[i]/PP2[i] * cos(t*logPP[i]), vars=[t], domain=float)) for i in range(len(PP))]

    T = T_function()

    def f(C, t):
        C = float(C); t = float(t)
        a = T(C, t)
        for pp, g in v:
            if pp <= C:
                a += g(t)
            else:
                return a
        raise ValueError, "C must be at most %s"%Cmax

    return f

def A_C_theta_tilde(Cmax):
    A = A_C_theta(Cmax)
    def f(C, t):
        return sum(A(c, t) for c in range(1, C+1)) / float(C)
    return f

def B_C_theta(Cmax):
    A = A_C_theta_tilde(Cmax)
    from math import log
    def f(C, t):
        return A(C, t) / log(float(C))
    return f



def plot_B_C_theta(C, xmin, xmax, plot_points=250, zeros=True):
    f = B_C_theta(C+10)
    P = plot(lambda t:f(C,t), xmin, xmax, plot_points=plot_points, ymax=1.1, ymin=0)
    if not zeros:
        return P
    ym = P.ymax()
    Z = []
    for y in zeta_zeros():
        if y > xmax: break
        Z.append(y)
    zeros = sum([arrow((x,ym),(x,0),rgbcolor='red',width=0.5,arrowsize=2)
                 for i, x in enumerate(Z)])
    return P + zeros

# TODO: this is tooooo slow: like 50 seconds total!
def fig_B_C_theta(dir, ext, verbose=False):
    p = []
    for C in [5, 20, 50, 100]:
        p.append(plot_B_C_theta(C, 2, 100))
        if verbose:
            print "Finished with C=%s"%C
    g = graphics_array([[a] for a in p],len(p),1)
    g.save(dir+'/Bc_all.%s'%ext, ymin=0, ymax=1.1)


def B_C_theta_tilde(Cmax):
    B = B_C_theta(Cmax)
    def f(C, t):
        return sum(B(c, t) for c in range(2, C+1)) / float(C)
    return f


def plot_B_C_theta_tilde(C, xmin, xmax, plot_points=250, zeros=True):
    f = B_C_theta_tilde(C+10)
    P = plot(lambda t:f(C,t), xmin, xmax, plot_points=plot_points, ymax=1.1, ymin=0)
    if not zeros:
        return P
    ym = P.ymax()
    Z = []
    for y in zeta_zeros():
        if y > xmax: break
        Z.append(y)
    zeros = sum([arrow((x,ym),(x,0),rgbcolor='red',width=0.5,arrowsize=2)
                 for i, x in enumerate(Z)])
    return P + zeros

# TODO: this is tooooo slow: like 50 seconds total!
def fig_B_C_theta_tilde(dir, ext, verbose=False):
    p = []
    for C in [5, 20, 50, 100]:
        p.append(plot_B_C_theta_tilde(C, 2, 100))
        if verbose:
            print "Finished with C=%s"%C
    g = graphics_array([[a] for a in p],len(p),1)
    g.save(dir+'/Bctilde_all.%s'%ext, ymin=0, ymax=1.1)

    





## def Phi_hat_terms(C):
##     """
##     INPUT:
##         - C -- a positive integer
##     OUTPUT:
##         - function that takes as input t and returns the
##           sequence of partial sums of the series
##             -sum( p^(-n/2)*log(p)*cos(log(p^n)*t) ... )
##           where the sum is over the first C prime powers
##     """
##     Z = [float(z) for z in zeta_zeros()]
##     C = int(C)
##     B = nth_prime(C+1)
##     from math import log, sqrt, cos
##     P = [log(p) for p in prime_range(B)]
##     PP = prime_powers(B)[1:]
##     logPP = [log(pn) for pn in PP]
##     logPP1 = [log(factor(pn)[0][0]) for pn in PP]
##     PP2 = [sqrt(pn) for pn in PP]

##     def f(t):
##         t = float(t)
##         s = [float(0)]
##         for i in range(C):
##             x = - logPP1[i]/PP2[i] * cos(t*logPP[i])
##             s.append(s[-1] + x)
##         return TimeSeries(s[1:])  # get rid of the s[0] = 0 which we put in just to simplify the above code.
##     return f

## def A_C_tilde(C):
##     T = T_C(C)
##     A = Phi_hat_terms(C)
    
    
##############################################################
# Gaussian Primes
##############################################################




##############################################################
# Calculus pictures
##############################################################

def fig_aplusone(dir,ext):
    a = var('a')
    g = plot(a+1, -5,8, thickness=3)
    g.save(dir + '/graph_aplusone.%s'%ext, gridlines=True, frame=True)

def fig_calculus(dir,ext):
    x = var('x')
    t = 8; f = log(x); fprime = f.diff()
    fontsize = 14
    g = plot(f, (0.5,t)) 
    g += plot(x*fprime(x=4)+(f(x=4)-4*fprime(x=4)), (.5,t), rgbcolor='black')
    g += point((4,f(x=4)), pointsize=20, rgbcolor='black')
    g += plot(fprime, (0.5,t), rgbcolor='red')
    g += text("What is the slope of the tangent line?", (3.5,2.2), 
                  fontsize=fontsize, rgbcolor='black')
    g += text("Here it is!",(5,.9), fontsize=fontsize, rgbcolor='black')
    g += arrow((4.7,.76), (4, fprime(x=4)), rgbcolor='black')
    g += point((4,fprime(x=4)),rgbcolor='black', pointsize=20)
    g += text("How to compute the slope?  This is Calculus.", (4.3, -0.5), 
                  fontsize=fontsize, rgbcolor='black')
    g.save(dir + '/graph_slope_deriv.%s'%ext, gridlines=True, frame=True)

def fig_jump(dir,ext):
    # straight jump
    v = line( [(0,1), (3,1), (3,2), (6,2)], thickness=2)
    v.ymin(0)
    v.save(dir + '/jump.%s'%ext)

    # smooth approximation to a jump
    e = .7
    v = line( [(0,1), (3-e,1)], thickness=2) + line([(3+e,2), (6,2)], thickness=2)
    v.ymin(0)
    S = spline( [(3-e,1), (3-e + e/20.0, 1), (3,1.5), (3+e-e/20.0, 2), (3+e,2)] )
    v += plot(S, (3-e, 3+e), thickness=2)
    v.save(dir + '/jump-smooth.%s'%ext, ymin=0)

    # derivatives of smooth jumps
    for e in ['7', '2', '05', '01']:
        g = smoothderiv(float('.'+e))
        g.save(dir + '/jump-smooth-deriv-%s.%s'%(e,ext))


def smoothderiv(e):
    def deriv(f, delta):
        # return very approximate numerical derivative of callable f, using
        # a given choice of delta
        def g(x):
            return (f(x + delta) - f(x))/delta
        return g
    
    v = line( [(0,1), (3-e,1)], thickness=2) + line([(3+e,2), (6,2)], thickness=2)
    v.ymin(0)
    S = spline( [(3-e,1), (3-e+e/20.0, 1), (3,1.5), (3+e-e/20.0, 2), (3+e,2)] )
    v += plot(S, (3-e, 3+e), thickness=2)
    D = (line( [(0,0), (3-e,0)], rgbcolor='red', thickness=2) +
         line([(3+e,0), (6,0)], rgbcolor='red', thickness=2))
    D += plot( deriv(S, e/30.0), (3-e, 3+e), rgbcolor='red', thickness=2)
    v += D
    return v


def fig_dirac(dir,ext):
    g = line([(0,0),(0,100)], rgbcolor='black')
    g += arrow((0,-1),(0,50), width=3)
    g += line([(-1.2,0), (1.25,0)], thickness=3)    
    g.save(dir+'/dirac_delta.%s'%ext,
           frame=False, xmin=-1, xmax=1, ymax=50, axes=False, gridlines=True) 

def fig_two_delta(dir,ext):
    g = line([(0,0),(0,100)], rgbcolor='black')
    g += arrow((-1/2.0,-1),(-1/2.0,50),width=3)
    g += arrow((1/2.0,-1),(1/2.0,50),width=3)
    g += line([(-1.2,0), (1.25,0)], thickness=3)
    g += text("$-x$", (-1/2.0 - 1/20.0,-4), rgbcolor='black', fontsize=35, horizontal_alignment='center')
    g += text("$x$", (1/2.0,-4), rgbcolor='black', fontsize=35, horizontal_alignment='center')
    g.save(dir+'/two_delta.%s'%ext,
           frame=False, xmin=-1, xmax=1, ymax=50, axes=False, gridlines=True)    

##############################################################
# Cosine sums
##############################################################

def fig_phi(dir,ext):
    g = phi_approx_plot(2,30,1000)
    g.save(dir+'/phi_cos_sum_2_30_1000.%s'%ext, ymin=-5,ymax=160)

    g = phi_interval_plot(26, 34)
    g.save(dir+'/phi_cos_sum_26_34_1000.%s'%ext, axes=False)

    g = phi_interval_plot(1010,1026,15000,drop=60)
    g.save(dir+'/phi_cos_sum_1010_1026_15000.%s'%ext, axes=False, ymin=-50)
    
def phi_interval_plot(xmin, xmax, zeros=1000,fontsize=12,drop=20):
    g = phi_approx_plot(xmin,xmax,zeros=zeros,fontsize=fontsize,drop=drop)
    g += line([(xmin,0),(xmax,0)],rgbcolor='black')
    return g


def phi_approx(m, positive_only=False, symbolic=False):
    if symbolic:
        assert not positive_only
        s = var('s')
        return -sum(cos(log(s)*t) for t in zeta_zeros()[:m])
    
    from math import cos, log
    v = [float(z) for z in zeta_zeros()[:m]]
    def f(s):
        s = log(float(s))
        return -sum(cos(s*t) for t in v)
    if positive_only:
        z = float(0)
        def g(s):
            return max(f(s),z)
        return g
    else:
        return f

def phi_approx_plot(xmin, xmax, zeros, pnts=2000, dots=True, positive_only=False,
                    fontsize=7, drop=10, **args):
    phi = phi_approx(zeros, positive_only)
    g = plot(phi, xmin, xmax, alpha=0.7, 
              plot_points=pnts, adaptive_recursion=0, **args)
    g.xmin(xmin); g.xmax(xmax)
    if dots: g += primepower_dots(xmin,xmax, fontsize=fontsize,drop=drop)
    return g

def primepower_dots(xmin, xmax, fontsize=7, drop=10):
    """
    Return plot with dots at the prime powers in the given range.
    """
    g = Graphics()
    for n in range(max(xmin,2),ceil(xmax)+1):
        F = factor(n)
        if len(F) == 1:
           g += point((n,0), pointsize=50*log(F[0][0]), rgbcolor=(1,0,0)) 
           if fontsize>0: 
               g += text(str(n),(n,-drop),fontsize=fontsize, rgbcolor='black')
    g.xmin(xmin)
    g.xmax(xmax)
    return g

##############################################################
# psi waves
##############################################################

def fig_psi_waves(dir, ext):
    theta, t = var('theta, t')
    f = (theta*sin(t*theta) + 1/2.0 * cos(t*theta)) / (theta**2 + 1/4.0)
    g = plot(f(theta=zeta_zeros()[0]),(t,0,pi))
    g.save(dir + '/psi_just_waves1.%s'%ext)

    g += plot(f(theta=zeta_zeros()[1]),(t,0,pi), rgbcolor='red')
    g.save(dir + '/psi_2_waves.%s'%ext)

    f = (e**(t/2)*theta*sin(t*theta) + 1/2.0 * e**(t/2) * cos(t*theta))/(theta**2 + 1/4.0)
    g = plot(f(theta=zeta_zeros()[0]),(t,0,pi))
    g.save(dir + '/psi_with_first_zero.%s'%ext)

    g += plot(f(theta=zeta_zeros()[1]),(t,0,pi), rgbcolor='red')
    g.save(dir + '/psi_with_exp_2.%s'%ext)
    

##############################################################
# Riemann's R_k
##############################################################

def fig_moebius(dir,ext):
    g = plot(moebius,0, 50)
    g.save(dir+'/moebius.%s'%ext,figsize=[10,2], axes_pad=.1)
    

def riemann_R(terms):
    c = [0] + [float(moebius(n))/n for n in range(1, terms+1)]
    def f(x):
        x = float(x)
        s = float(0)
        for n in range(1,terms+1):
            y = x**(1.0/n)
            if y < 2:
                break
            s += c[n] * Li(y)
        return s
    return f

def plot_pi_riemann_gauss(xmin, xmax, terms):
    R = riemann_R(terms)
    g = plot(R, xmin, xmax)
    g += plot(prime_pi, xmin, xmax, rgbcolor='red')
    g += plot(Li, xmin, xmax, rgbcolor='purple')
    #x = var('x'); g += plot(x/(log(x)-1), xmin, xmax, rgbcolor='green')
    return g

def fig_pi_riemann_gauss(dir,ext):
    for m in [100,1000]:
        g = plot_pi_riemann_gauss(2,m, 100)
        g.save(dir+'/pi_riemann_gauss_%s.%s'%(m,ext))
    g = plot_pi_riemann_gauss(10000,11000, 100)
    g.save(dir +'/pi_riemann_gauss_10000-11000.%s'%ext, axes=False, frame=True)

    
class RiemannPiApproximation:
    r"""
    Riemann's explicit formula for `\pi(X)`.

    EXAMPLES::

    We compute Riemann's analytic approximatin to `\pi(25)` using `R_{10}(x)`:
    
        sage: R = RiemannPiApproximation(10, 100); R
        Riemann explicit formula for pi(x) for x <= 100 using R_k for k <= 10
        sage: R.Rk(100, 10)
        25.3364299527
        sage: prime_pi(100)
        25
    
    """
    def __init__(self, kmax, xmax, prec=50):
        """
        INPUT:

            - ``kmax`` -- (integer) large k allowed

            - ``xmax`` -- (float) largest input x value allowed

            - ``prec`` -- (default: 50) determines precision of certain series approximations
        
        """
        from math import log
        self.xmax = xmax
        self.kmax = kmax
        self.prec = prec
        self.N = int(log(xmax)/log(2))
        self.rho_k = [0] + [CDF(0.5, zeta_zeros()[k-1]) for k in range(1,kmax+1)]
        self.rho = [[0]+[rho_k / float(n) for n in range(1, self.N+1)]  for rho_k in self.rho_k]
        self.mu = [float(x) for x in moebius.range(0,self.N+2)]
        self.msum = sum([moebius(n) for n in xrange(1,self.N+1)])
        self._init_coeffs()

    def __repr__(self):
        return "Riemann explicit formula for pi(x) for x <= %s using R_k for k <= %s"%(self.xmax, self.kmax)

    def _init_coeffs(self):
        self.coeffs = [1]
        n_factorial = 1.0
        for n in xrange(1, self.prec):
            n_factorial *= n
            zeta_value = float(abs(zeta(n+1)))
            self.coeffs.append(float(1.0/(n_factorial*n*zeta_value)))
    
    def _check(self, x, k):
        if x > self.xmax:
             raise ValueError, "x (=%s) must be at most %s"%(x, self.xmax)
        if k > self.kmax:
            raise ValueError, "k (=%s) must be at most %s"%(k, self.kmax)

    @cached_method
    def R(self, x):
        from math import log
        y = log(x)
        z = y
        a = float(1)
        for n in xrange(1,self.prec):
            a += self.coeffs[n]*z
            z *= y
        return a

    @cached_method
    def Rk(self, x, k):
        return self.R(x) + self.Sk(x, k)

    @cached_method
    def Sk(self, x, k):
        """
        Compute approximate correction term, so Rk(x,k) = R(x) + Sk(x,k)
        """
        self._check(x, k)

        from math import atan, pi, log
        log_x = log(x)  # base e
        # This is from equation 32 on page 978 of Riesel-Gohl.
        term1 = self.msum / (2*log_x) + \
                   (1/pi) * atan(pi/log_x)
    
        # This is from equation 19 on page 975
        term2 = sum(self.Tk(x, v) for v in xrange(1,k+1))
        return term1 + term2

    @cached_method
    def Tk(self, x, k):
        """
        Compute sum from 1 to N of
           mu(n)/n * ( -2*sqrt(x) * cos(im(rho_k/n)*log(x) \
                - arg(rho_k/n)) / ( pi_over_2 * log(x) )
        """
        self._check(x, k)
        x = float(x)
        log_x = log(x)
        val = float(0)
        rho_k = self.rho_k[k]
        rho = self.rho[k]
        for n in xrange(1, self.N+1):
            rho_k_over_n = rho[n]
            mu_n = self.mu[n]
            if mu_n != 0:
                z = Ei( rho_k_over_n * log_x)
                val += (mu_n/float(n)) * (2*z).real()
        return -val

    def plot_Rk(self, k, xmin=2, xmax=None, **kwds):
        r"""
        Plot `\pi(x)` and `R_k` between ``xmin`` and ``xmax``.  If `k`
        is a list, also plot every `R_k`, for `k` in the list.

        The **kwds are passed onto the line function, which is used
        to draw the plot of `R_k`.
        """
        if not xmax:
            xmax = self.xmax
        else:
            if xmax > self.xmax:
                raise ValueError, "xmax must be at most %s"%self.xmax
            xmax = min(self.xmax, xmax)
        if kwds.has_key('plot_points'):
            plot_points = kwds['plot_points']
            del kwds['plot_points']
        else:
            plot_points = 100
        eps = float(xmax-xmin)/plot_points
        if not isinstance(k, list):
            k = [k]
        f = sum(line([(x,self.Rk(x,kk)) for x in erange(xmin,xmin+eps,Ellipsis,xmax)], **kwds)
                for kk in k)
        g = prime_pi.plot(xmin, xmax, rgbcolor='red')
        return g+f


def fig_Rk(dir, ext):
    R = RiemannPiApproximation(50, 500, 50)
    for k,xmin,xmax in [(1,2,100), (10,2,100), (25,2,100),
                        (50,2,100), (50,2,500) ]:
        print "plotting k=%s"%k
        g = R.plot_Rk(k, xmin, xmax, plot_points=300, thickness=0.65)
        g.save(dir + '/Rk_%s_%s_%s.%s'%(k,xmin,xmax,ext))
    # 
    g = R.plot_Rk(50, 350, 400, plot_points=200)
    g += plot(Li,350,400,rgbcolor='green')
    g.save(dir + '/Rk_50_350_400.%s'%ext)




#################################################################
# Import fast cython versions of some functions, if available.

try:
    from psage.rh.mazur_stein.book_cython import mult_parities
except ImportError, msg:
    print msg
    print "Cython versions of some functions not available."
    mult_parieties = mult_parities_python

