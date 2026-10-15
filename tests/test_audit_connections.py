"""Furniture copies are separate items even when they share one profile."""
import audit_connections


def instance(id, part, design=None, group='Furniture'):
    inst={'id':id,'part':part,'group':group}
    if design is not None:inst['design_part']=design
    return inst


def test_complete_bookcase_copies_are_separate_assemblies():
    copies=[instance(f'BC1-{n:02}','BC1','BC1') for n in range(1,5)]
    data={'parts':{'BC1':{'category':'Furniture','boxes':[{'size':[1,2,3]}]}},'instances':copies}
    assert audit_connections.furniture_assemblies(data)=={i['id']:[i] for i in copies}


def test_shared_and_legacy_loose_books_are_excluded():
    ids=('BK1','BK_library','WL1','GL01')
    data={'parts':{pid:{'category':'Furniture'} for pid in ids},
          'instances':[instance(f'{pid}-01',pid,pid) for pid in ids]}
    assert audit_connections.furniture_assemblies(data)=={}


def test_separate_boards_keep_their_furniture_family_after_profile_sharing():
    boards=[instance('shared-01','shared','WP1'),instance('shared-02','shared','WP2'),
            instance('shared-03','shared','WP3'),instance('shared-04','shared','K2A'),
            instance('shared-05','shared','K7A')]
    data={'parts':{'shared':{'category':'Furniture'}},'instances':boards}
    assert audit_connections.furniture_assemblies(data)=={'WP':boards[:3],'K2':boards[3:]}


def test_audit_only_groups_installed_furniture():
    data={'parts':{'seat':{'category':'Furniture'},'wall':{'category':'Walls'}},
          'instances':[instance('seat-01','seat',group='Tools'),instance('wall-01','wall')]}
    assert audit_connections.furniture_assemblies(data)=={}
