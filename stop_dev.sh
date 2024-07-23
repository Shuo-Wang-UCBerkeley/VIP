APP_NAME=server
IMAGE_NAME=server_arm64
NAMESPACE=caopuzheng

# change the directory to the current directory
echo "changing directory to current script directory..."
cd "$(dirname "$0")"
echo "current directory: $(pwd)"

# test the docker container
echo "testing '/docs' endpoint, expecting 200..."
curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/docs"

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
kubectl delete -k .k8s/overlays/dev
# kubectl delete --all deployments,services --namespace ${NAMESPACE}
# kubectl delete configmap redis --namespace=caopuzheng

echo "stop the minikube tunnel..."
# kill ${TUNNEL_PID}
docker image rm ${IMAGE_NAME}
minikube stop
echo "The script has finished running properly!"
