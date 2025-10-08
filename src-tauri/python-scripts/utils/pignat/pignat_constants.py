TIME = 'Time'
TT301 = 'TT301 °C'
TT302 = 'TT302 °C'
TT303 = 'TT303 °C'
TT206 = 'TT206 °C'
FT240 = 'FT240'
PI177 = 'PI177 bar'
PT230 = 'PT230 bar'

# Internal metric names (used for API communication - NO ACCENTS to avoid serialization issues)
TEMPERATURE_DEPENDING_TIME = 'temperature_time'
DEBIMETRIC_RESPONSE_DEPENDING_TIME = 'debimetric_time'
PRESSURE_PYROLYSEUR_DEPENDING_TIME = 'pressure_pyrolyseur_time'
PRESSURE_POMPE_DEPENDING_TIME = 'pressure_pump_time'
DELTA_PRESSURE_DEPENDING_TIME = 'delta_pressure_time'

# Display titles for Excel (with accents and special characters)
TEMPERATURE_DISPLAY_TITLE = 'Suivi de Température des inducteurs'
DEBIMETRIC_DISPLAY_TITLE = 'Suivi du débit massique'
PRESSURE_PYROLYSEUR_DISPLAY_TITLE = 'Pression dans le pyrolyseur'
PRESSURE_POMPE_DISPLAY_TITLE = 'Pression en sortie de pompe'
DELTA_PRESSURE_DISPLAY_TITLE = 'DP (Pyrolyseur – Pompe)'

# Mapping internal IDs to display names
DISPLAY_NAME_MAPPING = {
    TEMPERATURE_DEPENDING_TIME: TEMPERATURE_DISPLAY_TITLE,
    DEBIMETRIC_RESPONSE_DEPENDING_TIME: DEBIMETRIC_DISPLAY_TITLE,
    PRESSURE_PYROLYSEUR_DEPENDING_TIME: PRESSURE_PYROLYSEUR_DISPLAY_TITLE,
    PRESSURE_POMPE_DEPENDING_TIME: PRESSURE_POMPE_DISPLAY_TITLE,
    DELTA_PRESSURE_DEPENDING_TIME: DELTA_PRESSURE_DISPLAY_TITLE,
}

DATA_REQUIRED = [TIME, TT301, TT302, TT303, TT206, FT240, PI177, PT230]

GRAPHS = [
    {
        'name': TEMPERATURE_DEPENDING_TIME,
        'columns': [TIME, TT301, TT302, TT303, TT206]
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