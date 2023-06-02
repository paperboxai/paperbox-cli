# PBX CLI

## To install

```
pip install git+https://github.com/paperboxai/paperbox-cli.git
```

## CLI Manual

```
❯ pbx --help
Usage: pbx [OPTIONS] COMMAND [ARGS]...

Options:
  -V, --version  Print the current version number and exit.
  -h, --help     Show this message and exit.

Commands:
  documents  All commands related to documents within Paperbox.
```

## FAQ

### How do I upload documents?

```
❯ pbx documents upload --help
Usage: pbx documents upload [OPTIONS] DOCUMENT_PATH

  Upload a document to PBX.

Options:
  --tag-type-id TEXT
  --document-class TEXT
  --document-subclass TEXT
  -r, --recursive
  --inbox-id TEXT           Inbox ID where the document is going to or resides
                            in. NOTE: This argument is mutually exclusive with
                            arguments: [router_id].
  --router-id TEXT          Router ID where the document is going to or
                            resides in. NOTE: This argument is mutually
                            exclusive with  arguments: [inbox_id].
  -kf, --key-file TEXT      Path to the JSON file containing the Token
                            Credentials
  -ak, --api-key TEXT       The API key to use for authentication
  -h, --help                Show this message and exit.
```

#### Authentication

To each request you provide an `--api-key` and `--key-file`.
You should contact a Paperbox representative for information on both.

The API Key should me a short string and the key file a `JSON` text file.

#### Example 1 (Simple)

Upload a **single document** to inbox `foo` with document-class `MAIL`.

```
pbx documents upload ./my/path-to/document.eml --inbox-id foo --document-class MAIL
```

Upload a **folder of documents** to inbox `foo` with document-class `MAIL`.

```
pbx documents upload ./my/path-to/documents/ --inbox-id foo --document-class MAIL
```

Upload **nested folders of documents** to inbox `foo` with document-class `MAIL`.

```
pbx documents upload ./my/path-to/documents/ --recursive --inbox-id foo --document-class MAIL
```

#### Example 2 (Advanced)

You can use placeholders to efficiently make use of the folderstructure you have.

Upload a **single document** to inbox `foo` with `document_class` within the filename.

```
pbx documents upload ./my/path-to/{document_class}_document.eml --inbox-id foo
```

Upload a **folder of documents** to inbox `foo` with `document_subclass` within the filename and `document_class` as a folder name.

```
pbx documents upload ./my/path-to/documents/{document_class}/{document_subclass}_* --inbox-id foo
```

Upload **nested folders of documents** to inbox `foo` with `document_class` as a folder name and unrelated folders in between.

```
pbx documents upload ./my/path-to/documents/*/{document_class}/ --recursive  --inbox-id foo
```
