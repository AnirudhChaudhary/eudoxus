"""
Run Eudoxus on the examples and then ask the LLM whether it thinks the output model matches the original.

1. Run Eudoxus and get the file outputs
2. Take the file outputs and then wrap it in an LLM call
"""


import subprocess
import os
import time

def run():
    files = ["data/BaierKatoen/bk-ex2_17-part2.txt"]
    # files = []
    
    for folder in ["data/BaierKatoen", "data/HuthRyan", "data/LeeSeshia"]:
        for file in [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".txt")]:
            if files:
                if file in files:
                    e = run_file(file)
            else:
                e = run_file(file)
            
            # if error first time, run again
            if e == "error":
                run_file(file)
    print("done running")

def run_file(file):
    date = time.strftime("%m-%d-%Y-%H-%M")
    print("starting file: ", file)
    filename = os.path.basename(file)
    output = os.path.join("results", date, filename + ".ucl")
    summary = os.path.join("results", date, filename)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    # gpt-3.5-turbo-0125
    # "gpt-4-turbo-2024-04-09"
    try:
        with open(summary, "wb") as f:
            f.write(subprocess.run([
                "eudoxus",
                "--iterations", "5",
                file,
                "--output", output,
                "--model", "gpt-3.5-turbo-0125"
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True).stdout)
    except subprocess.CalledProcessError as e:
        print("Command failed with error:")
        print("stderr:", e.stderr)
        print("Return code:", e.returncode)
        try:
            print("stderr: ", subprocess.STDOUT)
        except:
            print("could not print error message")    
        return "error"
    except Exception as e:
        print("An unexpected error occurred.")
        print(str(e))
        return "error"
    


if __name__ == "__main__":
    run()

