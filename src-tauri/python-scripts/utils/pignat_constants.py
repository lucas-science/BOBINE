TIME = 'Time'
TT301 = 'TT301 °C'
TT302 = 'TT302 °C'
TT303 = 'TT303 °C'
FT240 = 'FT240'
PI177 = 'PI177 bar'
PT230 = 'PT230 bar'

TEMPERATURE_DEPENDING_TIME = 'Température par rapport au temps'
DEBIMETRIC_RESPONSE_DEPENDING_TIME = 'Réponsse débimétrique par rapport au temps'
PRESSURE_PYROLYSEUR_DEPENDING_TIME = 'Pression pyrolyseur par rapport au temps'
PRESSURE_POMPE_DEPENDING_TIME = 'Pression sortie pompe par rapport au temps'
DELTA_PRESSURE_DEPENDING_TIME = 'Delta de pression entre le pyrilyseur et la pompe'



DATA_REQUIRED = [TIME, TT301, TT302, TT303, FT240, PI177, PT230]

GRAPHS = [
    {
        'name': TEMPERATURE_DEPENDING_TIME,
        'columns': [TIME, TT301, TT302, TT303]
    },
    {
        'name': DEBIMETRIC_RESPONSE_DEPENDING_TIME,
        'columns': [TIME, FT240]
    },
    {
        'name': PRESSURE_PYROLYSEUR_DEPENDING_TIME,
        'columns': [TIME, PI177]
    },
    {
        'name': PRESSURE_POMPE_DEPENDING_TIME,
        'columns': [TIME, PT230]
    },
    {
        'name': DELTA_PRESSURE_DEPENDING_TIME,
        'columns': [TIME, PI177, PT230]
    }
]