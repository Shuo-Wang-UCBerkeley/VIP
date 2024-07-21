APP_NAME=server
IMAGE_NAME=server_amd64
NAMESPACE=caopuzheng

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

# Train the model if model_pipeline.pkl does not exist
# echo
# FILE=./model_pipeline.pkl
# if [ ! -f ${FILE} ]; then
#   echo "Training model..."
#   poetry run python ./trainer/train.py
# else
#   echo "${FILE} already exists, skipping training..."
# fi

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
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/${NAMESPACE}

# use kubectl to check if this exists
echo
sleep 5
kubectl rollout status -w deployment/redis -n ${NAMESPACE}
kubectl rollout status -w deployment/${APP_NAME} -n ${NAMESPACE}
echo

# test the {docs,health,predict,bulk_predict} endpoints
echo "Testing '/docs' endpoint, expecting 200..."
curl -o /dev/null -s -w "%{http_code}\n" -X GET \
  'https://caopuzheng.mids255.com/docs' -H 'accept: application/json'

echo "Testing '/health' endpoint, expecting 200..."
curl -o /dev/null -s -w "%{http_code}\n" -X GET \
  'https://caopuzheng.mids255.com/health' -H 'accept: application/json'

# echo "Testing '/predict' endpoint, expecting an valid prediction output..."
# curl -X 'POST' \
#   'https://caopuzheng.mids255.com/predict' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{
#   "ave_bedrm_num": 1.02,
#   "ave_occup": 2.56,
#   "ave_room_num": 7.1,
#   "house_age": 41,
#   "latitude": 37.88,
#   "longitude": -122.23,
#   "med_income": 8.3,
#   "population": 322
# }' | python -m json.tool

# echo
# echo "Testing '/bulk_predict' endpoint, expecting an valid prediction output..."
# # Test bulk predict endpoint with valid input
# curl -X 'POST' \
#   'https://caopuzheng.mids255.com/bulk_predict' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{
#   "houses": [
#     {
#       "ave_bedrm_num": 1.02,
#       "ave_occup": 2.56,
#       "ave_room_num": 7.1,
#       "house_age": 41,
#       "latitude": 37.88,
#       "longitude": -122.23,
#       "med_income": 8.3,
#       "population": 322
#     },
#     {
#       "ave_bedrm_num": 1.02,
#       "ave_occup": 2.56,
#       "ave_room_num": 7.1,
#       "house_age": 41,
#       "latitude": 37.88,
#       "longitude": -122.23,
#       "med_income": 8.3,
#       "population": 322
#     }
#     ]
#   }' | python -m json.tool

# echo
# echo "Testing '/bulk_predict' endpoint again, expecting the same hash_key per above..."
# curl -X 'POST' \
#   'https://caopuzheng.mids255.com/bulk_predict' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{
#   "houses": [
#     {
#       "ave_bedrm_num": 1.02,
#       "ave_occup": 2.56,
#       "ave_room_num": 7.1,
#       "house_age": 41,
#       "latitude": 37.88,
#       "longitude": -122.23,
#       "med_income": 8.3,
#       "population": 322
#     },
#     {
#       "ave_bedrm_num": 1.02,
#       "ave_occup": 2.56,
#       "ave_room_num": 7.1,
#       "house_age": 41,
#       "latitude": 37.88,
#       "longitude": -122.23,
#       "med_income": 8.3,
#       "population": 322
#     }
#     ]
#   }' | python -m json.tool

# output and tail the logs for the api deployment
echo
echo
kubectl logs -n ${NAMESPACE} -l app=${APP_NAME}

echo
echo "Prod deployment has been finished succesfully!"

# start the port-forwarding of the grafana service
echo
kubectl port-forward -n prometheus svc/grafana 3000:3000

# Below not needed per instructions of the lab4
# echo "Cleaning up..."
# kubectl delete --all deployments,services --namespace=caopuzheng
# kubectl delete configmap redis --namespace=caopuzheng

# In Prod, we can't delete the namespace as we don't have ability to recreate it
