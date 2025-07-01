TIME = 'Time'
TT301 = 'TT301 °C'
TT302 = 'TT302 °C'
TT303 = 'TT303 °C'
FT240 = 'FT240'
PI177 = 'PI177 bar'
PT230 = 'PT230 bar'



DATA_REQUIRED = [TIME, TT301, TT302, TT303, FT240, PI177, PT230]

GRAPHS = [
    {
        'name': 'Température par rapport au temps',
        'columns': [TIME, TT301, TT302, TT303]
    },
    {
        'name': 'Réponsse débimétrique par rapport au temps',
        'columns': [TIME, FT240, "caca"]
    },
    {
        'name': 'Pression pyrolyseur par rapport au temps',
        'columns': [TIME, PI177]
    },
    {
        'name': 'Pression sortie pompe par rapport au temps',
        'columns': [TIME, PT230]
    },
    {
        'name': 'Delta de pression entre le pyrilyseur et la pompe',
        'columns': [TIME, PI177, PT230]
    }
]