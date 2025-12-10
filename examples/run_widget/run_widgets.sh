#!/bin/bash

for widget in examples/widgets/*.widget; do
  echo "Running $widget";
  uv run python examples/run_widget/run_widget.py "$widget";
done
