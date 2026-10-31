#!/usr/bin/env bash
# ==============================================================================
# PP-OCRv6 Small Setup & Verification Script for EC2
# Supported OS: Ubuntu 22.04 / 24.04, Amazon Linux 2023 / AL2, Debian
# ==============================================================================

set -e

echo "=========================================================="
echo " STEP 1: Inspecting OS & Environment"
echo "=========================================================="
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME=$NAME
    OS_VER=$VERSION_ID
    echo "[INFO] Operating System: $OS_NAME ($OS_VER)"
else
    echo "[WARN] Could not determine OS from /etc/os-release"
fi

echo "[INFO] Architecture: $(uname -m)"
echo "[INFO] Available Memory:"
free -h

# Check Python version
PYTHON_BIN=""
for py in python3.11 python3.10 python3.12 python3; do
    if command -v $py &> /dev/null; then
        PYTHON_BIN=$(command -v $py)
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "[ERROR] Python 3 not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3 python3-pip
    fi
    PYTHON_BIN=$(command -v python3)
fi

echo "[INFO] Using Python binary: $PYTHON_BIN"
$PYTHON_BIN --version

echo ""
echo "=========================================================="
echo " STEP 2: Installing System-Level Dependencies (OpenCV / GL)"
echo "=========================================================="
if command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libgomp1 libspatialindex-dev wget curl
elif command -v dnf &> /dev/null; then
    sudo dnf install -y mesa-libGL glib2 libgomp wget curl
elif command -v yum &> /dev/null; then
    sudo yum install -y mesa-libGL glib2 libgomp wget curl
fi

echo ""
echo "=========================================================="
echo " STEP 3: Setting Up Virtual Environment & Dependencies"
echo "=========================================================="
VENV_DIR="$HOME/paddleocr_env"
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtualenv at $VENV_DIR..."
    $PYTHON_BIN -m venv "$VENV_DIR" || $PYTHON_BIN -m pip install --user virtualenv && $PYTHON_BIN -m virtualenv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel

echo "[INFO] Installing PaddlePaddle (CPU)..."
pip install paddlepaddle -i https://www.paddlepaddle.org.cn/packages/stable/cpu/

echo "[INFO] Installing PaddleOCR with PP-OCRv6 support..."
pip install "paddleocr[all]"

echo ""
echo "=========================================================="
echo " STEP 4: Verifying PP-OCRv6 Installation"
echo "=========================================================="
python3 -c "
import paddle
import paddleocr
print('[SUCCESS] PaddlePaddle Version:', paddle.__version__)
print('[SUCCESS] PaddleOCR Version:', paddleocr.__version__)
"

# Run sample verification script
if [ -f "verify_ppocr_v6.py" ]; then
    python3 verify_ppocr_v6.py
fi

echo "=========================================================="
echo " PP-OCRv6 SETUP COMPLETED SUCCESSFULLY"
echo "=========================================================="
