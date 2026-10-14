"""Manufacturing export tests: physical size, clean vectors, languages and whole parts."""
import copy,io
from collections import Counter
import pytest
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import supplier
from pdf_checks import pdf_paths
from pdf_assembly import combine

@pytest.fixture
def job():
    part={'id':'D01','name':'Window bar','thickness':3,'width':50,'height':5,'outer':[[0,0],[50,0],[50,5],[0,5]],'cuts':[],'holes':[],'starters':[{'x':7,'y':3,'diameter':2}],'quantity':1,'optional':False}
    hole={'id':'E08','name':'Roof catch','thickness':3,'width':38,'height':16,'outer':[[0,0],[38,0],[38,16],[0,16]],'cuts':[],'holes':[{'x':8,'y':8,'diameter':3.2,'depth':None}],'starters':[],'quantity':1,'optional':False}
    sheet={'id':'PLY3-01','thickness':3,'width':297,'height':420,'window':[10,10,287,410],'items':[{'part':'D01','copy':1,'x':10,'y':10,'angle':0},{'part':'E08','copy':1,'x':70,'y':10,'angle':0}]}
    return {'parts':{'D01':part,'E08':hole}},{'sheets':[sheet],'optional_sheets':[]}

@pytest.mark.parametrize('lang',['pl','en'])
def test_supplier_has_full_size_unannotated_vectors(job,tmp_path,lang):
    d,n=job;path,report=supplier.build(d,n,{},lang,tmp_path/f'{lang}.pdf')
    reader=PdfReader(path);meta=report['pages'][-1];p=reader.pages[meta['page']-1]
    assert (float(p.mediabox.width)/mm,float(p.mediabox.height)/mm)==pytest.approx((297,420),abs=.001)
    assert p.extract_text()=='' and len(p.images)==0 and not p.get('/Annots')
    curves=pdf_paths(p);assert len(curves)==3 # two outer profiles and one finished hole; no starter hole
    assert curves[0][0]=='polygon' and curves[0][1]==pytest.approx([10,10,60,10,60,15,10,15],abs=.0001)
    assert curves[-1][0]=='circle' and curves[-1][1]==pytest.approx([78,18,1.6],abs=.0001)
    assert report['optional_pieces']==0 and report['house_pieces']==2
    assert 'DO WYCENY' in reader.pages[0].extract_text() if lang=='pl' else 'FOR QUOTATION' in reader.pages[0].extract_text()
    assert reader.trailer['/Root']['/Lang']==lang

def test_polish_accents_survive_embedding(job,tmp_path):
    path,_=supplier.build(*job,{},'pl',tmp_path/'pl.pdf')
    text=''.join(p.extract_text() for p in PdfReader(path).pages)
    assert 'Załącznik' in text and 'Grubość' in text and 'KAŻDY ELEMENT' in text

def test_languages_share_exact_production_geometry(job,tmp_path):
    streams=[]
    for lang in ('pl','en'):
        path,r=supplier.build(*job,{},lang,tmp_path/f'{lang}.pdf')
        streams.append(PdfReader(path).pages[r['pages'][-1]['page']-1].get_contents().get_data())
    assert streams[0]==streams[1]

@pytest.mark.parametrize('change,error',[
    (lambda d,n:n['sheets'][0]['items'][0].update(y=408),'whole part'),
    (lambda d,n:n['sheets'][0]['items'].append(copy.deepcopy(n['sheets'][0]['items'][0])),'omit or duplicate'),
    (lambda d,n:n['sheets'][0]['items'].pop(),'omit or duplicate'),
    (lambda d,n:d['parts']['D01'].update(render_only=True),'View-only'),
    (lambda d,n:d['parts']['E08']['holes'][0].update(depth=1),'blind hole')])
def test_incomplete_split_or_unmanufacturable_job_is_rejected(job,tmp_path,change,error):
    d,n=copy.deepcopy(job);change(d,n)
    with pytest.raises(ValueError,match=error):supplier.build(d,n,{},'pl',tmp_path/'bad.pdf')

def test_machine_envelope_is_checked(job,tmp_path):
    with pytest.raises(ValueError,match='laser envelope'):
        supplier.build(*job,{'supplier':dict(supplier.DEFAULTS,maximum_sheet_mm=[100,200])},'pl',tmp_path/'bad.pdf')

def test_whole_roof_fits_a3_but_cannot_be_clipped_to_a4(job):
    data,nest=copy.deepcopy(job)
    roof=data['parts']['D01']
    roof.update(width=100.1308,height=387.2109,outer=[[0,0],[100.1308,0],[50.0654,387.2109]])
    sheet=nest['sheets'][0]
    supplier.sheets_for(data,nest,supplier.DEFAULTS)
    sheet.update(width=210,height=297,window=[10,10,200,287])
    with pytest.raises(ValueError,match='whole part'):
        supplier.sheets_for(data,nest,supplier.DEFAULTS)

def test_contents_links_account_for_inserted_pages(tmp_path):
    paths=[]
    for name,num in [('instructions',3),('supplier',2)]:
        p=tmp_path/f'{name}.pdf';c=canvas.Canvas(str(p))
        for j in range(num):c.drawString(40,700,f'{name} {j+1}');c.showPage()
        c.save();paths.append(p)
    sections=[{'path':paths[0],'title':'Instructions','entries':[{'title':f'Entry {j}','page':2} for j in range(65)]},{'path':paths[1],'title':'Supplier','entries':[]}]
    out=tmp_path/'complete.pdf';meta=combine(sections,out);reader=PdfReader(out)
    assert meta['contents_pages']==3 and len(reader.pages)==8
    assert 'instructions 1' in reader.pages[0].extract_text() and 'instructions 2' in reader.pages[4].extract_text()
    assert meta['sections'][-1]['first_page']==7
    links=sum(len(reader.pages[j].get('/Annots',[])) for j in (1,2,3));assert links==len(meta['entries'])
    assert all(e['complete_page']==5 for e in meta['entries'] if e['level']==1)
