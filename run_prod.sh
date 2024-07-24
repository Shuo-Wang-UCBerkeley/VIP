APP_NAME=server
IMAGE_NAME=server_amd64
NAMESPACE=caopuzheng
URI=https://caopuzheng.mids255.com

# change the directory to the current directory
echo "changing directory to current script directory..."
cd "$(dirname "$0")"
echo "current directory: $(pwd)"

# version control the deployment patch and image
GIT_HASH=$(git rev-parse --short HEAD)
echo "git hash: ${GIT_HASH}"
IMAGE_FQDN=w255mids.azurecr.io/${NAMESPACE}/${IMAGE_NAME}:${GIT_HASH}
## generate the deployment patch yaml file
sed "s/GIT_HASH/${GIT_HASH}/g" \
  .k8s/overlays/prod/patch-deployment-server.template.yaml \
  >.k8s/overlays/prod/patch-deployment-server.yaml

# Initialize poetry virtualenv
echo
echo
echo "Creating environment..."
# poetry env remove python3.11
poetry install
poetry env list --full-path

# Run pytest within poetry virtualenv
# echo
# echo "Running pytest..."
# poetry run pytest -vv -s

# build the docker file
echo
echo "Build and push docker image for amd64 architecture..."
az acr login --name w255mids
docker buildx build --push --tag ${IMAGE_FQDN} -o type=image --platform=linux/amd64 .
# docker push w255mids.azurecr.io/caopuzheng/${IMAGE_NAME}:${GIT_HASH}
# az acr repository delete --name w255mids --image caopuzheng/lab4_image:e9160fb
echo "Docker image pushed to Azure Container Registry: ${IMAGE_FQDN}"

# deploy prod k8s resources to AKS
echo
kubectl config use-context w255-aks

kustomize build .k8s/overlays/prod -o ./temp/prod/
kubectl apply -k .k8s/overlays/prod

echo
sleep 5
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/${NAMESPACE}

# use kubectl to check if this exists
echo
sleep 5
kubectl rollout status -w deployment/redis -n ${NAMESPACE}
kubectl rollout status -w deployment/${APP_NAME} -n ${NAMESPACE}
echo

# test the endpoints
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
echo "Prod deployment has been finished succesfully!"

# start the port-forwarding of the grafana service
echo
kubectl port-forward -n prometheus svc/grafana 3000:3000

# In Prod, we can't delete the namespace as we don't have ability to recreate it
