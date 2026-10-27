import numpy as np
import pandas as pd

from observatorio.estatistica import _d2, _simular, holm
from observatorio.relatorios import n


def test_holm_monotono_e_limitado():
    p = pd.Series([0.01, 0.04, 0.03, 0.5])
    a = holm(p)
    assert a[0] == 0.04 and a[2] == 0.09 and a[1] == 0.09 and a[3] == 0.5
    assert (a <= 1).all()


def test_segundo_digito():
    assert list(_d2(np.array([10, 123, 4567, 99]))) == [0, 2, 5, 9]


def test_simulacao_binomial_distribuicoes_validas():
    u, d = _simular(np.full(2000, 300), np.full(2000, 0.5), rep=2)
    assert abs(u.sum() - 1) < 1e-9 and abs(d.sum() - 1) < 1e-9
    assert np.all(np.abs(u - 0.1) < 0.02)  # último dígito ~uniforme para contagens grandes


def test_formato_brasileiro():
    assert n(1234567) == "1.234.567"
    assert n(20.946, 2) == "20,95"
    assert n(None) == "—"
