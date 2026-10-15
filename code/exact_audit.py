"""Exact small-instance comparability utilities (Python standard library only).

All financial inputs and calculations use fractions.Fraction.  Floats are rejected
at the public conversion boundary. The quadratic optimiser requires explicit box
bounds, so its feasible polytope is bounded. It enumerates stationary points on
faces; unlike a vertex-only test it handles indefinite and singular quadratics.
This is an exponential reference implementation, not a large-scale optimiser.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from typing import Iterable, Sequence

F = Fraction

def rational(x: int | str | Fraction) -> Fraction:
    if isinstance(x, float):
        raise TypeError("Use an integer, rational string or Fraction, not float")
    return F(x)

def dot(a: Sequence[Fraction], b: Sequence[Fraction]) -> Fraction:
    if len(a) != len(b):
        raise ValueError("dot product dimension mismatch")
    return sum((x*y for x, y in zip(a, b)), F(0))


def affine_space(E: Sequence[Sequence[Fraction]], f: Sequence[Fraction], n: int):
    """Return exact (particular solution, nullspace basis) to E x=f, or None."""
    if len(E) != len(f) or any(len(row) != n for row in E):
        raise ValueError("Invalid equality-system dimensions")
    a = [[rational(v) for v in row] + [rational(rhs)] for row, rhs in zip(E, f)]
    pivots = []
    r = 0
    for col in range(n):
        k = next((i for i in range(r, len(a)) if a[i][col]), None)
        if k is None:
            continue
        a[r], a[k] = a[k], a[r]
        v = a[r][col]
        a[r] = [x/v for x in a[r]]
        for i in range(len(a)):
            if i != r and a[i][col]:
                v = a[i][col]
                a[i] = [x-v*y for x, y in zip(a[i], a[r])]
        pivots.append(col)
        r += 1
        if r == len(a):
            break
    if any(not any(row[:n]) and row[n] for row in a):
        return None
    x0 = [F(0)]*n
    for i, col in enumerate(pivots):
        x0[col] = a[i][n]
    basis = []
    for col in (j for j in range(n) if j not in pivots):
        v = [F(0)]*n
        v[col] = F(1)
        for i, p in enumerate(pivots):
            v[p] = -a[i][col]
        basis.append(v)
    return x0, basis


def feasible_point(A, b, E, f, n):
    """Find a rational point in bounded {x: Ax<=b, Ex=f}, or return None.

    Uses vertex enumeration in the affine subspace. Boundedness is supplied by
    the explicit box constraints inserted by min_quadratic.
    """
    sol = affine_space(E, f, n)
    if sol is None:
        return None
    x0, basis = sol
    k = len(basis)
    if k == 0:
        return x0 if all(dot(row, x0) <= rhs for row, rhs in zip(A, b)) else None
    Ar = [[dot(row, v) for v in basis] for row in A]
    br = [rhs-dot(row, x0) for row, rhs in zip(A, b)]
    for J in combinations(range(len(A)), k):
        candidate = affine_space([Ar[j] for j in J], [br[j] for j in J], k)
        if candidate is None or candidate[1]:
            continue
        y = candidate[0]
        if all(dot(row, y) <= rhs for row, rhs in zip(Ar, br)):
            return [x0[i]+sum((basis[j][i]*y[j] for j in range(k)), F(0)) for i in range(n)]
    return None

@dataclass(frozen=True)
class QuadraticResult:
    minimum: Fraction
    point: tuple[Fraction, ...]
    candidates: tuple[dict, ...]


def min_quadratic(Q, linear, constant, lower, upper, extra_A=(), extra_b=()):
    """Exactly minimise x^T Q x + linear^T x + constant on a boxed polytope.

    Q must be symmetric. A rational witness from every nonempty face-stationary
    solution set is examined. That solution set has a constant objective value,
    including when the projected Hessian is singular. The proof is in the paper.
    """
    lo, hi = list(map(rational, lower)), list(map(rational, upper))
    n = len(lo)
    if n == 0 or len(hi) != n or any(l > h for l, h in zip(lo, hi)):
        raise ValueError("A nonempty-dimensional ordered bounding box is required")
    Q = [list(map(rational, row)) for row in Q]
    linear = list(map(rational, linear))
    constant = rational(constant)
    if len(Q) != n or any(len(row) != n for row in Q) or len(linear) != n:
        raise ValueError("Invalid quadratic dimensions")
    if any(Q[i][j] != Q[j][i] for i in range(n) for j in range(n)):
        raise ValueError("Q must be symmetric")
    A, b = [], []
    for i in range(n):
        row = [F(0)]*n
        row[i] = F(-1)
        A.append(row); b.append(-lo[i])
        row = [F(0)]*n
        row[i] = F(1)
        A.append(row); b.append(hi[i])
    if len(extra_A) != len(extra_b):
        raise ValueError("Invalid extra constraints")
    for row, rhs in zip(extra_A, extra_b):
        if len(row) != n:
            raise ValueError("Invalid extra constraint dimension")
        A.append(list(map(rational, row))); b.append(rational(rhs))
    candidates = []
    # Every face has an independent active-row basis of at most n rows.
    for k in range(n+1):
        for I in combinations(range(len(A)), k):
            EI, fi = [A[i] for i in I], [b[i] for i in I]
            affine = affine_space(EI, fi, n)
            if affine is None or n-len(affine[1]) != k:
                continue
            tangent = affine[1]
            E, f = EI[:], fi[:]
            for v in tangent:
                E.append([2*sum((v[i]*Q[i][j] for i in range(n)), F(0)) for j in range(n)])
                f.append(-dot(v, linear))
            point = feasible_point(A, b, E, f, n)
            if point is None:
                continue
            value = constant + dot(linear, point) + sum(
                (point[i]*Q[i][j]*point[j] for i in range(n) for j in range(n)), F(0))
            candidates.append({"face_basis": list(I), "point": point, "value": value})
    if not candidates:
        raise ValueError("The boxed polytope is empty")
    winner = min(candidates, key=lambda z: (z["value"], tuple(z["point"])))
    return QuadraticResult(winner["value"], tuple(winner["point"]), tuple(candidates))

@dataclass(frozen=True)
class Metrics:
    pv: Fraction
    moment: Fraction
    duration: Fraction
    programme_service: Fraction


def metrics(cashflows: dict[int, Fraction], rate: Fraction, programme_end: int,
            programme_start: int = 0) -> Metrics:
    rate = rational(rate)
    if rate <= -1:
        raise ValueError("Annual discount rate must exceed -1")
    if programme_start > programme_end:
        raise ValueError("Invalid programme window")
    if any(not isinstance(t, int) or t < 0 for t in cashflows):
        raise ValueError("This executable kernel requires nonnegative integer dates")
    cf = {t: rational(v) for t, v in cashflows.items()}
    if any(v < 0 for v in cf.values()):
        raise ValueError("Negative cashflows require a separately specified model")
    pv = sum((v/(1+rate)**t for t, v in cf.items()), F(0))
    moment = sum((t*v/(1+rate)**t for t, v in cf.items()), F(0))
    if pv <= 0:
        raise ValueError("Duration is undefined for a zero-value payment stream")
    service = sum((v for t, v in cf.items() if programme_start <= t <= programme_end), F(0))
    return Metrics(pv, moment, moment/pv, service)


def efforts(old: Metrics, new: Metrics) -> tuple[Fraction, Fraction, Fraction]:
    if old.programme_service <= 0:
        raise ValueError("Old programme service is zero; declare a different flow criterion")
    # First two signs reversed from the Paris Club's Post/Pre - 1 convention.
    return (1-new.pv/old.pv,
            1-new.programme_service/old.programme_service,
            new.duration-old.duration)


def interval_from_rows(rows: Iterable[tuple[str, Fraction, Fraction]],
                       upper_limit: Fraction | None = None):
    """Intersect p>=0 and a*p<=b rows. Return (lower, upper, witnesses) or None.

    A negative row coefficient imposes a lower bound, not an upper cap.
    None for upper means +infinity. Zero-coefficient inconsistent rows fail.
    """
    lower = F(0)
    upper = None if upper_limit is None else rational(upper_limit)
    witnesses = []
    for name, a, b in rows:
        a, b = rational(a), rational(b)
        if a == 0:
            if b < 0:
                return None
            witnesses.append({"row": name, "kind": "constant", "slack": b})
        elif a > 0:
            cap = b/a
            if upper is None or cap < upper:
                upper = cap
            witnesses.append({"row": name, "kind": "upper", "value": cap})
        else:
            floor = b/a
            lower = max(lower, floor)
            witnesses.append({"row": name, "kind": "lower", "value": floor})
    if upper is not None and lower > upper:
        return None
    return lower, upper, witnesses


def payment_rows(old_i: Metrics, old_o: Metrics, base_i: Metrics,
                 reference: Metrics, payment_shape: dict[int, Fraction],
                 rate: Fraction, programme_end: int,
                 tolerances=(F(0), F(0), F(0)), programme_start: int = 0):
    """Linear rows for a scalar p paid according to a fixed nonnegative shape.

    The benchmark is fixed while p is designed. This is not a simultaneous
    optimisation over both creditors' agreements.
    """
    if old_i.programme_service <= 0 or old_o.programme_service <= 0:
        raise ValueError("Positive old programme-service denominators required")
    ev, es, ed = map(rational, tolerances)
    if min(ev, es, ed) < 0:
        raise ValueError("Tolerances must be nonnegative")
    rate = rational(rate)
    if rate <= -1 or programme_start > programme_end:
        raise ValueError("Invalid rate or programme window")
    if any(not isinstance(t, int) or t < 0 for t in payment_shape):
        raise ValueError("Payment dates must be nonnegative integers")
    q = {t: rational(v) for t, v in payment_shape.items()}
    if any(v < 0 for v in q.values()):
        raise ValueError("Payment shape must be nonnegative")
    v = sum((c/(1+rate)**t for t, c in q.items()), F(0))
    m = sum((t*c/(1+rate)**t for t, c in q.items()), F(0))
    s = sum((c for t, c in q.items() if programme_start <= t <= programme_end), F(0))
    bound_v = old_i.pv*(reference.pv/old_o.pv+ev)
    bound_s = old_i.programme_service*(reference.programme_service/old_o.programme_service+es)
    target_d = old_i.duration+reference.duration-old_o.duration-ed
    return [
        ("NPV", v, bound_v-base_i.pv),
        ("programme", s, bound_s-base_i.programme_service),
        ("duration", target_d*v-m,
         base_i.moment-target_d*base_i.pv),
    ]


def jsonable(obj):
    if isinstance(obj, Fraction):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (tuple, list)):
        return [jsonable(v) for v in obj]
    if hasattr(obj, "__dataclass_fields__"):
        return {k: jsonable(getattr(obj, k)) for k in obj.__dataclass_fields__}
    return obj
