# Optional semantic retrieval; the baseline app remains functional offline.
from pathlib import Path

def build_retriever(documents):
    import chromadb
    from sentence_transformers import SentenceTransformer
    model=SentenceTransformer('all-MiniLM-L6-v2')
    client=chromadb.Client()
    collection=client.get_or_create_collection('payintel')
    names=list(documents)
    if not names:return None
    texts=[documents[n] for n in names]
    vectors=model.encode(texts).tolist()
    collection.upsert(ids=[str(i) for i in range(len(names))],embeddings=vectors,documents=texts,metadatas=[{'filename':n} for n in names])
    return (collection,model)

def retrieve(index,query,k=3):
    if index is None:return []
    collection,model=index
    result=collection.query(query_embeddings=model.encode([query]).tolist(),n_results=k)
    return [{'source':m['filename'],'excerpt':d[:500]} for m,d in zip(result['metadatas'][0],result['documents'][0])]
