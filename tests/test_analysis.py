from rfp_analyzer import extract,analyze
def test_synonyms():assert 'Visa Tokenization' in extract('We need VTS integration')
def test_distinct_count():
 rows=analyze({'a':'QR acquiring and QR acquiring','b':'Merchant QR required'},{'p':'Google Pay'})
 assert next(r for r in rows if r['Capability']=='QR Acquiring')['RFP Count']==2
def test_supported():
 rows=analyze({'a':'Google Pay and Click to Pay'},{'p':'Google Pay'})
 assert {r['Capability']:r['Status'] for r in rows}=={'Google Pay':'Supported','Click to Pay':'Missing'}
