APP_NAME=server
IMAGE_NAME=server_arm64
NAMESPACE=caopuzheng

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

# Run pytest within poetry virtualenv
echo
echo "running pytest..."
poetry run pytest -vv -s

# start mini-kube
minikube start --kubernetes-version=v1.27.3 --namespace ${NAMESPACE}
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

minikube tunnel &
TUNNEL_PID=$!
sleep 5
echo "minikube tunnel started in pid: ${TUNNEL_PID}..."
# we shouldn't use this b/c port-forward won't really use the load balancer (using multiple pods)
# kubectl port-forward -n=caopuzheng service/service-prediction 8000:8000

# test the docker container
echo
echo "testing '/hello' endpoint with name=Winegar, expecting 200, 422..."
curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/hello?name=Winegar"
curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/hello?na=Winegar"

echo "testing '/docs' endpoint, expecting 200..."
curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/docs"

# echo "testing '/predict' endpoint, expecting an valid prediction output..."
# curl -X POST 'http://localhost:8000/predict' \
#     -H 'accept: application/json' \
#     -H 'Content-Type: application/json' \
#     -d '{"ave_bedrm_num":1.02,"ave_occup":2.6,"ave_room_num":7,"house_age":41,"latitude":37.88,"longitude":-122.23,"med_income":8.3,"population":322}'

# echo
# echo "testing '/bulk_predict' endpoint, expecting an valid prediction output..."
# # Test bulk predict endpoint with valid input
# curl -X POST "http://localhost:8000/bulk_predict" \
#     -H "Content-Type: application/json" \
#     -d '{"houses": [{"ave_bedrm_num":1.02,"ave_occup":2.6,"ave_room_num":7,"house_age":41,"latitude":37.88,"longitude":-122.23,"med_income":8.3,"population":322},{"ave_bedrm_num":1.02,"ave_occup":2.6,"ave_room_num":7,"house_age":41,"latitude":37.88,"longitude":-122.23,"med_income":8.3,"population":322}]}'

# output and tail the logs for the api deployment
echo
echo
kubectl logs -n ${NAMESPACE} -l app=${APP_NAME}

echo
echo
echo "Cleaning up..."
# kubectl delete namespace ${NAMESPACE} # this will also delete everything in it
kubectl delete --all deployments,services --namespace ${NAMESPACE}
#kubectl delete configmap redis --namespace=caopuzheng

echo "stop the minikube tunnel..."
kill ${TUNNEL_PID}
docker image rm ${IMAGE_NAME}
minikube stop
echo "The script has finished running properly!"
