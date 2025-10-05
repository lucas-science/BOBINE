# Constants for ChromeleonOnline (chromeleon_online.py)
# Mapping of chemical compounds to their carbon number and chemical family

COMPOUND_MAPPING = {
    'Methane':             ('C1', 'Paraffin'),
    'Ethane':              ('C2', 'Paraffin'),
    'Ethylene':            ('C2', 'Olefin'),
    'Propane':             ('C3', 'Paraffin'),
    'Cyclopropane':        ('C3', 'Autres'),
    'Propylene':           ('C3', 'Olefin'),
    'Propadiene':          ('C3', 'Olefin'),
    'iso-Butane':          ('C4', 'Paraffin'),
    'Acetylene':           ('C2', 'Autres'),
    'n-Butane':            ('C4', 'Paraffin'),
    'trans-2-Butene':      ('C4', 'Olefin'),
    '1-Butene':            ('C4', 'Olefin'),
    'iso-Butylene':        ('C4', 'Olefin'),
    'cis-2-Butene':        ('C4', 'Olefin'),
    'iso-Pentane':         ('C5', 'Olefin'),
    'n-Pentane':           ('C5', 'Paraffin'),
    '1,3-Butadiene':       ('C4', 'Olefin'),
    'trans-2-Pentene':     ('C5', 'Olefin'),
    '2-methyl-2-Butene':   ('C5', 'Olefin'),
    '1-Pentene':           ('C5', 'Olefin'),
    'cis-2-Pentene':       ('C5', 'Olefin'),
    'Other C5':            ('C5', 'Olefin'),
    'n-Hexane':            ('C6', 'Paraffin'),
    'Other C6':            ('C6', 'Olefin'),
    'Benzene':             ('C6', 'BTX'),
    'Other C7':            ('C7', 'Olefin'),
    'Toluene':             ('C7', 'BTX'),
}

# Carbon row categories for aggregation
CARBON_ROWS = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'Autres']

# Chemical family categories
FAMILIES = ['Paraffin', 'Olefin', 'BTX']

# HVC (High Value Chemicals) categories for small summary table
HVC_CATEGORIES = [
    ("C2 Olefin", "C2", "Olefin"),
    ("C3 Olefin", "C3", "Olefin"),
    ("C4 Olefin", "C4", "Olefin"),
    ("BTX", ["C6", "C7"], "BTX")  # Multi-carbones pour C6 + C7
]