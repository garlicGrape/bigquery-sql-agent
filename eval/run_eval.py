"""Eval harness using LangSmith. Run with: uv run python eval/run_eval.py"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate

load_dotenv()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from app.graph import graph
from app.state import AgentState


DATASET_PATH = Path(__file__).parent / "dataset.jsonl"


def load_examples() -> list[dict]:
    with open(DATASET_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]


def run_agent(question: str) -> dict:
    initial: AgentState = {
        "question": question,
        "schema": "",
        "sql": "",
        "error": None,
        "attempts": 0,
        "result": None,
        "answer": "",
    }
    return graph.invoke(initial)


def sql_contains_checker(run, example) -> dict:
    """Checks that generated SQL contains all expected substrings."""
    sql = (run.outputs or {}).get("sql", "").upper()
    expected = example.inputs.get("expected_contains", [])
    hits = [kw for kw in expected if kw.upper() in sql]
    score = len(hits) / len(expected) if expected else 1.0
    return {"key": "sql_keyword_match", "score": score}


def answer_present_checker(run, example) -> dict:
    answer = (run.outputs or {}).get("answer", "")
    return {"key": "answer_present", "score": 1 if len(answer) > 20 else 0}


def main():
    ls_client = Client()
    examples = load_examples()

    dataset_name = "bigquery-sql-agent-citibike"
    if not ls_client.has_dataset(dataset_name=dataset_name):
        dataset = ls_client.create_dataset(dataset_name=dataset_name)
        ls_client.create_examples(
            inputs=[{"question": e["question"], "expected_contains": e["expected_contains"]} for e in examples],
            outputs=[{"description": e["description"]} for e in examples],
            dataset_id=dataset.id,
        )
        print(f"Created LangSmith dataset '{dataset_name}' with {len(examples)} examples.")
    else:
        print(f"Using existing LangSmith dataset '{dataset_name}'.")

    def agent_fn(inputs: dict) -> dict:
        result = run_agent(inputs["question"])
        return {"answer": result["answer"], "sql": result["sql"], "attempts": result["attempts"]}

    results = evaluate(
        agent_fn,
        data=dataset_name,
        evaluators=[sql_contains_checker, answer_present_checker],
        experiment_prefix="citibike-agent",
    )
    print(f"\nEval complete. Results: {results}")


if __name__ == "__main__":
    main()
