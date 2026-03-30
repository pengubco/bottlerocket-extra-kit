## Set auth token to pull ECR images.

```
mkdir -p /tmp/nerdctl-config

# 
TOKEN=$(aws ecr get-login-password --region us-west-2)
echo "{\"auths\":{\"xxxxxxxxxxxx.dkr.ecr.us-west-2.amazonaws.com\":{\"auth\":\"$(echo -n "AWS:${TOKEN}" | base64 -w0)\"}}}" \
  > /tmp/nerdctl-config/config.json

DOCKER_CONFIG=/tmp/nerdctl-config nerdctl pull $IMAGE
```