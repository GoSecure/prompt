### Description
C# code PoC that reflectively compiles and executes AI-generated code (requested via the OpenAI API in this example).

All the code is contained in the source file `Program.cs`.

### Usage
1. Set your OpenAI API key in the `apiKey` variable in the `Program.cs` file
2. Build the program (follow the build instructions)
3. Usage: `prompt.exe <prompt>`

### Example output:
```
>> prompt.exe "list the content of the C:/ drive. Prefix [F] for files and [D] for directories"
[*] Asking AI to generate code...
[*] Compiling reflectively...
[*] Loading assembly...
[*] Executing reflectively...
[*] Output:

[D] C:\$Recycle.Bin
[D] C:\Documents and Settings
[D] C:\PerfLogs
[D] C:\Program Files
[D] C:\Program Files (x86)
[D] C:\ProgramData
[D] C:\Recovery
[D] C:\System Volume Information
[D] C:\Users
[D] C:\Windows
[F] C:\DumpStack.log.tmp
[F] C:\pagefile.sys
[F] C:\swapfile.sys
```

### Requirements
I recommend performing this procedure in a Linux **VM** (tested on kali). This procedure might not work in your environment.

```bash
sudo apt update
sudo apt install gnupg ca-certificates curl -y
sudo curl -o /usr/local/bin/nuget.exe https://dist.nuget.org/win-x86-commandline/latest/nuget.exe
echo -e '!#/bin/bash\nmono /usr/local/bin/nuget.exe $*' > /usr/bin/nuget
sudo chmod +x /usr/bin/nuget
sudo mkdir -p /etc/apt/keyrings
sudo wget https://download.mono-project.com/repo/xamarin.gpg -O /etc/apt/keyrings/mono-official.asc
echo "deb [signed-by=/etc/apt/keyrings/mono-official.asc] https://download.mono-project.com/repo/debian stable-buster main" | sudo tee /etc/apt/sources.list.d/mono-official-stable.list
sudo apt update
sudo apt install mono-complete msbuild
```

### Build
I also recommend performing this procedure in a Linux **VM**. 

```bash
# The first time only,
# copy `ilrepack` folder in the `/tmp` folder, then:
cd /tmp/ilrepack
nuget install ILRepack -OutputDirectory .
cd /tmp/ilrepack/RoslynCompileAndExecute/
nuget restore RoslynCompileAndExecute.csproj
# Always:
msbuild RoslynCompileAndExecute.csproj /p:Configuration=Release
mono /tmp/ilrepack/ILRepack.2.0.40/tools/ILRepack.exe /out:/tmp/compileandexec.exe ./bin/Release/net48/RoslynCompileAndExecute.exe ./bin/Release/net48/Microsoft.CodeAnalysis.dll ./bin/Release/net48/Microsoft.CodeAnalysis.CSharp.dll ~/.nuget/packages/system.collections.immutable/6.0.0/lib/net461/System.Collections.Immutable.dll ~/.nuget/packages/system.reflection.metadata/5.0.0/lib/net461/System.Reflection.Metadata.dll ~/.nuget/packages/system.memory/4.5.5/lib/net461/System.Memory.dll ~/.nuget/packages/system.runtime.compilerservices.unsafe/6.0.0/lib/net461/System.Runtime.CompilerServices.Unsafe.dll ~/.nuget/packages/system.numerics.vectors/4.5.0/lib/net46/System.Numerics.Vectors.dll
```

