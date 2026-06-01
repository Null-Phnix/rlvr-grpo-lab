#!/usr/bin/env bash
set -euo pipefail

run_python_module() {
  if [ -n "${RLVR_PYTHON:-}" ]; then
    PYTHONPATH="src${PYTHONPATH:+:${PYTHONPATH}}" "${RLVR_PYTHON}" -m "$@"
  else
    uv run python -m "$@"
  fi
}

run_logged() {
  local name="$1"
  shift
  mkdir -p outputs/logs
  echo
  echo "==> ${name}"
  "$@" 2>&1 | tee "outputs/logs/${name}.log"
}

config_output_dir() {
  local config_path="$1"
  awk '$1 == "output_dir:" { print $2; exit }' "${config_path}"
}

checksum_eval_dir() {
  local output_dir="$1"
  (
    cd "${output_dir}"
    if command -v sha256sum >/dev/null 2>&1; then
      find . -maxdepth 1 -type f \( \
        -name summary.json -o \
        -name samples.jsonl -o \
        -name failure_analysis.json -o \
        -name "*.md" \
      \) -print0 | sort -z | xargs -0 sha256sum > sha256s.txt
    else
      find . -maxdepth 1 -type f \( \
        -name summary.json -o \
        -name samples.jsonl -o \
        -name failure_analysis.json -o \
        -name "*.md" \
      \) -print0 | sort -z | xargs -0 shasum -a 256 > sha256s.txt
    fi
  )
}

checksum_adapter_dir() {
  local output_dir="$1"
  (
    cd "${output_dir}"
    if command -v sha256sum >/dev/null 2>&1; then
      find . -maxdepth 2 -type f \( \
        -name "*.json" -o \
        -name "*.safetensors" -o \
        -name "*.bin" -o \
        -name "*.md" -o \
        -name "*.jinja" -o \
        -name "*.pth" -o \
        -name "*.pt" \
      \) -print0 | sort -z | xargs -0 sha256sum > sha256s.txt
    else
      find . -maxdepth 2 -type f \( \
        -name "*.json" -o \
        -name "*.safetensors" -o \
        -name "*.bin" -o \
        -name "*.md" -o \
        -name "*.jinja" -o \
        -name "*.pth" -o \
        -name "*.pt" \
      \) -print0 | sort -z | xargs -0 shasum -a 256 > sha256s.txt
    fi
  )
}

checksum_dataset_artifacts() {
  local dataset_path="$1"
  local summary_path="${dataset_path%.jsonl}.summary.json"
  local checksum_path="${dataset_path%.jsonl}.sha256s.txt"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${dataset_path}" "${summary_path}" > "${checksum_path}"
  else
    shasum -a 256 "${dataset_path}" "${summary_path}" > "${checksum_path}"
  fi
}

run_eval_config() {
  local config_path="$1"
  local name
  local output_dir
  name="$(basename "${config_path}" .yaml)"
  output_dir="$(config_output_dir "${config_path}")"
  run_logged "${name}" run_python_module rlvr_lab.eval_model --config "${config_path}"
  run_python_module rlvr_lab.analyze_samples "${output_dir}" --output "${output_dir}/failure_analysis.json"
  checksum_eval_dir "${output_dir}"
  echo "Wrote ${output_dir}/summary.json"
}

require_path() {
  local path="$1"
  local message="$2"
  if [ ! -e "${path}" ]; then
    echo "Missing required path: ${path}" >&2
    echo "${message}" >&2
    exit 1
  fi
}
