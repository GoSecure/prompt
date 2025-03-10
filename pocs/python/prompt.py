#!/usr/bin/python3
import os
import sys
import ast
import json
import platform
import http.client

# Argument handling
if not len(sys.argv) > 1:
    print("Usage: prompt.py [prompt]")
    exit()
input_prompt = sys.argv[1]

# Define base prompt
prompt = f'''I am going to give you an order, and you will answer only by using python code.
For example, if I ask you to list a system folder, you will write python code that list the system folder and prints the output.    
Constraints:
- Always print the result if there is one. If your result is a list, print every element, one by line.
- Use only native python module (no pip install)
- The python code will be running on a {platform.system()} system
The order is: {input_prompt}'''

# OpenAI API host and endpoint
HOST = "api.openai.com"
ENDPOINT = "/v1/chat/completions"
MODEL  = 'gpt-4o' # choose you model, such as: gpt-4o, gpt-4o-mini, o1-mini...
API_KEY = "[YOUR API KEY HERE]"

# Define the function to send a request to GPT-4o
def send_prompt(prompt, model=MODEL):
    # Prepare request data
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    })

    # Establish connection and send request
    conn = http.client.HTTPSConnection(HOST)
    conn.request("POST", ENDPOINT, body=payload, headers=headers)

    # Get response
    response = conn.getresponse()
    if response.status != 200:
        print(f"Error: Received status code {response.status}")
        print(response.read().decode())

    data = response.read().decode()
    conn.close()

    # Parse and print response
    response_json = json.loads(data)
    return response_json["choices"][0]["message"]["content"]

# Verify if python code is valid
def verify_code(code):
    try:
        ast.parse(code) 
        return True
    except Exception as e:
        print(f"Code is invalid. Error: {e}")
        return False

# Function that mainly remove magic quotes added by chatgpt when giving code
def sanitize_code(code):
    code = code.replace('```python', '')
    code = code.replace('```', '')
    return code

# Main
if __name__ == '__main__':
    # Getting the generated code
    output = send_prompt(prompt)

    # Sanitize code
    output = sanitize_code(output)

    # Verify if code is valid python code
    if verify_code:
        # Executing code
        exec(output)

