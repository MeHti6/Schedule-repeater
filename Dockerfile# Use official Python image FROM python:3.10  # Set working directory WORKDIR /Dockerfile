# Use official Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy all files into container
COPY . .

# Install required packages
RUN pip install --no-cache-dir -r requirements.txt

# Start the bot
CMD ["python", "bot.py"]
