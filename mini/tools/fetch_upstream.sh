#!/usr/bin/env bash
# Fetch the two reference repos into mini/third_party (git-ignored). Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p third_party && cd third_party
if [ ! -d microduck_rl/.git ]; then
  git clone --filter=blob:none --no-checkout https://github.com/pollen-robotics/microduck_rl.git
  cd microduck_rl
  git sparse-checkout init --cone
  git sparse-checkout set src/mjlab_microduck/robot/microduck
  git checkout 29e887ecfbf5d37144759e5a9f8a176dfb83d547
  cd ..
fi
if [ ! -d microduck-step-3d-models-ai-stl/.git ]; then
  git clone --depth 1 https://github.com/tianjin66/microduck-step-3d-models-ai-stl.git
fi
echo "microduck_rl @ $(git -C microduck_rl rev-parse HEAD)"
echo "stl repo    @ $(git -C microduck-step-3d-models-ai-stl rev-parse HEAD)"
ls microduck_rl/src/mjlab_microduck/robot/microduck/robot_walk.xml
ls microduck-step-3d-models-ai-stl/01_STL_original | wc -l
