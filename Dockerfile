FROM python:3.12-slim

WORKDIR /app

# تثبيت التبعيات الأساسية للنظام
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libdbus-1-dev \
    libglib2.0-dev \
    libcairo2-dev \
    libgirepository1.0-dev \
    meson \
    ninja-build \
    curl \
    dbus \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY constraints.txt .

# التنظيف التلقائي
RUN sed -i '/python-apt/d' requirements.txt && \
    sed -i '/pkg-resources/d' requirements.txt && \
    sed -i '/pycairo/d' requirements.txt

# تثبيت مكتبات البايثون
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    if [ -s constraints.txt ]; then \
        pip install --no-cache-dir -r requirements.txt -c constraints.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

COPY . .

# 🔥 إنشاء مجلد وملف secrets.toml الافتراضي لتفادي خطأ Streamlit
RUN mkdir -p /app/.streamlit && \
    echo '[general]' > /app/.streamlit/secrets.toml

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
