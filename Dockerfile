FROM rocm/pytorch:rocm6.2_ubuntu22.04_py3.10_pytorch_release_2.1.0

WORKDIR /workspace/kalpixk

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
