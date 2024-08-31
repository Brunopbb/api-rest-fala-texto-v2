# Usar uma imagem base Python leve
# Usar uma imagem base Python leve
FROM python:3.12-slim

# Definir o diretório de trabalho no contêiner
WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar as dependências da aplicação
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o conteúdo da aplicação para o diretório de trabalho
COPY . .

# Expor a porta que será usada pelo Flask
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "app.py"]
