# Documentation

## What my application does?

My application is a simple python application that uses the [FastAPI](https://fastapi.tiangolo.com/) framework to create a simple REST API and hosted asynchronous using [uvicorn](https://www.uvicorn.org/).

The Application is packaged using [Poetry](https://python-poetry.org/), and is built and run using [Docker](https://www.docker.com/).

It can be deployed via [kubernetes](https://kubernetes.io/), either to local computer using [minikube](https://minikube.sigs.k8s.io/docs/) or to a cloud provider such as [Azure](https://azure.microsoft.com/en-us/).

The API has the following endpoints:

- a primary "/bulk_calibrate" endpoint for calibrating the best allocation for a list of stock tickers. The endpoint takes a list of stock tickers and returns the best allocation for the given tickers, together the expected volatility of the portfolio.

  - we allow the user to lock the weight of a specific stock, by providing the weight in the request. The endpoint will then calculate the best allocation for the remaining stocks.

  It also implements caching, so that if the same request is made again in a short period, the result is returned from the cache instead of being calculated again.

Other supporting endpoints include:

- a "/refresh_data" endpoint for fetching the latest stock data from the Yahoo Finance API, and the latest stock embeddings from the S3 bucket
- a "/health" endpoint for healthchecking
- a "/docs" endpoint for the openapi documentation
- a "/openapi.json" endpoint that returns a `json` object that meets the OpenAPI specification version `3+`

## How to build my application?

To build it, you need to run the following command, assuming you are in the same directory as the `Dockerfile`:

```bash
# build and deploy to Azure
sh run_prod.sh

# build and deploy to minikube
sh run_dev.sh
```

## How to run my application?

To run the production version of the app, you can go to [here](https://caopuzheng.mids255.com/docs#) and try with the example data.
