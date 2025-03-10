using System;
using System.IO;
using System.Net;
using System.Reflection;
using System.Collections.Generic;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using System.Text.RegularExpressions;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.Emit;


namespace RoslynCompileAndExecute
{

    // Classes for deserializing the ChatGPT API response
    [DataContract]
    public class ChatMessage
    {
        [DataMember(Name = "role")]
        public string Role { get; set; }
        
        [DataMember(Name = "content")]
        public string Content { get; set; }
    }

    [DataContract]
    public class ChatChoice
    {
        [DataMember(Name = "index")]
        public int Index { get; set; }
        
        [DataMember(Name = "message")]
        public ChatMessage Message { get; set; }
        
        [DataMember(Name = "finish_reason")]
        public string FinishReason { get; set; }
    }

    [DataContract]
    public class ChatCompletionResponse
    {
        [DataMember(Name = "choices")]
        public ChatChoice[] Choices { get; set; }
    }


    class Program
    {

        // Remove leading/trailing ``` generate by chatgpt
        static string SanitizeSourceCode(string sourceCode)
        {
            if (string.IsNullOrEmpty(sourceCode))
                return sourceCode;

            // Remove leading ``` followed by an optional language name
            sourceCode = Regex.Replace(sourceCode, @"^```[\w]*\n?", "");

            // Remove trailing ```
            sourceCode = Regex.Replace(sourceCode, @"\n?```$", "");

            return sourceCode;
        }

        // Main
        static void Main(string[] args)
        {

            // Check if the user provided an argument
            if (args.Length < 1)
            {
                Console.WriteLine("Usage: prompt.exe <prompt>");
                return;
            }
            
            // Get the prompt from user input
            string inputprompt = args[0];

            // Build the main prompt
            string prompt = $@"I am going to give you an order, and you will answer only by using C# code.
For example, if I ask you to list a system folder, you will write C# code that list the system folder and prints the output.
Constraints:
- The code will be running on a Windows system
- Always print the result if there is one. If your result is a array of data, print every element, one by line.
- The main program class will be a public class called 'DynamicProgram'
- The main execution entry point will be a public static function called 'Execute'
- Use only native C# libraries, no external libraries to install
The order is: {inputprompt}";

            // Escaping prompt for JSON formatting
            string escapedprompt = prompt.Replace("\r\n", "\\n").Replace("\n", "\\n");

            // Configure ChatGPT request (set your API key here)
            string apiKey = "[YOUR API KEY HERE]"; 
            string url = "https://api.openai.com/v1/chat/completions";
            string jsonRequestBody = $@"{{
                ""model"": ""gpt-4o"",
                ""temperature"": 0.2,
                ""messages"": [
                    {{ ""role"": ""user"", ""content"": ""{escapedprompt}"" }}
                ]
            }}";

            Console.WriteLine("[*] Asking AI to generate code...");
            // Create the HTTP request (using native .NET libraries)
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
            request.Method = "POST";
            request.ContentType = "application/json";
            request.Headers["Authorization"] = "Bearer " + apiKey;

            // Write the request body
            using (var streamWriter = new StreamWriter(request.GetRequestStream()))
            {
                streamWriter.Write(jsonRequestBody);
                streamWriter.Flush();
            }

            // Get and read the response
            string responseContent;
            using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
            {
                using (var streamReader = new StreamReader(response.GetResponseStream()))
                {
                    responseContent = streamReader.ReadToEnd();
                }
            }

            // Deserialize the JSON response to extract the generated code
            ChatCompletionResponse chatResponse;
            using (var ms = new MemoryStream(System.Text.Encoding.UTF8.GetBytes(responseContent)))
            {
                var serializer = new DataContractJsonSerializer(typeof(ChatCompletionResponse));
                chatResponse = (ChatCompletionResponse)serializer.ReadObject(ms);
            }

            // The generated C# code from ChatGPT is now stored in sourceCode
            string sourceCode = chatResponse.Choices[0].Message.Content;

            // Sanitize the source code
            sourceCode = SanitizeSourceCode(sourceCode);
            //Console.WriteLine("[*] Generated code:\n" + sourceCode);

            // Parse the source code into a syntax tree
            SyntaxTree syntaxTree = CSharpSyntaxTree.ParseText(sourceCode);

            // Prepare references required for compilation.
            // These references point to the assemblies from the .NET Framework 4.8.
            string assemblyPath = Path.GetDirectoryName(typeof(object).Assembly.Location);
            var references = new List<MetadataReference>()
            {
                MetadataReference.CreateFromFile(Path.Combine(assemblyPath, "mscorlib.dll")),
                MetadataReference.CreateFromFile(Path.Combine(assemblyPath, "System.dll")),
                MetadataReference.CreateFromFile(Path.Combine(assemblyPath, "System.Core.dll")),
                MetadataReference.CreateFromFile(typeof(object).Assembly.Location),
                MetadataReference.CreateFromFile(typeof(Console).Assembly.Location)
            };

            // Create a Roslyn compilation for a dynamically linked library
            CSharpCompilation compilation = CSharpCompilation.Create(
                "DynamicAssembly",
                new[] { syntaxTree },
                references,
                new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary));

            // Emit the compiled assembly to a MemoryStream (our byte buffer)
            using (var ms = new MemoryStream())
            {
                Console.WriteLine("[*] Compiling reflectively...");
                EmitResult result = compilation.Emit(ms);

                if (!result.Success)
                {
                    // If there are compilation errors, output them and exit.
                    foreach (Diagnostic diagnostic in result.Diagnostics)
                    {
                        Console.Error.WriteLine(diagnostic.ToString());
                    }
                    return;
                }

                // Get the compiled assembly as a byte array.
                byte[] assemblyBytes = ms.ToArray();

                // Load the assembly from the byte array using reflection.
                Console.WriteLine("[*] Loading assembly...");
                Assembly assembly = Assembly.Load(assemblyBytes);

                // Find the type and method to execute.
                Console.WriteLine("[*] Executing reflectively...");
                Type dynamicType = assembly.GetType("DynamicProgram");
                MethodInfo executeMethod = dynamicType?.GetMethod("Execute", BindingFlags.Public | BindingFlags.Static);

                if (executeMethod != null)
                {
                    // Invoke the method; it will print "Hello World" to stdout.
                    Console.WriteLine("[*] Output: \n");
                    executeMethod.Invoke(null, null);
                }
                else
                {
                    Console.Error.WriteLine("Method 'Execute' not found.");
                }
            }
        }
    }
}

