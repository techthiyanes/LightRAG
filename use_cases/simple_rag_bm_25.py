from typing import Any, List, Optional
import dotenv


from core.openai_client import OpenAIClient
from core.generator import Generator
from core.data_components import (
    RetrieverOutputToContextStr,
)

from core.string_parser import JsonParser
from core.component import Component, Sequential
from components.retriever.bm25_retriever import InMemoryBM25Retriever
from core.db import LocalDocumentDB
from core.data_classes import Document

dotenv.load_dotenv(dotenv_path=".env", override=True)


# TODO: RAG can potentially be a component itsefl and be provided to the users
class RAG(Component):

    def __init__(self):
        super().__init__()

        self.retriever_settings = {
            "top_k": 1,
        }
        self.generator_model_kwargs = {
            "model": "gpt-3.5-turbo",
            "temperature": 0.3,
            "stream": False,
        }

        retriever = InMemoryBM25Retriever(
            top_k=self.retriever_settings["top_k"],
        )

        self.db = LocalDocumentDB(
            retriever=retriever,
            retriever_output_processors=RetrieverOutputToContextStr(deduplicate=True),
        )

        # initialize generator
        self.generator = Generator(
            preset_prompt_kwargs={
                "task_desc_str": r"""
You are a helpful assistant.

Your task is to answer the query that may or may not come with context information.
When context is provided, you should stick to the context and less on your prior knowledge to answer the query.

Output JSON format:
{
    "answer": "The answer to the query",
}"""
            },
            model_client=OpenAIClient(),
            model_kwargs=self.generator_model_kwargs,
            output_processors=Sequential(JsonParser()),
        )
        self.tracking = {"vectorizer": {"num_calls": 0, "num_tokens": 0}}

    def build_index(self, documents: List[Document]):
        self.db.load_documents(documents)
        # self.db()  # transform the documents
        self.db.build_retrieve_index()

    def generate(self, query: str, context: Optional[str] = None) -> Any:
        if not self.generator:
            raise ValueError("Generator is not set")

        prompt_kwargs = {
            "context_str": context,
        }
        response = self.generator.call(input=query, prompt_kwargs=prompt_kwargs)
        return response

    def call(self, query: str) -> Any:
        context_str = self.db.retrieve(query)
        return self.generate(query, context=context_str)


if __name__ == "__main__":
    doc1 = Document(
        meta_data={"title": "Li Yin's profile"},
        text="My name is Li Yin, I love rock climbing" + "lots of nonsense text" * 500,
        id="doc1",
    )
    doc2 = Document(
        meta_data={"title": "Interviewing Li Yin"},
        text="lots of more nonsense text" * 250
        + "Li Yin is a software developer and AI researcher"
        + "lots of more nonsense text" * 250,
        id="doc2",
    )
    rag = RAG()
    print(rag)
    rag.build_index([doc1, doc2])
    print(rag.tracking)
    query = "What is Li Yin's profession?"

    response = rag.call(query)
    print(f"response: {response}")
