#!/usr/bin/env python3
"""Run unchanged campaign tests with explicit historical policy verification."""
import importlib.util,json,sys,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('h',Path(__file__).with_name('museum-expansion-policy-history-20261007.py'));h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_museum_expansion*py');adapters=[]
for name,module in list(sys.modules.items()):
 if name.startswith('test_museum_expansion'):adapters+=h.install(module)
print(json.dumps(dict(historical_policy_receipt=str(h.RECEIPT),adapted_validators=len(adapters),test_databases=False)),flush=True)
result=unittest.TextTestRunner(verbosity=1).run(suite);sys.exit(not result.wasSuccessful())
