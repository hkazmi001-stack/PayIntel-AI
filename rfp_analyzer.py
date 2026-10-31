import json,re
from pathlib import Path
CAPABILITIES=json.loads((Path(__file__).parent/'capabilities.json').read_text())
def has_term(text,term):
    return bool(re.search(r'(?<![\w])'+re.escape(term)+r'(?![\w])',text,re.I))
def extract(text):
    return {name for name,terms in CAPABILITIES.items() if any(has_term(text,t) for t in terms)}
def analyze(rfps,portfolio):
    # rfps and portfolio are mappings filename -> extracted plain text
    demands={c:[] for c in CAPABILITIES}
    for filename,content in rfps.items():
        for c in extract(content):demands[c].append(filename)
    supported={}
    for filename,content in portfolio.items():
        for c in extract(content):supported.setdefault(c,[]).append(filename)
    rows=[]
    for c,files in demands.items():
        if not files:continue
        rows.append({'Capability':c,'RFP Count':len(files),'Demand %':round(len(files)/max(1,len(rfps))*100,1),'Status':'Supported' if c in supported else 'Missing','RFP Sources':', '.join(files),'Portfolio Evidence':', '.join(supported.get(c,[]))})
    return sorted(rows,key=lambda r:(-r['RFP Count'],r['Capability']))
