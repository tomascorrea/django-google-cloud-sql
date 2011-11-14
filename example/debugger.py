def pdb():
    import pdb
    import sys 
    for attr in ('stdin', 'stdout', 'stderr'):
        setattr(sys, attr, getattr(sys, '__%s__' % attr))

    return pdb