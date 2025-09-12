# Constants for ChromeleonOnline (chromeleon_online.py)
# Mapping of chemical compounds to their carbon number and chemical family

COMPOUND_MAPPING = {
    'Methane':             ('C1', 'Linear'),
    'Ethane':              ('C2', 'Linear'),
    'Ethylene':            ('C2', 'Olefin'),
    'Propane':             ('C3', 'Linear'),
    'Cyclopropane':        ('C3', 'Autres'),
    'Propylene':           ('C3', 'Olefin'),
    'Propadiene':          ('C3', 'Olefin'),
    'iso-Butane':          ('C4', 'Linear'),
    'Acetylene':           ('C2', 'Autres'),
    'n-Butane':            ('C4', 'Linear'),
    'trans-2-Butene':      ('C4', 'Olefin'),
    '1-Butene':            ('C4', 'Olefin'),
    'iso-Butylene':        ('C4', 'Olefin'),
    'cis-2-Butene':        ('C4', 'Olefin'),
    'iso-Pentane':         ('C5', 'Olefin'),
    'n-Pentane':           ('C5', 'Linear'),
    '1,3-Butadiene':       ('C4', 'Olefin'),
    'trans-2-Pentene':     ('C5', 'Olefin'),
    '2-methyl-2-Butene':   ('C4', 'Olefin'),
    '1-Pentene':           ('C5', 'Olefin'),
    'cis-2-Pentene':       ('C5', 'Olefin'),
    'Other C5':            ('C5', 'Olefin'),
    'n-Hexane':            ('C6', 'Linear'),
    'Other C6':            ('C6', 'Olefin'),
    'Benzene':             ('C6', 'BTX gas'),
    'Other C7':            ('C7', 'Olefin'),
    'Toluene':             ('C7', 'BTX gas'),
}

# Carbon row categories for aggregation
CARBON_ROWS = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'Autres']

# Chemical family categories
FAMILIES = ['Linear', 'Olefin', 'BTX gas']

# HVC (High Value Chemicals) categories for small summary table
HVC_CATEGORIES = [
    ("C2 Olefin", "C2", "Olefin"),
    ("C3 Olefin", "C3", "Olefin"), 
    ("C4 Olefin", "C4", "Olefin"),
    ("C6 BTX gas", "C6", "BTX gas")
]