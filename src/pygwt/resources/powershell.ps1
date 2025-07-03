$script_block = {
    param($wordToComplete, $commandAst, $cursorPosition)

    $command=$commandAst.ToString()

    if ($command.StartsWith("git twig") -or $command.StartsWith("git-twig")) {
        $env:_GIT_TWIG_COMPLETE="powershell_complete"
        $env:COMP_WORDS=$commandAst.ToString()
        $env:COMP_CPOS=$cursorPosition
        git-twig.exe | ForEach-Object {
            $comp = $_ -Split "::",2
            if($comp[1]){
                [System.Management.Automation.CompletionResult]::new($comp[0], $comp[0], 'ParameterValue', $comp[1])
            }
            else{
                echo $_
            }
        } ; $env:_GIT_TWIG_COMPLETE=$null
    }
}

function git-twig {
    if ($args[0] -eq "switch" -or ($args[0] -eq "repository" -and $args[1] -eq "switch")) {
        $directory = git-twig.exe $args
        if ($LASTEXITCODE -eq 0) {
            cd $directory
        }
    }
    else {
        git-twig.exe $args
    }
}

function git {
    # If command is 'git twig' we call our handler/hook, otherwise we simply call git
    if ($args[0] -eq "twig") {
        git-twig($args[1..$args.count])
    }
    else{
        git.exe $args[0..$args.count]
    }
}

Register-ArgumentCompleter -Native -CommandName git -ScriptBlock $script_block
Register-ArgumentCompleter -Native -CommandName git.exe -ScriptBlock $script_block
Register-ArgumentCompleter -Native -CommandName git-twig -ScriptBlock $script_block
Register-ArgumentCompleter -Native -CommandName git-twig.exe -ScriptBlock $script_block
