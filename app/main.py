import time
from contextlib import asynccontextmanager

import pandas as pd
import psutil
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

import mlflow

loaded_model = None

# Create Prometheus metrics
cpu_usage_gauge = Gauge("cpu_usage_percent", "CPU usage percentage")
memory_usage_gauge = Gauge("memory_usage_bytes", "Memory usage in bytes")

prediction_gauge = Gauge("model_prediction", "Model prediction value")
model_latency = Gauge("model_latency_seconds", "Time taken for model prediction")
# Counters
request_counter = Counter("total_requests", "Total number of prediction requests")
success_counter = Counter(
    "successful_predictions", "Total number of successful predictions"
)
failure_counter = Counter("failed_predictions", "Total number of failed predictions")

# Histograms for latency
latency_histogram = Histogram(
    "request_latency_seconds",
    "Request latency in seconds",
    buckets=(0.1, 0.5, 1, 2.5, 5, 10),  # Customize buckets as needed
)
# Histograms for input features
# Histograms for input features
feature_histograms = {
    "fixed_acidity": Histogram(
        "input_fixed_acidity",
        "Fixed acidity of input data",
        buckets=[5, 6, 7, 8, 9, 10, 11, 12, 13],
    ),
    "volatile_acidity": Histogram(
        "input_volatile_acidity",
        "Volatile acidity of input data",
        buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
    ),
    # Add histograms for other features as needed...
}
# Histogram for prediction values
prediction_histogram = Histogram(
    "prediction_values", "Distribution of prediction values"
)

mlflow.set_tracking_uri("http://mlflow_server:5000")


# Instantiate the FastAPI app
app = FastAPI(debug=True)
# Expose default metrics
instrumentator = Instrumentator()

instrumentator.instrument(app).expose(app)

# Expose custom metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global loaded_model
    MODEL_ID = "81016038b59b4414921424a53061c62c"
    logged_model = f"runs:/{MODEL_ID}/model"

    # Load the model once at startup
    loaded_model = mlflow.pyfunc.load_model(logged_model)
    print("Model loaded and cached at startup")

    yield

    # You can add any cleanup logic here if needed
    print("Application shutdown, resources cleaned")


# Assign the lifespan context manager to the app
app.router.lifespan_context = lifespan


@app.middleware("http")
async def add_process_metrics(request: Request, call_next):
    response = await call_next(request)
    cpu_usage_gauge.set(psutil.cpu_percent())
    memory_usage_gauge.set(psutil.virtual_memory().used)
    return response


@app.get("/")
async def home():
    return "Hello World"


class PredictionInput(BaseModel):
    data: list


@app.post("/predict")
async def predict(input_data: PredictionInput):
    global loaded_model
    data = input_data.data
    request_counter.inc()
    start_time = time.time()
    try:
        # Validate input data
        # Increment failure_counter if validation fails

        # Record feature statistics
        for i, feature_name in enumerate(feature_histograms.keys()):
            feature_value = input_data.data[i]
            feature_histograms[feature_name].observe(feature_value)
        # Prepare the input data
        data = pd.DataFrame(
            columns=[
                "fixed acidity",
                "volatile acidity",
                "citric acid",
                "residual sugar",
                "chlorides",
                "free sulfur dioxide",
                "total sulfur dioxide",
                "density",
                "pH",
                "sulphates",
                "alcohol",
            ],
            data=[data],
        )

        prediction = loaded_model.predict(data)

        prediction_value = prediction[0]
        prediction_gauge.set(prediction_value)
        prediction_histogram.observe(prediction_value)

        success_counter.inc()
    except Exception as e:
        failure_counter.inc()
        raise e
    finally:
        elapsed_time = time.time() - start_time
        latency_histogram.observe(elapsed_time)

        return JSONResponse({"prediction": prediction_value})


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
