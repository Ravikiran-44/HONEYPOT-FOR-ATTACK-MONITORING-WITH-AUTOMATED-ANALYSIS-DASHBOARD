FROM python:3.11-slim

WORKDIR /app
COPY requirements_streamlit.txt ./
RUN pip install --no-cache-dir -r requirements_streamlit.txt

COPY app.py ./

# expose streamlit port and run
ENV PORT=8501
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
