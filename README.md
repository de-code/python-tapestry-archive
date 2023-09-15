# Python Tapestry Archive

This is based on [tapestry-archive](https://github.com/aldreth/tapestry-archive), written in Ruby.

Download all the pictures & videos from your child's [tapestry](https://tapestryjournal.com) account.

## Requirements

* Python 3.9
* Pip
* Make

## Setup

```bash
make dev-venv
```

That will create a Python virtual environment and install dependencies.

## Configuration

Copy `env.example` to `.env` and fill in the details.

* SCHOOL is in the URL
* Press F12 to open the dev tools in a browser and go to storage to grab the session cookie value

## Run

* Run `make run`

The images will be downloaded to the `images` directory.
The files will be named with the date & title of the observation, and the EXIF title.
