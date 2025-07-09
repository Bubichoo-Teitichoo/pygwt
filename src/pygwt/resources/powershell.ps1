if (Get-Command git -CommandType Function -ErrorAction SilentlyContinue) {
    Remove-Item function:git
}

if (Get-Command git-twig -CommandType Function -ErrorAction SilentlyContinue) {
    Remove-Item function:git-twig
}

$env:_GIT_PATH =(Get-Command git).Source
$env:_GIT_TWIG_PATH =(Get-Command git-twig).Source

$script_block = {
    param($wordToComplete, $commandAst, $cursorPosition)

    $command=$commandAst.ToString()

    if ($command.StartsWith("git twig") -or $command.StartsWith("git-twig")) {
        $env:_GIT_TWIG_COMPLETE="powershell_complete"
        $env:COMP_WORDS=$command
        $env:COMP_CPOS=$cursorPosition

        & $env:_GIT_TWIG_PATH | ForEach-Object {
            $comp = $_ -Split "::",2
            if($comp[1]){
                [System.Management.Automation.CompletionResult]::new($comp[0], $comp[0], 'ParameterValue', $comp[1])
            }
            else{
                echo $_
            }
        } ; $env:_GIT_TWIG_COMPLETE=$null ; $env:COMP_WORDS=$null ;  $env:COMP_CPOS=$null
    }
}

Register-ArgumentCompleter -Native -CommandName git -ScriptBlock $script_block
Register-ArgumentCompleter -Native -CommandName git-twig -ScriptBlock $script_block

function git-twig {
    if ($args[0] -eq "switch" -or ($args[0] -eq "repository" -and $args[1] -eq "switch")) {
        $directory= & $env:_GIT_TWIG_PATH @args
        if ($LASTEXITCODE -eq 0) {
            cd $directory
        }
    }
    else {
        & $env:_GIT_TWIG_PATH @args
    }
}

function git {
    # If command is 'git twig' we call our handler/hook, otherwise we simply call git
    if ($args[0] -eq "twig") {
        git-twig @($args[1..$args.count])
    }
    else{
        & $env:_GIT_PATH @args
    }
}
