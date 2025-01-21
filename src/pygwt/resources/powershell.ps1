$script_block = {
    param($wordToComplete, $commandAst, $cursorPosition)

    $command=$commandAst.ToString()

    if ($command.StartsWith("git wt") -or $command.StartsWith("pygwt")) {
        $env:_PYGWT_COMPLETE="powershell_complete"
        $env:COMP_WORDS=$commandAst.ToString()
        $env:COMP_CPOS=$cursorPosition
        pygwt.exe | ForEach-Object {
            $comp = $_ -Split "::",2
            if($comp[1]){
                [System.Management.Automation.CompletionResult]::new($comp[0], $comp[0], 'ParameterValue', $comp[1])
            }
            else{
                echo $_
            }
        } ; $env:_PYGWT_COMPLETE=$null
    }
}

function pygwt {
    if ($args[0] -eq "switch" -or ($args[0] -eq "repository" -and $args[1] -eq "switch")) {
        pygwt.exe $args | cd
    }
    else {
        pygwt.exe $args
    }
}

function git-wt {
    if ($args[0] -eq "switch" -or ($args[0] -eq "repository" -and $args[1] -eq "switch")) {
        pygwt.exe $args | cd
    }
    else {
        pygwt.exe $args
    }
}

function git {
    if ($args[0] -eq "wt") {
        if ($args[1] -eq "switch" -or ($args[1] -eq "repository" -and $args[2] -eq "switch")) {
            pygwt.exe $args[1..$args.count] | cd
        }
        else {
            pygwt.exe $args[1..$args.count]
        }
    }
    else{
        git.exe $args[0..$args.count]
    }
}

Register-ArgumentCompleter -Native -CommandName pygwt -ScriptBlock $script_block
Register-ArgumentCompleter -Native -CommandName pygwt.exe -ScriptBlock $script_block
Register-ArgumentCompleter -Native -CommandName git -ScriptBlock $script_block
Register-ArgumentCompleter -Native -CommandName git-wt -ScriptBlock $script_block
