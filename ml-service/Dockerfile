FROM python:3.10-slim

WORKDIR /app

# Устанавливаем системные зависимости
# libgl1-mesa-glx заменён на libgl1 + libglx0 + libopengl0
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglx0 \
    libopengl0 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Обновляем pip
RUN pip install --upgrade pip

COPY requirements.txt .

# Устанавливаем PyTorch CPU
RUN pip install --no-cache-dir torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cpu

# Устанавливаем остальные зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Проверяем критический импорт
RUN python -c "import cv2; print('OpenCV OK:', cv2.__version__)"

COPY . .

RUN mkdir -p dataset models files logs

EXPOSE 5010

CMD ["python", "-u", "server.py"]