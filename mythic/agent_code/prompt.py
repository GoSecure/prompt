    def prompt(self, task_id, prompt, model, cmdless, obfuscation):
        import io, ast, sys

        # prompt has been replaced by generated python code by the server (this is a solution to send data to the agent from the server)
        generated_code = prompt

        # verifying (again) if the code is correct
        try:
            ast.parse(generated_code)  
        except Exception as e:
            return f"Execution failed: {e}"
        
        # Get output
        output_capture = io.StringIO()
        sys.stdout = output_capture

        #exec(generated_code) # OLD
        # better exec code that support external variables/classes within classes and function:
        namespace = dict()
        # Ensure built-in functions (including __import__) are available.
        namespace['__builtins__'] = __import__('builtins')
        # Compile the source code in 'exec' mode.
        code_obj = compile(generated_code, '<string>', 'exec')
        # Use the same dictionary for both globals and locals.
        eval(code_obj, namespace, namespace)

        # Get the output
        sys.stdout = sys.__stdout__
        captured_output = output_capture.getvalue()

        # display result
        return f"Output:\n\n{captured_output}"

