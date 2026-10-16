#!/usr/bin/env python3
"""Reuse the established batch-251 gates for three version-resolved icons."""
from pathlib import Path
src=Path(__file__).with_name('continuous-warsaw-000251-prepare.py').read_text()
src=src.replace('continuous-warsaw-batch-000251.py','continuous-warsaw-batch-000252.py')
start=src.index('observations={')
end=src.index('\nfiles=[]; decisions=[]',start)
observations="""observations={
'498663':'Original and derivative individually viewed. Complete rectangular icon with the Resurrection centrally and twelve surrounding feast scenes. Full supplied support and margins retained; inventory IK 50 MNW is visibly a distinct composition from the prior same-title version.',
'498667':'Original and derivative individually viewed. Complete rectangular Resurrection icon with two central resurrection registers and surrounding figures. Full supplied support retained; inventory IK 53 MNW and its composition differ from prior IK 168 MNW.',
'498653':'Original and derivative individually viewed. Complete rectangular Resurrection icon with two central resurrection registers, upper scenes and a dark border. Full supplied support retained; inventory IK 42 MNW is visibly distinct from both IK 53 and prior IK 168 MNW.'}"""
src=src[:start]+observations+src[end:]
exec(compile(src,__file__,'exec'),globals())
