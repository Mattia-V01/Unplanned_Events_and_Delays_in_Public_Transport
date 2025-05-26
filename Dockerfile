FROM python:3.11-slim

# Crea la directory di lavoro
WORKDIR /app

# Installa git, clona la repo e rimuovi git per alleggerire
RUN apt-get update && \
    apt-get install -y git && \
    git clone https://github.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport.git . && \
    apt-get remove -y git && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Espone la porta per Shiny
EXPOSE 8000

# Comando per avviare l'app
CMD ["shiny", "run", "--reload", "App/app.py"]
