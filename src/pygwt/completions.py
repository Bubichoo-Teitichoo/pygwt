"""Module providing shell completions."""

import os

from click import shell_completion
from click.shell_completion import split_arg_string


@shell_completion.add_completion_class
class PowershellComplete(shell_completion.ShellComplete):
    """Click Powershell completions."""

    name = "powershell"
    source_template = ""

    def get_completion_args(self) -> tuple[list[str], str]:
        """
        Parse completion arguments.

        This function always assumes that the last word is to be completed.
        Everything else isn't really supported by click.
        """
        command = os.environ["COMP_WORDS"]
        pos = int(os.environ["COMP_CPOS"])
        words = split_arg_string(command)

        if words[0] == "git-twig":
            words = words[1:]
        elif words[0] == "git" and words[1] == "twig":
            words = words[2:]

        if len(command) < pos:
            incomplete = ""
        else:
            incomplete = words[-1]
            words = words[:-1]

        return words, incomplete

    def format_completion(self, item: shell_completion.CompletionItem) -> str:
        """
        Format the completion items.

        For the completion to be digestible for powershell,
        we split the value and the help text with to colons.
        That way we can easily split them at that marker
        and create completion items within powershell.
        """
        if item.help is not None:
            return f"{item.value} ::{item.help}"
        return f"{item.value} "
