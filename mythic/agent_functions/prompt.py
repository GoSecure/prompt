from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
import json, base64, ast
import http.client

# Function that mainly remove magic quotes added by chatgpt when giving code
def sanitize_code(code):
    code = code.replace('```python', '')
    code = code.replace('```', '')
    return code

# Verify if code is OK
# return {'status': True/False, 'reason': exception}
def verify_code(code):
    result={"status":False, "reason":str()}
    try:
        ast.parse(code)  # Try parsing the code
        result["status"] = True
    except Exception as e:
        result["status"] = False
        result["reason"] = str(e)
    return result

# Function to query OpenAI API
def ask_ai(prompt, model):
        # Specify your OpenAI API key here
        api_key = "[YOUR API KEY HERE]"

        # OpenAI API host and endpoint
        host = "api.openai.com"
        endpoint = "/v1/chat/completions"
        temperature = 0.7
        if model == "gpt-4o" or model == "gpt-4o-mini":
            temperature = 0.2 # more deterministic, better for coding
        elif model == "o1-mini":
            temperature = 1

        # Prepare request data
        headers_req = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        # Configure model and temperature
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        })

        # Establish connection and send request
        try:
            conn = http.client.HTTPSConnection(host)
            conn.request("POST", endpoint, body=payload, headers=headers_req)
        except:
            return f"[!] Error: Connection to host {host} failed\n"

        # Get response
        r = conn.getresponse()
        if r.status != 200:
            return f"[!] Error: Received status code {r.status}\n" + r.read().decode()
        d = r.read().decode()
        conn.close()

        # Parse and print response
        response_json = json.loads(d)
        outputcode = response_json["choices"][0]["message"]["content"]

        # Sanitize the code in case AI added magic quotes
        outputcode = sanitize_code(outputcode)

        # Return generated code
        return outputcode


# medusa arguments
class promptArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="prompt",
                type=ParameterType.String,
                parameter_group_info=[ParameterGroupInfo(
                    required=True,
                    ui_position=1
                )],
                description="Prompt that will generate python code",
            ),
            CommandParameter(
                name="model",
                choices=["gpt-4o", "gpt-4o-mini", "gpt-4.5-preview", "o1-mini", "o1" , "o3-mini"],
                type=ParameterType.ChooseOne,
                parameter_group_info=[ParameterGroupInfo(
                    required=True,
                    ui_position=2
                )],
                description="ChatGPT model",
            ),
            CommandParameter(
                name="cmdless",
                choices=["True", "False"],
                type=ParameterType.ChooseOne,
                parameter_group_info=[ParameterGroupInfo(
                    required=True,
                    ui_position=3
                )],
                description="Avoid to execute os command using the os or subprocess module",
            ),
            CommandParameter(
                name="obfuscation",
                choices=["False", "True"],
                type=ParameterType.ChooseOne,
                parameter_group_info=[ParameterGroupInfo(
                    required=True,
                    ui_position=4
                )],
                description="Randomize all variable and function names",
            ),
        ]

    async def parse_arguments(self):
        if self.command_line[0] != "{":
            pieces = self.command_line.split(" ")
            if len(pieces) == 4:
                self.add_arg("prompt", pieces[0])
                self.add_arg("model", pieces[1])
                self.add_arg("cmdless", pieces[2])
                self.add_arg("obfuscation", pieces[2])
            else:
                raise Exception("Wrong number of parameters, should be 4")
        else:
            self.load_args_from_json_string(self.command_line)


# Command details
class promptCommand(CommandBase):
    cmd = "prompt"
    needs_admin = False
    help_cmd = "prompt [string]"
    description = "Order to give to the agent. For example: list local users"
    version = 1
    author = "GoSecure"
    attackmapping = []
    argument_class = promptArguments
    attributes = CommandAttributes(
        supported_python_versions=["Python 3.8"],
        supported_os=[SupportedOS.MacOS, SupportedOS.Windows, SupportedOS.Linux ],
    )
    
    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        # Init the response object
        response = PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=True,
        )

        # Init outputs
        response.Stdout = "\n" 
        response.Stderr = "\n" 

        # Get initial prompt for user input
        prompt      = taskData.args.get_arg("prompt")
        model       = taskData.args.get_arg("model") 
        cmdless     = taskData.args.get_arg("cmdless") 
        obfuscation = taskData.args.get_arg("obfuscation") 

        # Get OS to refine the prompt
        OS = taskData.Payload.OS

        # Building the prompt from user input
        baseprompt = f'''I am going to give you an order, and you will answer only by using python code.\nFor example, if I ask you to list a system folder, you will write python code that list the system folder and prints the output.
Constraints:
- Always print the result if there is one. If your result is a list, print every element, one by line.
- Use only native python module (no pip install)
- Do not write any "main" function, just run the code directly
- The python code will be running on a {OS} system
'''
        if obfuscation == "True":
            baseprompt += f"- For any variable or function or class, or object you define, name it by using words that are fruit, animal, or plant. Make sure to use words without any special character\n"
        if cmdless == "True":
            baseprompt += f'- Do not use any system shell command, or use any local system executables.'
            if OS == "Windows":
                baseprompt += " Prefer using ctypes or winreg for example."
        baseprompt += f'\nThe order is: {prompt}'

        # Stdout output
        response.Stdout += f"[*] Model:\n{model}\n\n[*] Full prompt:\n{baseprompt}\n\n"

        # GUI print
        await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
        TaskID=taskData.Task.ID,
        Response="Asking AI to generate code...\n".encode()
        ))
        
        # making chatgpt request
        outputcode = ask_ai(baseprompt, model)
        codestatus = verify_code(outputcode); status = codestatus["status"]; reason = codestatus["reason"]
        if not status:
            response.Stderr +=  f"[!] Generated code was invalid python code:\n{outputcode}\n"
            response.Stderr +=  f"[!] Reason:\n{reason}\n\n"
            response.Success = False
            return response

        # adding generated code to stderr
        response.Stdout += f"[*] Generated code: {outputcode}\n\n"

        # GUI print
        await SendMythicRPCResponseCreate(MythicRPCResponseCreateMessage(
        TaskID=taskData.Task.ID,
        Response="Code generated. Send it back to the agent...\n".encode()
        ))

        # Send data back to the agent (by modifying its own user input parameter)
        taskData.args.set_arg("prompt", outputcode)

        # C2 display 
        response.DisplayParams = f'"{prompt}"'

        # Save the full prompt and the generated code to stderr
        response.Stdout += "[!] Warning:\n"
        return response


    # Process agent's reponse
    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        resp = PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
        return resp

