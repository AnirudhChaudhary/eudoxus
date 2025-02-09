def get_property_gen_prompt(task):
    """ Returns property generating prompt """
    prompt = "You are an expert in formal methods, specializing in generating system properties and specifications. Your task is to generate invariants and LTL specifications for a system based on its natural language description.\n"

    prompt += "Guidelines:\n \
    1. Invariants: Identify properties that must hold true in all states of the system. These are conditions that are always true regardless of the system's execution path.\n \
    2. LTL Specifications: Formulate Linear Temporal Logic properties that capture temporal behaviors of the system. These properties should describe relationships or constraints that hold over time (e.g., safety, liveness, fairness).\n"

    prompt += "Input: \n \
        I will provide you witha  natural language description of the system, including: \n \
            * The components and their interactions. \
            * The desired behaviors of the system. \
            * Any constraints, safety, or performance requirements.\n"

    prompt += "Output: \n \
        * A list of invariants expressed in mathematical notation \
        * A list of LTL Specifications in standard syntax (e.g., G (p -> Fq), where G is 'Globally' and F is 'Eventually'). \
        * Explanations for each property, detailing why it is relevant and representative of the system.\n"

    prompt += task
    
    return prompt

def get_llm_response(task):
    prompt = get_property_gen_prompt(task)
    message_to_send =[
        {"role": "user", "content": prompt}
    ]
    response = OpenAI().chat.completions.create(
        model="gpt-4-turbo",
        messages=message_to_send,
        temperature=1
    )

    return f"Prompt: {prompt} \n" + response.choices[0].message.content

if __name__ == "__main__":
    import subprocess
    import os
    import time
    import openai  # Assuming OpenAI API is being used for the LLM call
    from openai import OpenAI

    # Set up the OpenAI API key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    date = time.strftime("%m-%d-%Y-%H-%M")
    
    for folder in ["data/BaierKatoen", "data/HuthRyan", "data/LeeSeshia"]:
        for file in [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".txt")]:
            print("starting file: ", file)
            filename = os.path.basename(file)
            filename = filename.strip(".txt")
            summary = os.path.join("results", date, filename + ".md")
            os.makedirs(os.path.dirname(summary), exist_ok=True)
            with open(file, "r") as f:
                task = f.read()
            # gpt-3.5-turbo-0125
            # "gpt-4-turbo-2024-04-09"
            try:
                with open(summary, "w") as f:

                    f.write(get_llm_response(task))

            except subprocess.CalledProcessError as e:
                print("Command failed with error:")
                print("stderr:", e.stderr)
                print("Return code:", e.returncode)
                continue
            except Exception as e:
                print("An unexpected error occurred.")
                print(str(e))
                continue
            break
        break
    print("done")