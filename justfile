set shell := ["zsh", "-cu"]
venv_bin := ".venv/bin"

default:
  @just --list

help:
  {{venv_bin}}/videt --help

test *args="-q":
  {{venv_bin}}/pytest {{args}}

run *args:
  {{venv_bin}}/videt {{args}}

single input output:
  {{venv_bin}}/videt {{input}} {{output}}

single-with-words input output words:
  {{venv_bin}}/videt {{input}} {{output}} --words {{words}}

batch input output words_file workers="4" model_size="small.en" compute_type="int8":
  {{venv_bin}}/videt {{input}} {{output}} --recursive --words-file {{words_file}} --workers {{workers}} --model-size {{model_size}} --compute-type {{compute_type}}

dry-run input output words_file report_dir="reports" model_size="small.en" compute_type="int8":
  {{venv_bin}}/videt {{input}} {{output}} --recursive --words-file {{words_file}} --dry-run --report-dir {{report_dir}} --model-size {{model_size}} --compute-type {{compute_type}}
