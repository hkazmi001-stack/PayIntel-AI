import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
from rfp_analyzer import analyze
st.set_page_config(page_title='PayIntel AI',layout='wide')
st.title('PayIntel AI — Historical RFP Portfolio Gap Analysis')
st.caption('KSBL university prototype • Synthetic data only • Advisory, not predictive')
def read_file(f):
    name=f.name.lower();data=f.read()
    if name.endswith('.pdf'):
        import fitz
        with fitz.open(stream=data,filetype='pdf') as doc:return '\n'.join(page.get_text() for page in doc)
    if name.endswith('.docx'):
        from docx import Document
        return '\n'.join(x.text for x in Document(BytesIO(data)).paragraphs)
    return data.decode('utf-8',errors='replace')
st.sidebar.header('Documents')
rfp_upload=st.sidebar.file_uploader('Historical RFPs',type=['txt','pdf','docx'],accept_multiple_files=True)
portfolio_upload=st.sidebar.file_uploader('Existing portfolio',type=['txt','pdf','docx'],accept_multiple_files=True)
demo=st.sidebar.checkbox('Use 15 bundled demo RFPs and 5 products',value=True)
if st.sidebar.button('Analyze RFPs',type='primary'):
    if demo:
        root=Path(__file__).parent
        rfps={f.name:f.read_text(encoding='utf-8') for f in sorted((root/'data/rfps').glob('*.txt'))}
        portfolio={f.name:f.read_text(encoding='utf-8') for f in sorted((root/'data/portfolio').glob('*.txt'))}
    else:
        rfps={f.name:read_file(f) for f in rfp_upload}
        portfolio={f.name:read_file(f) for f in portfolio_upload}
    if not rfps or not portfolio:st.error('Upload both RFPs and portfolio documents, or enable demo data.')
    else:st.session_state['results']=(rfps,portfolio,analyze(rfps,portfolio))
if 'results' not in st.session_state:
    st.info('Select Analyze RFPs in the sidebar to run the bundled demo.')
else:
    rfps,portfolio,rows=st.session_state['results'];df=pd.DataFrame(rows)
    missing=df[df['Status']=='Missing'] if not df.empty else df
    a,b,c=st.columns(3);a.metric('RFPs reviewed',len(rfps));b.metric('Capabilities requested',len(df));c.metric('Portfolio gaps',len(missing))
    st.subheader('Historical capability demand')
    if not df.empty:
        st.bar_chart(df.set_index('Capability')['RFP Count'])
        st.subheader('Portfolio fit and evidence')
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.subheader('Suggested portfolio additions')
        if missing.empty:st.success('No documented gaps detected in the requested capability taxonomy.')
        for _,r in missing.iterrows():st.markdown(f"**{r['Capability']}** — requested in **{r['RFP Count']} of {len(rfps)}** RFPs. Sources: {r['RFP Sources']}. Advisory recommendation only.")
        st.download_button('Download CSV',df.to_csv(index=False).encode(),file_name='payintel_results.csv',mime='text/csv')
        out=BytesIO()
        with pd.ExcelWriter(out,engine='openpyxl') as writer:df.to_excel(writer,index=False,sheet_name='Gap Analysis')
        st.download_button('Download Excel',out.getvalue(),file_name='payintel_results.xlsx')
        with st.expander('Optional AI summary (local Ollama)'):
            if st.button('Generate summary with Ollama'):
                try:
                    import requests
                    facts='\n'.join(f"{r['Capability']}: {r['RFP Count']} RFPs, {r['Status']}" for r in rows)
                    prompt='Summarize these VERIFIED historical counts. Do not invent numbers or make predictions. Recommendations are advisory only.\n'+facts
                    response=requests.post('http://localhost:11434/api/generate',json={'model':'llama3.2:3b','prompt':prompt,'stream':False,'options':{'num_predict':250}},timeout=90)
                    response.raise_for_status();st.write(response.json()['response'])
                except Exception as exc:st.warning(f'Ollama unavailable or timed out: {exc}. Deterministic analysis remains valid.')

        st.divider()
        st.subheader('RAG Evidence Assistant — ChromaDB + Ollama')
        st.caption('Retrieves passages from the currently analyzed RFPs and portfolio documents. The historical demand counts above are unchanged.')
        if st.button('Build RAG index from current documents'):
            try:
                from rag_engine import build_retriever
                with st.spinner('Creating local embeddings and ChromaDB index (first run downloads the embedding model)...'):
                    docs={f'RFP/{name}':text for name,text in rfps.items()}
                    docs.update({f'Portfolio/{name}':text for name,text in portfolio.items()})
                    st.session_state['rag_index']=build_retriever(docs)
                    st.session_state['rag_doc_names']=tuple(sorted(docs))
                st.success(f'Indexed {len(docs)} documents. You can now ask evidence questions.')
            except Exception as exc:
                st.error(f'Could not build RAG index: {exc}')
        question=st.text_input('Ask a question about historical RFP demand or portfolio evidence',placeholder='Which RFPs mention QR acquiring?')
        if st.button('Retrieve evidence and ask Ollama'):
            if 'rag_index' not in st.session_state:
                st.warning('Click Build RAG index first.')
            elif not question.strip():
                st.warning('Enter a question first.')
            else:
                try:
                    from rag_engine import retrieve
                    hits=retrieve(st.session_state['rag_index'],question,k=5)
                    st.markdown('**Retrieved evidence (inspect these sources):**')
                    for i,hit in enumerate(hits,1):
                        with st.expander(f"{i}. {hit['source']}",expanded=i==1):
                            st.text(hit['excerpt'])
                    import requests
                    evidence='\n\n'.join(f"[{i}] {h['source']}: {h['excerpt']}" for i,h in enumerate(hits,1))
                    prompt=("Answer ONLY using the source passages below. Cite source filenames in your answer. "
                            "If evidence is insufficient, say so. Do not invent demand counts, product support, or future forecasts. "
                            "For authoritative demand counts, use the dashboard above.\n\nQuestion: " + question + "\n\nSources:\n" + evidence)
                    with st.spinner('Ollama is preparing an evidence-grounded response...'):
                        response=requests.post('http://localhost:11434/api/generate',json={
                            'model':'llama3.2:3b','prompt':prompt,'stream':False,
                            'options':{'num_predict':240,'num_ctx':4096}},timeout=120)
                        response.raise_for_status()
                    st.markdown('**Ollama answer (verify against retrieved passages):**')
                    st.write(response.json().get('response','No answer returned.'))
                except Exception as exc:
                    st.warning(f'RAG/Ollama request failed: {exc}. Your existing analysis remains available.')
    else:st.warning('No recognized capabilities found. Review document contents and taxonomy.')
