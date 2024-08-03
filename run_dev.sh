APP_NAME=server
IMAGE_NAME=server_arm64
NAMESPACE=caopuzheng
URI="http://localhost:8000"
SHUT_DOWN_MINIKUBE=1

# change the directory to the current directory
echo "changing directory to current script directory..."
cd "$(dirname "$0")"
echo "current directory: $(pwd)"

# Initialize poetry virtualenv
echo

# train the model and save it to the models directory
echo
echo "creating environment..."
# poetry env remove python3.11
poetry install
poetry env list --full-path

# Train the model if model_pipeline.pkl does not exist
# echo
# FILE=./model_pipeline.pkl
# if [ ! -f ${FILE} ]; then
#     echo "training model..."
#     poetry run python ./trainer/train.py
# else
#     echo "${FILE} already exists, skipping training..."
# fi

# start mini-kube
if [ $SHUT_DOWN_MINIKUBE -eq 1 ]; then
    minikube start --kubernetes-version=v1.29.2 --namespace ${NAMESPACE}
fi
kubectl config use-context minikube

#Register local docker instance with minikube
eval $(minikube docker-env)

# build the docker file
echo
echo "building docker image..."
docker build -t ${IMAGE_NAME} .

# deploy the Redis
kustomize build .k8s/overlays/dev -o ./temp/dev/
kubectl apply -k .k8s/overlays/dev
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/${NAMESPACE}

# use kubectl to check if this exists
echo
sleep 5
kubectl rollout status -w deployment/redis -n ${NAMESPACE}
kubectl rollout status -w deployment/${APP_NAME} -n ${NAMESPACE}
echo

# kill $(ps aux | grep "[m]inikube tunnel" | awk '{print $2}')
minikube tunnel &
TUNNEL_PID=$!
sleep 8
echo "minikube tunnel started in pid: ${TUNNEL_PID}..."

# test the docker container
echo "testing '/docs' endpoint, expecting 200..."
curl -o /dev/null -s -w "%{http_code}\n" -X GET "$URI/docs"

echo
echo "testing '/baseline_allocate' endpoint, expecting 200..."
curl -o /dev/null -s -w "%{http_code}\n" -X 'POST' "$URI/baseline_allocate" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
            "risk_tolerance": "moderate",
            "stockList": [{"ticker":"AAPL","weight_lower_bound":0.05,"weight_upper_bound":0.15},{"ticker":"AMZN","weight_lower_bound":0.35,"weight_upper_bound":0.35},{"ticker":"GOOGL"},{"ticker":"NVDA","weight_lower_bound":0.25}]
        }'

echo
echo "testing '/ml_allocate_cosine_similarity' endpoint, expecting 200..."
curl -o /dev/null -s -w "%{http_code}\n" -X 'POST' "$URI/ml_allocate_cosine_similarity" \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
            "risk_tolerance": "moderate",
            "stockList": [{"ticker":"AAPL","weight_lower_bound":0.05,"weight_upper_bound":0.15},{"ticker":"AMZN","weight_lower_bound":0.35,"weight_upper_bound":0.35},{"ticker":"GOOGL"},{"ticker":"NVDA","weight_lower_bound":0.25}]
        }'

# output and tail the logs for the api deployment
echo
echo
kubectl logs -n ${NAMESPACE} -l app=${APP_NAME}

echo
echo
echo "Press any key to clean up..."
read -n 1 -s

echo
echo "Cleaning up..."
# kubectl delete namespace ${NAMESPACE} # this will also delete everything in it
kubectl delete -k .k8s/overlays/dev
# kubectl delete configmap redis --namespace=caopuzheng

echo "stop the minikube tunnel..."
kill ${TUNNEL_PID}
docker image rm ${IMAGE_NAME}
if [ $SHUT_DOWN_MINIKUBE -eq 1 ]; then
    minikube stop
fi
echo "The script has finished running properly!"
