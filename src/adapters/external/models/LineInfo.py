from typing import TypedDict, List


class LineInfo(TypedDict):
    cl: int     # código da linha (código interno SPTrans)
    lc: bool    # sentido preferencial (circular / comum)
    lt: str     # número da linha (ex: "8000")
    sl: int     # sentido (0: ida, 1: volta)
    tl: int     # tipo da linha (10 = urbana, etc.)
    tp: str     # ponto inicial
    ts: str     # ponto final
