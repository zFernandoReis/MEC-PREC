from enum import Enum


class FuelType(str, Enum):
    GASOLINE = "gasoline"
    ETHANOL = "ethanol"
    FLEX = "flex"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"