from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage
import os
#from langchain.tools import tool
#@tool(description="Llama Index Tool for building and querying tariff data index")
class LlamaIndexTool:
    def __init__(self, persist_dir="data/index"):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)

    def build_index_from_db(self, df):
        """Create index from DB dataframe"""
        docs = [f"HSCode: {row['hscode']}, Goods: {row['goods_description']}, Duty: {row['duty_fee']}"
                for _, row in df.iterrows()]
        with open("data/temp/data.txt", "w") as f:
            f.write("\n".join(docs))

        documents = SimpleDirectoryReader("data/temp").load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=self.persist_dir)
        print("✅ Index built and persisted")

    def query_index(self, query: str):
        """Query the persisted index"""
        storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
        index = load_index_from_storage(storage_context)
        query_engine = index.as_query_engine()
        return query_engine.query(query)
