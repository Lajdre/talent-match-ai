import asyncio
import json
import statistics
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from result import Err

from src.services.openai_service import get_openai_chat
from src.services.query_service import process_query


class JudgeResult(BaseModel):
  passed: bool = Field(description="Whether the system answer matches the ground truth")
  reason: str = Field(description="Short justification for the decision")


JUDGE_PROMPT = textwrap.dedent("""
  You are an evaluation system.

  You will be given:
  - A natural language question
  - The ground truth answer
  - A system-generated answer

  Determine whether the system answer is CORRECT.

  Evaluation rules:
  - The system answer must match the ground truth in meaning.
  - Paraphrasing is allowed.
  - Ordering of names or items does not matter.
  - If the question asks for a count, the count must be correct.
  - If the question asks for a list, all required items must be present.
  - Missing required items means failure.
  - Adding incorrect or hallucinated items means failure.
  - Vague or non-committal answers mean failure.

  Make a strict decision.

  Question:
  {question}

  Ground truth:
  {ground_truth}

  System answer:
  {system_answer}
""")


def load_ground_truths(path: Path) -> list[dict[str, Any]]:
  with path.open("r", encoding="utf-8") as f:
    return json.load(f)


def build_naive_rag():
  pdf_paths = []
  for folder in ["data/programmers", "data/RFP"]:
    pdf_paths.extend(Path(folder).glob("*.pdf"))

  documents = []
  for pdf in pdf_paths:
    loader = PyPDFLoader(str(pdf))
    documents.extend(loader.load())

  splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
  )
  chunks = splitter.split_documents(documents)

  vectordb = Chroma.from_documents(
    documents=chunks,
    embedding=OpenAIEmbeddings(),
    persist_directory=".chroma_naive_rag",
  )

  retriever = vectordb.as_retriever(search_kwargs={"k": 5})

  prompt = ChatPromptTemplate.from_messages(
    [
      (
        "system",
        textwrap.dedent("""
          You are an assistant answering questions using the provided context.
          Use ONLY the context to answer. If the answer cannot be determined from the
          context, say so clearly.

          Context:
          {context}
        """),
      ),
      ("human", "{question}"),
    ]
  )

  llm = ChatOpenAI(temperature=0)

  def format_docs(docs):
    return "\n\n".join(
      f"[Document {i + 1}]\n{doc.page_content}" for i, doc in enumerate(docs)
    )

  rag_chain = (
    {
      "context": retriever | format_docs,
      "question": RunnablePassthrough(),
    }
    | prompt
    | llm
    | StrOutputParser()
  )

  return rag_chain


async def judge_answer(
  question: str,
  ground_truth: str,
  system_answer: str,
) -> JudgeResult:
  llm_result = get_openai_chat(temperature=0)
  if isinstance(llm_result, Err):
    raise RuntimeError("Failed to initialize judge LLM")

  structured_llm = llm_result.ok().with_structured_output(JudgeResult)

  prompt = JUDGE_PROMPT.format(
    question=question,
    ground_truth=ground_truth,
    system_answer=system_answer,
  )

  result = await structured_llm.ainvoke(prompt)

  if isinstance(result, JudgeResult):
    return result

  return JudgeResult.model_validate(result)


async def main() -> None:
  graph_times = []
  rag_times = []
  ground_truths = load_ground_truths(Path("./example_data/questions.json"))
  rag_chain = build_naive_rag()

  results = []
  graph_passed = 0
  rag_passed = 0

  for item in ground_truths:
    question = item["question"]
    truth = str(item["answer"])

    start = time.perf_counter()
    graph_result = await process_query(question)
    graph_time_ms = (time.perf_counter() - start) * 1000
    graph_answer = graph_result.get("answer", "No answer")

    start = time.perf_counter()
    rag_answer = rag_chain.invoke(question)
    rag_time_ms = (time.perf_counter() - start) * 1000

    graph_judge = await judge_answer(question, truth, graph_answer)
    rag_judge = await judge_answer(question, truth, rag_answer)

    graph_passed += int(graph_judge.passed)
    rag_passed += int(rag_judge.passed)

    graph_times.append(graph_time_ms)
    rag_times.append(rag_time_ms)

    results.append(
      {
        "question": question,
        "ground_truth": truth,
        "graph_rag": {
          "answer": graph_answer,
          "passed": graph_judge.passed,
          "reason": graph_judge.reason,
          "response_time_ms": round(graph_time_ms, 2),
        },
        "naive_rag": {
          "answer": rag_answer,
          "passed": rag_judge.passed,
          "reason": rag_judge.reason,
          "response_time_ms": round(rag_time_ms, 2),
        },
      }
    )

  graph_avg = statistics.mean(graph_times)
  graph_median = statistics.median(graph_times)

  rag_avg = statistics.mean(rag_times)
  rag_median = statistics.median(rag_times)

  report = {
    "metadata": {
      "run_at": datetime.now().isoformat(),
      "total_questions": len(ground_truths),
    },
    "summary": {
      "graph_rag_passed": graph_passed,
      "naive_rag_passed": rag_passed,
      "graph_rag_pass_rate": graph_passed / len(ground_truths),
      "naive_rag_pass_rate": rag_passed / len(ground_truths),
      "latency_ms": {
        "graph_rag": {
          "average": round(graph_avg, 2),
          "median": round(graph_median, 2),
        },
        "naive_rag": {
          "average": round(rag_avg, 2),
          "median": round(rag_median, 2),
        },
      },
    },
    "results": results,
  }

  with open("rag_comparison_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

  print("Comparison complete.")
  print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
  asyncio.run(main())
