# Constants for ChromeleonOnlinePermanent (chromeleon_online_permanent.py)
# Mapping of chemical compounds to their carbon number and chemical family

COMPOUND_MAPPING = {
    'Helium':         ('C0', 'Autres'),   # gaz noble, aucun carbone
    'Hydrogen':       ('C0', 'Autres'),   # dihydrogène, aucun carbone
    'Carbon dioxide': ('C1', 'Autres'),   # oxyde de carbone (CO2), non hydrocarbure
    'Methane':        ('C1', 'Paraffin'),   # alcane saturé le plus simple
    'CO':             ('C1', 'Autres'),   # monoxyde de carbone, non hydrocarbure
}

# Carbon row categories for aggregation
CARBON_ROWS = ['C0', 'C1', 'C2', 'Autres']

# Chemical family categories
FAMILIES = ['Paraffin', 'Olefin', 'BTX gas', 'Autres']