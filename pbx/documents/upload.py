"""Helper functions for uploading documents."""


import os
from typing import Callable, List, Optional, Union

from ..utils import string_to_identifier
from ..security import auth

from ..helpers.sparp import sparp
import aiohttp


async def upload_document(
    document_path: str,
    key_file: str,
    api_key: str,
    tag_type_id: Optional[str] = None,
    document_class: Optional[str] = None,
    document_subclass: Optional[str] = None,
    inbox_id: Optional[str] = None,
    router_id: Optional[str] = None,
    dry_run: bool = False,
):
    """Uploads a document to the PBX-CLI server.

    Args:
        document_path (str): path to the document to upload.
        key_file (str): keyfile path to use for the upload.
        api_key (str): api key to use for the upload.
        tag_type_id (Optional[str], optional): tag type id to use for the document. Defaults to None.
        document_class (Optional[str], optional): document class to use for the document. Defaults to None.
        document_subclass (Optional[str], optional): document subclass to use for the document. Defaults to None.
        inbox_id (Optional[str], optional): inbox id to use for the document. Defaults to None.
        router_id (Optional[str], optional): router id to use for the document. Defaults to None.

    """
    if inbox_id and router_id:
        raise ValueError("Cannot specify both inbox_id and router_id.")
    elif not inbox_id and not router_id:
        raise ValueError("Must specify either inbox_id or router_id.")

    if not os.path.isfile(document_path):
        raise FileNotFoundError(f"File {document_path} not found.")

    token, endpoint = auth.generate_jwt(key_file)

    endpoint = endpoint.rstrip("/")
    if inbox_id:
        url = f"{endpoint}/v2/operational/inboxes/{inbox_id}/documents"
    else:
        url = f"{endpoint}/v2/operational/routers/{router_id}/documents"

    with aiohttp.MultipartWriter("form-data") as writer:
        # Add "document" field
        with open(document_path, "rb") as f:
            writer.append(
                f.read(),
                {
                    "Content-Type": "application/octet-stream",
                    "Content-Disposition": 'form-data; name="document"; filename="{}"'.format(
                        document_path
                    ),
                },
            )

        # Add other fields, if they exist
        if tag_type_id:
            writer.append(
                string_to_identifier(tag_type_id),
                {"Content-Disposition": 'form-data; name="tag_type_id"'},
            )
        if document_class:
            writer.append(
                string_to_identifier(document_class),
                {"Content-Disposition": 'form-data; name="document_class"'},
            )
        if document_subclass:
            writer.append(
                string_to_identifier(document_subclass),
                {"Content-Disposition": 'form-data; name="document_subclass"'},
            )
        writer.append(document_path, {"Content-Disposition": 'form-data; name="document_id"'})

        config = {
            "method": "post",
            "url": url,
            "headers": {
                "Authorization": f"Bearer {token}",
                "Content-Type": writer.content_type,
                "Content-Length": str(writer.size),
            },
            "params": {"key": api_key},
            "data": writer,
            "timeout": aiohttp.ClientTimeout(total=900),
        }
        if not dry_run:
            batch_upload_configs([config])
        return config


def batch_upload_configs(configs: List[Union[dict, Callable]]):
    """Batch uploads documents to the PBX Integration.

    Args:
        configs (List[Union[dict, Callable]]): list of upload configs.
    """
    ok_status_codes = [200, 202, 201, 204]
    results = sparp(
        configs,
        max_outstanding_requests=1000000,
        time_between_requests=(1 / (500 / 60)) * 2,
        stop_on_first_fail=False,
        ok_status_codes=ok_status_codes,
        disable_bar=False,
        attempts=100,
        retry_status_codes=[429, 401, 403, 425, 424, 503],
    )
    if any(result["status_code"] not in ok_status_codes for result in results):
        raise Exception("Failed to upload files: %s", results)
