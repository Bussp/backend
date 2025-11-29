from typing import TypedDict


class Vehicle(TypedDict):
    p: str       # prefixo do ônibus
    a: bool      # acessibilidade
    ta: str      # timestamp ISO
    py: float    # latitude
    px: float    # longitude


class SPTransPositionsResponse(TypedDict):
    hr: str           # horário da resposta
    vs: list[Vehicle] # lista de veículos
