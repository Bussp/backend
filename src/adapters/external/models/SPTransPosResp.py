from typing import TypedDict, List


class Vehicle(TypedDict):
    p: str       # prefixo do ônibus
    a: bool      # acessibilidade
    ta: str      # timestamp ISO
    py: float    # latitude
    px: float    # longitude


class SPTransPositionsResponse(TypedDict):
    hr: str           # horário da resposta
    vs: List[Vehicle] # lista de veículos
