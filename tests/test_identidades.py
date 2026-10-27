"""Identidade contábil entre turnos com dados sintéticos (sem dados reais)."""
import duckdb


def test_reconciliacao_entre_turnos_fecha():
    con = duckdb.connect()
    con.execute("""CREATE TABLE b AS SELECT * FROM (VALUES
        (1, 100, 80, 70, 4, 6), (2, 100, 85, 78, 3, 4)) t(turno, aptos, comp, validos, brancos, nulos)""")
    r = con.execute("""SELECT (b2.validos - b1.validos) - ((b2.comp - b1.comp) - ((b2.brancos + b2.nulos) - (b1.brancos + b1.nulos)))
        FROM b b1, b b2 WHERE b1.turno = 1 AND b2.turno = 2""").fetchone()[0]
    assert r == 0
