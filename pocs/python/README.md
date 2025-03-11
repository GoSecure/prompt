### Description
Python code PoC that reflectively executes AI-generated code (requested via the OpenAI API in this example).

### Requirements
- `python3`
- An OpenAI API key

### Usage
1. Set your OpenAI API key in the `API_KEY` variable in the `prompt.py` file
2. Usage: `prompt.py [prompt]`

### Example output
```
>> prompt.py 'list the content of the /etc/hosts file'
[*] Asking AI to generate code...
[*] Executing reflectively...

127.0.0.1	localhost
127.0.1.1	kali

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
```

