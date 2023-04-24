import logging
import re
from typing import Optional
import pbx

import os
from functools import partial
import glob

import click

from clickclick import AliasedGroup

from .helpers.click_helpers import MutuallyExclusiveOption, GroupWithCommandOptions
from .documents import upload as upload_documents
from .security import auth

logger = logging.getLogger("pbx.cli")

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"PBX {pbx.__version__}")
    ctx.exit()


@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
@click.option(
    "-V",
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Print the current version number and exit.",
)
def main():
    pass


@main.group(cls=GroupWithCommandOptions, help="TBD")
@click.option(
    "--inbox-id",
    cls=MutuallyExclusiveOption,
    help="TBD",
    required=False,
    default=None,
    mutually_exclusive=["router_id"],
)
@click.option(
    "--router-id",
    cls=MutuallyExclusiveOption,
    help="TBD",
    required=False,
    default=None,
    mutually_exclusive=["inbox_id"],
)
@click.option(
    "-kf",
    "--key-file",
    help="Path to the JSON file containing the Token Credentials",
    required=False,
    default=None,
)
@click.option(
    "-ak",
    "--api-key",
    help="The API key to use for authentication",
    required=False,
    default=None,
)
@click.pass_context
def documents(
    ctx,
    inbox_id: Optional[str] = None,
    router_id: Optional[str] = None,
    key_file: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    TBA
    """
    key_file = key_file or os.environ.get("PBX_KEY_FILE")
    api_key = api_key or os.environ.get("PBX_API_KEY")
    if not ctx.invoked_subcommand and (not key_file or not api_key):
        os_args = click.get_os_args()
        if not any(arg in os_args for arg in ["--help", "-h"]):
            raise click.UsageError(
                "The PBX_KEY_FILE and PBX_API_KEY environment variables must"
                " be set or provided during command invocation."
            )
    ctx.obj = {
        "inbox_id": inbox_id,
        "router_id": router_id,
        "key_file": key_file,
        "api_key": api_key,
    }


def _replace_placeholders_with_regex(path):
    # Regular expression pattern for matching placeholders
    pattern = r"{(\w+)}"

    # Escape special characters in the path
    path = (
        re.escape(path)
        .replace("\*", ".*")
        .replace("\?", ".?")
        .replace("\{", "{")
        .replace("\}", "}")
    )

    # Replace placeholders with a regex match group
    path = re.sub(pattern, r"(?P<\1>[^/]+)", path)

    # Return the path with placeholders replaced with regex match groups
    return path


def _find_files(root: str, pattern: str, recursive=True):
    """
    Recursively/non-recursively walks the directory tree rooted at root and returns a list of file paths that match the given pattern regex.

    root (str): the root directory to start the search from.
    pattern (str): a regex pattern that the file paths should match.
    recursive (str): a flag to indicate whether to recursively traverse the directory tree.

    Return: a list of file paths that match the given pattern regex.
    """
    matches = []
    if recursive:
        for dirpath, _, filenames in os.walk(root):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)

                if parsed_path := re.search(pattern, filepath):
                    matches.append((filepath, parsed_path.groupdict()))
    else:
        for filename in os.listdir(root):
            filepath = os.path.join(root, filename)
            if parsed_path := re.search(pattern, filepath):
                if os.path.isfile(filepath):
                    matches.append((filepath, parsed_path.groupdict()))
                else:
                    if filepath.split("/")[-1] == parsed_path.groups()[-1]:
                        matches.extend(_find_files(filepath, pattern, recursive))
                    else:
                        logging.warning(
                            f"Skipping directory {filepath}, use --recursive to include it."
                        )

    return matches


@documents.command(help="TBD")
@click.argument("document-path")
@click.option("--tag-type-id", default=None, required=False)
@click.option("--document-class", default=None, required=False)
@click.option("--document-subclass", default=None, required=False)
@click.option("-r", "--recursive", is_flag=True, default=False, required=False)
@click.pass_obj
def upload(
    ctx,
    *,
    document_path: str,
    recursive: bool = False,
    tag_type_id: Optional[str] = None,
    document_class: Optional[str] = None,
    document_subclass: Optional[str] = None,
):
    """
    TBA
    """
    document_path = os.path.normpath(document_path)
    match_path = _replace_placeholders_with_regex(document_path)
    root = os.path.dirname(document_path.split("{", 1)[0]) or match_path

    config_gens = []
    for path, variables in _find_files(root, match_path, recursive):
        params = {
            "inbox_id": ctx["inbox_id"],
            "router_id": ctx["router_id"],
            "tag_type_id": tag_type_id,
            "document_class": document_class,
            "document_subclass": document_subclass,
            **variables,
        }
        config_gen = partial(
            upload_documents.upload_document,
            document_path=path,
            dry_run=True,
            key_file=ctx["key_file"],
            api_key=ctx["api_key"],
            **params,
        )
        config_gens.append(config_gen)

    upload_documents.batch_upload_configs(config_gens)
