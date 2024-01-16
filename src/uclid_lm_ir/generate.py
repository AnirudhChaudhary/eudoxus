import ast
import inspect
import os

import chromadb
from openai import OpenAI

from .module import Module
from .printer import print_uclid5
from .utils import generator_log, llm_log


def chat_gpt(prompt, engine="gpt-4-0613"):
    if os.environ["OPENAI_API_KEY"]:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    else:
        llm_log("OPENAI_API_KEY not set. Returning empty string.")
        return ""
    response = client.chat.completions.create(
        model=engine, messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def get_api_description() -> str:
    source = inspect.getsource(Module)
    index = source.find("def __str__")
    source = source[:index]
    # remove trailing new lines
    source = source.rstrip()
    return source


def get_sketch_prompt(task) -> str:
    """Returns the sketch prompt for the GPT-4 API."""

    generator_log("Getting sketch prompt...")

    if task.endswith("."):
        task = task[:-1]

    prompt = "Extend the `Module` class below to complete the following task:"
    prompt += " " + task + ". Reply with your code inside one unique code block."
    module_class = "```python3\n" + get_api_description() + "\n```\n"
    prompt += f"\n\n{module_class}\n```python3\n#TODO\n"

    generator_log("Prompt:", prompt)

    return prompt


def extract_code(output) -> str:
    """Extracts the code from the GPT-4 API response."""
    generator_log("Extracting code...")

    # replace any occurrences of "``````" with "```"
    output = output.replace("``````", "```")

    end_index = output.rfind("```")
    before_start = output.rfind("```", 0, end_index)
    # find the newline after the index
    start_index = output.find("\n", before_start + 1)

    # extract the code
    code = output[start_index:end_index]
    # remove trailing new lines
    code = code.rstrip()

    generator_log("Code:", code)
    return code


def process_code(code) -> str:
    """Processes the code to remove unwanted lines."""
    generator_log("Processing code...")

    parsed = ast.parse(code)
    # extract all the classes and nothing else
    parsed.body = [node for node in parsed.body if isinstance(node, ast.ClassDef)]
    output = print_uclid5(parsed)
    # remove empty lines
    output = "\n".join([line for line in output.split("\n") if line.strip()])

    generator_log("Processed code:", output)
    return output


def sketch_api(task, engine="gpt-4-0613"):
    """Generates code for a given task using the GPT-4 API."""
    generator_log("Generating code...")

    prompt = get_sketch_prompt(task)

    response = chat_gpt(prompt, engine)
    llm_log("Response:", response)

    code = extract_code(response)
    code = process_code(code)
    return code


def find_nearest_neighbours(code_with_holes, examples, k):
    """
    Finds the k nearest neighbours to the code with holes in the examples
    """
    generator_log("Finding nearest neighbours...")

    if not examples:
        return []

    client = chromadb.Client()
    collection = client.create_collection("uclid5-examples")

    # find all the files in examples that end in .ucl
    examples = [file for file in examples.glob("**/*.ucl")]
    documents = []
    ids = []

    for example in examples:
        with open(example, "r") as f:
            code = f.read()
            documents.append(code)
            ids.append(str(example))

    collection.add(documents=documents, ids=ids)

    results = collection.query(
        query_texts=[code_with_holes],
        n_results=k,
        include=["documents"],
    )

    generator_log("Nearest neighbours:", results["ids"][0])

    return results["documents"][0]


def get_complete_prompt(code_with_holes, examples, k):
    generator_log("Getting sketch prompt...")

    nearest_neighbours = find_nearest_neighbours(code_with_holes, examples, k)

    prompt = ""

    for neighbour in nearest_neighbours:
        prompt += "This is an example of a UCLID5 model: \n```uclid5\n"
        prompt += neighbour + "\n```\n\n"

    prompt += "\nFix the UCLID5 code below by replacing every occurrence of `??` "
    prompt += f"with the correct value:\n```uclid5\n{code_with_holes}\n```\n"

    generator_log("Prompt:", prompt)
    return prompt


def complete_api(code_with_holes, examples=None, k=1, engine="gpt-4-0613") -> str:
    """Ask the llm to remove the question marks."""
    generator_log("Asking the llm to remove the question marks...")

    if "??" not in code_with_holes:
        return code_with_holes

    prompt = get_complete_prompt(code_with_holes, examples, k)

    response = chat_gpt(prompt, engine)

    llm_log("Response:", response)
    code_with_holes = extract_code(response)
    return code_with_holes
